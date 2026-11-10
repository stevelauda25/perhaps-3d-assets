"""Write one self-contained collection gallery for a brand from the delivered GLBs in ~/Documents/<brand>/.

    python3 -B -m pipeline.watch_gallery_html orient      # -> ~/Documents/orient/orient-gallery.html

Every <brand>-*.glb in the delivery folder is a card, so any session can rerun this after copying its GLB there. Title,
subtitle and round come from jobs/<name>.json and its spec's "review" block; the thumbnail is the job's cmp-front.png.
A GLB without a job still shows (name from the file, no thumbnail). GLBs are embedded and decoded only when a card is
opened, so the page holds one 3D viewer (model-viewer 4.1.0, the tracker's version) at a time. Same look as watch_review_html.
"""
import base64
import datetime
import html
import json
import re
import sys
from pathlib import Path

import cv2
import numpy as np

from pipeline.watch_review_html import HEAD, ROOT

THUMB = 520  # px, square JPEG

STYLE = """<style>
  .tools { display: flex; flex-wrap: wrap; gap: 12px; align-items: center; justify-content: space-between; }
  input[type=search] { font: 15px var(--display); color: var(--fg); background: var(--plate); border: 1px solid var(--line); border-radius: 8px; padding: 9px 12px; width: min(100%, 320px); }
  input[type=search]:focus-visible { outline: 2px solid var(--accent); outline-offset: 2px; }
  .grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(220px, 1fr)); gap: 16px; }
  .card { all: unset; box-sizing: border-box; cursor: pointer; display: grid; background: var(--plate); border: 1px solid var(--line); border-radius: 10px; overflow: hidden; }
  .card:hover { border-color: var(--muted); }
  .card:focus-visible { outline: 2px solid var(--accent); outline-offset: 2px; }
  .card img, .card .ph { display: block; width: 100%; aspect-ratio: 1; object-fit: cover; background: #fff; }
  .card .ph { display: grid; place-items: center; color: #8a939c; font: 500 12px var(--mono); }
  .card .meta { padding: 10px 12px 12px; display: grid; gap: 4px; border-top: 1px solid var(--line); }
  .card b { font-size: 15px; font-weight: 600; }
  .card .info { font: 12px var(--mono); color: var(--muted); }
  dialog { width: min(1000px, calc(100vw - 32px)); max-height: calc(100vh - 32px); padding: 0; border: 1px solid var(--line); border-radius: 12px; background: var(--plate); color: var(--fg); }
  dialog::backdrop { background: rgb(0 0 0 / .6); }
  dialog model-viewer { height: min(70vh, 680px); }
  .dhead { display: flex; gap: 12px; align-items: baseline; justify-content: space-between; padding: 14px 16px; border-bottom: 1px solid var(--line); }
  .dhead p { margin: 4px 0 0; color: var(--muted); font-size: 13px; }
  a.pill { font: 500 13px var(--display); color: var(--fg); border: 1px solid var(--line); border-radius: 999px; padding: 7px 14px; text-decoration: none; }
  .empty { color: var(--muted); }
</style>
"""

BODY = """  <div class="tools">
    <input type="search" id="q" placeholder="Search name or SKU" aria-label="Search name or SKU">
    <span class="note" id="count"></span>
  </div>
  <div class="grid" id="grid">%(cards)s</div>
  <p class="empty" id="none" hidden>No watch matches.</p>
</div>
<dialog id="dlg" aria-labelledby="dtitle">
  <div class="dhead"><div><h2 id="dtitle"></h2><p id="dsub"></p></div><button type="button" class="pill" id="close">Close</button></div>
  <model-viewer id="mv" alt="" camera-controls camera-orbit="0deg 90deg auto" field-of-view="30deg"
    min-camera-orbit="auto auto 0.01m" interaction-prompt="none" shadow-intensity="0"></model-viewer>
  <div class="foot">
    <div class="views" role="group" aria-label="View">
      <button type="button" class="pill" data-o="0deg 90deg auto" data-t="auto auto auto" aria-pressed="true">Front</button>
      <button type="button" class="pill" data-o="90deg 90deg auto" data-t="auto auto auto" aria-pressed="false">Side</button>
      <button type="button" class="pill" data-o="35deg 65deg auto" data-t="auto auto auto" aria-pressed="false">Angled</button>
      <button type="button" class="pill" data-o="0deg 90deg 0.07m" data-t="0m 0.05m 0.003m" aria-pressed="false">Dial close-up</button>
    </div>
    <a class="pill" id="dl" download>Download GLB</a>
  </div>
</dialog>
<script>
  const glbs = %(glbs)s;
  const urls = {};
  const dlg = document.getElementById("dlg"), mv = document.getElementById("mv"), dl = document.getElementById("dl");
  const views = dlg.querySelectorAll(".views button");
  const setView = b => { views.forEach(x => x.setAttribute("aria-pressed", x === b)); mv.cameraTarget = b.dataset.t; mv.cameraOrbit = b.dataset.o; mv.jumpCameraToGoal?.(); };
  views.forEach(b => b.addEventListener("click", () => setView(b)));
  document.querySelectorAll(".card").forEach(c => c.addEventListener("click", () => {
    const id = c.dataset.id;
    urls[id] ??= URL.createObjectURL(new Blob([Uint8Array.from(atob(glbs[id]), ch => ch.charCodeAt(0))], {type: "model/gltf-binary"}));
    document.getElementById("dtitle").textContent = c.dataset.title;
    document.getElementById("dsub").textContent = c.dataset.sub;
    mv.alt = c.dataset.title + " watch, 3D";
    mv.src = urls[id];
    dl.href = urls[id]; dl.download = id + ".glb";
    setView(views[0]);
    dlg.showModal();
  }));
  document.getElementById("close").addEventListener("click", () => dlg.close());
  dlg.addEventListener("click", e => { if (e.target === dlg) dlg.close(); });
  const q = document.getElementById("q"), cards = [...document.querySelectorAll(".card")];
  const filter = () => {
    const t = q.value.trim().toLowerCase();
    let n = 0;
    cards.forEach(c => { const ok = !t || c.dataset.find.includes(t); c.hidden = !ok; n += ok; });
    document.getElementById("count").textContent = n + " of " + cards.length + " watches";
    document.getElementById("none").hidden = n > 0;
  };
  q.addEventListener("input", filter);
  filter();
</script>
</body></html>
"""


def card(glb):
    name = glb.stem
    job_file = ROOT / "jobs" / (name + ".json")
    title, sub, rnd, thumb = name, "", None, None
    if job_file.exists():
        job = json.loads(job_file.read_text())
        title = job.get("model", name)
        out = ROOT / job["output"]
        try:
            spec = json.loads((ROOT / job["stages"][0]["params"]["spec"]).read_text())
            sub = spec.get("review", {}).get("subtitle", "")
        except (KeyError, FileNotFoundError):
            pass
        rounds = [int(m.group(1)) for p in out.glob("board_round*.jpg") if (m := re.search(r"(\d+)$", p.stem))]
        rnd = max(rounds) if rounds else None
        im = cv2.imread(str(out / "cmp-front.png"))
        if im is not None:
            ys, xs = np.nonzero(im.min(2) < 245)  # the watch on the white kit; every render framed the same way
            cy, cx = (ys.min() + ys.max()) // 2, (xs.min() + xs.max()) // 2
            s = int(max(ys.max() - ys.min(), xs.max() - xs.min()) * 1.06) // 2
            im = cv2.copyMakeBorder(im, s, s, s, s, cv2.BORDER_CONSTANT, value=(255, 255, 255))[cy:cy + 2 * s, cx:cx + 2 * s]
            im = cv2.resize(im, (THUMB, THUMB), interpolation=cv2.INTER_AREA)
            thumb = base64.b64encode(cv2.imencode(".jpg", im, [cv2.IMWRITE_JPEG_QUALITY, 82])[1].tobytes()).decode()
    sku = name.split("-", 1)[1].upper() if "-" in name else name.upper()
    info = "%s · %s%.1f MB" % (sku, "round %d · " % rnd if rnd else "", glb.stat().st_size / 1e6)
    esc = html.escape
    pic = ('<img alt="" loading="lazy" src="data:image/jpeg;base64,%s">' % thumb) if thumb else '<span class="ph">no render</span>'
    return ('<button type="button" class="card" data-id="%s" data-title="%s" data-sub="%s" data-find="%s">%s'
            '<span class="meta"><b>%s</b><span class="info">%s</span></span></button>'
            % (esc(name), esc(title), esc(sub), esc((title + " " + name + " " + sku).lower()), pic, esc(title), esc(info)))


def build(brand):
    folder = Path.home() / "Documents" / brand
    glbs = sorted(folder.glob(brand + "-*.glb"))
    assert glbs, "no %s-*.glb in %s" % (brand, folder)
    page = HEAD % {"title": html.escape(brand.capitalize() + " collection"), "date": datetime.date.today().strftime("%-d %B %Y"),
                   "sub": "%d front relief GLBs. Open a watch to turn it in 3D." % len(glbs)}
    page = page.replace("</head>", STYLE + "</head>")
    page += BODY % {"cards": "".join(card(g) for g in glbs),
                    "glbs": json.dumps({g.stem: base64.b64encode(g.read_bytes()).decode() for g in glbs})}
    dest = folder / (brand + "-gallery.html")
    dest.write_text(page)
    return dest, len(glbs)


if __name__ == "__main__":
    dest, n = build(sys.argv[1])
    print(dest, n, "watches", round(dest.stat().st_size / 1e6, 2), "MB")
