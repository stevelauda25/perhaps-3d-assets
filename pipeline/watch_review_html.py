"""Write one self-contained review page (model-viewer 4.1.0, the tracker's version) for one or more watch jobs.

    python3 -B -m pipeline.watch_review_html <out.html> <job id> [<job id> ...]
    e.g. python3 -B -m pipeline.watch_review_html ~/Documents/orient/orient-re-at0007n00b-review.html orient-re-at0007n00b

Per job: the GLB from the export stage and the newest outputs/jobs/<id>/board_round<N>.jpg are embedded (base64), so the page
opens from disk and can be sent as one file. Title from the job's "model"; subtitle, measurement tiles and notes from the
spec's "review" block: {"subtitle": str, "specs": [[value, label], ...], "notes": [str, ...]}. Same layout as the Armani page.
"""
import base64
import datetime
import html
import json
import re
import sys
from pathlib import Path

import cv2

ROOT = Path(__file__).resolve().parents[1]
BOARD_W = 1600  # board image width in the page (JPEG)

HEAD = """<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>%(title)s review</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Familjen+Grotesk:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap">
<script type="module" src="https://cdn.jsdelivr.net/npm/@google/model-viewer@4.1.0/dist/model-viewer.min.js"></script>
<style>
  :root {
    --bg: #eef0f2; --plate: #f8f9fa; --stage: #e2e5e9; --fg: #16191d; --muted: #5d6670; --line: #d3d8de; --accent: #1f5f8b;
    --display: "Familjen Grotesk", "Helvetica Neue", Arial, sans-serif;
    --mono: "JetBrains Mono", ui-monospace, Menlo, monospace;
  }
  @media (prefers-color-scheme: dark) {
    :root:not([data-theme="light"]) { --bg: #111417; --plate: #181c20; --stage: #20252b; --fg: #e9edf1; --muted: #9aa4ae; --line: #2b3239; --accent: #8cc2ea; color-scheme: dark; }
  }
  :root[data-theme="dark"] { --bg: #111417; --plate: #181c20; --stage: #20252b; --fg: #e9edf1; --muted: #9aa4ae; --line: #2b3239; --accent: #8cc2ea; color-scheme: dark; }
  body { margin: 0; font-size: 14px; background: var(--bg); color: var(--fg); font-family: var(--display); }
  .wrap { max-width: 1100px; margin: 0 auto; padding: 40px max(16px, env(safe-area-inset-left, 0px)) 56px; display: grid; gap: 24px; }
  .eyebrow { font: 500 12px/1 var(--mono); letter-spacing: .08em; text-transform: uppercase; color: var(--muted); }
  h1 { margin: 8px 0 0; font-size: clamp(28px, 5vw, 44px); font-weight: 700; letter-spacing: -.02em; line-height: 1.05; }
  h2 { margin: 0; font-size: 18px; font-weight: 600; }
  .sub { margin: 8px 0 0; color: var(--muted); font-size: 15px; }
  .panel { background: var(--plate); border: 1px solid var(--line); border-radius: 10px; overflow: hidden; }
  model-viewer { display: block; width: 100%%; height: min(78vh, 760px); background: var(--stage); }
  .foot { display: flex; flex-wrap: wrap; gap: 8px; padding: 12px 16px; border-top: 1px solid var(--line); align-items: center; justify-content: space-between; }
  .views { display: flex; flex-wrap: wrap; gap: 8px; }
  button.pill { font: 500 13px var(--display); color: var(--fg); background: transparent; border: 1px solid var(--line); border-radius: 999px; padding: 7px 14px; cursor: pointer; }
  button.pill[aria-pressed="true"] { background: var(--fg); color: var(--bg); border-color: var(--fg); }
  button:focus-visible { outline: 2px solid var(--accent); outline-offset: 2px; }
  .note { font-size: 13px; color: var(--muted); }
  .head { padding: 14px 16px; border-bottom: 1px solid var(--line); display: flex; flex-wrap: wrap; gap: 8px 16px; align-items: baseline; justify-content: space-between; }
  .board { display: block; width: 100%%; height: auto; }
  .specs { display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 1px; background: var(--line); }
  .specs div { background: var(--plate); padding: 12px 16px; display: grid; gap: 4px; }
  .specs b { font: 500 16px var(--mono); font-variant-numeric: tabular-nums; }
  .specs span { font-size: 12px; color: var(--muted); }
  .model { padding-top: 16px; border-top: 1px solid var(--line); display: grid; gap: 24px; }
  .model h2 { font-size: clamp(22px, 3.5vw, 30px); font-weight: 700; letter-spacing: -.01em; }
  ul { margin: 0; padding: 14px 16px 16px 34px; display: grid; gap: 6px; line-height: 1.45; }
</style>
</head><body>
<div class="wrap">
  <header>
    <div class="eyebrow">Perhaps watch tracker &middot; %(date)s</div>
    <h1>%(title)s</h1>
    <p class="sub">%(sub)s</p>
  </header>
"""

MODEL = """  <section class="model" aria-label="%(model)s">
    <div><div class="eyebrow">Round %(round)s</div><h2>%(model)s</h2><p class="sub">%(sub)s</p></div>
    <section class="panel" aria-label="3D model">
      <model-viewer id="%(mv)s" alt="%(model)s watch, 3D" camera-controls camera-orbit="0deg 90deg auto" field-of-view="30deg"
        min-camera-orbit="auto auto 0.01m" interaction-prompt="none" shadow-intensity="0"></model-viewer>
      <div class="foot">
        <div class="views" role="group" aria-label="View">
          <button type="button" class="pill" data-o="0deg 90deg auto" data-t="auto auto auto" aria-pressed="true">Front</button>
          <button type="button" class="pill" data-o="90deg 90deg auto" data-t="auto auto auto" aria-pressed="false">Side</button>
          <button type="button" class="pill" data-o="35deg 65deg auto" data-t="auto auto auto" aria-pressed="false">Angled</button>
          <button type="button" class="pill" data-o="0deg 90deg 0.07m" data-t="0m 0.05m 0.003m" aria-pressed="false">Dial close-up</button>
        </div>
        <span class="note">Drag to turn, scroll or pinch to zoom.</span>
      </div>
    </section>
    <section class="panel" aria-label="Measurements"><div class="specs">%(specs)s</div></section>
    <section class="panel" aria-label="Photo and render">
      <div class="head"><h2>Product photo and render</h2><span class="note">Left: product photo. Right: render of the model, same scale and framing.</span></div>
      <img class="board" alt="Product photo on the left, render of the model on the right" src="data:image/jpeg;base64,%(board)s">
    </section>
    <section class="panel" aria-label="Notes"><div class="head"><h2>Round %(round)s notes</h2></div><ul>%(notes)s</ul></section>
  </section>
"""

TAIL = """</div>
<script>
  const glbs = %(glbs)s;
  for (const [id, b64] of Object.entries(glbs)) {
    const bytes = Uint8Array.from(atob(b64), c => c.charCodeAt(0));
    document.getElementById(id).src = URL.createObjectURL(new Blob([bytes], {type: "model/gltf-binary"}));
  }
  document.querySelectorAll(".panel .views").forEach(row => {
    const mv = row.closest(".panel").querySelector("model-viewer");
    const views = row.querySelectorAll("button");
    views.forEach(b => b.addEventListener("click", () => {
      views.forEach(x => x.setAttribute("aria-pressed", x === b));
      mv.cameraTarget = b.dataset.t;
      mv.cameraOrbit = b.dataset.o;
      mv.jumpCameraToGoal?.();
    }));
  });
</script>
</body></html>
"""


def model_block(job_id):
    job = json.loads((ROOT / "jobs" / (job_id + ".json")).read_text())
    spec = json.loads((ROOT / job["stages"][0]["params"]["spec"]).read_text())
    rv = spec["review"]
    out = ROOT / job["output"]
    glb = ROOT / next(s["params"]["glb"] for s in job["stages"] if "glb" in s.get("params", {}))
    boards = sorted(out.glob("board_round*.jpg"), key=lambda p: int(re.search(r"(\d+)", p.stem).group(1)))
    assert boards, "no board_round<N>.jpg in %s" % out
    im = cv2.imread(str(boards[-1]))
    im = cv2.resize(im, (BOARD_W, round(im.shape[0] * BOARD_W / im.shape[1])), interpolation=cv2.INTER_AREA)
    board = base64.b64encode(cv2.imencode(".jpg", im, [cv2.IMWRITE_JPEG_QUALITY, 85])[1].tobytes()).decode()
    mb = glb.stat().st_size / 1e6
    specs = rv["specs"] + [["%.2f MB" % mb, "GLB file"]]
    esc = html.escape
    mv = "mv-" + job_id
    block = MODEL % {"model": esc(job["model"]), "round": re.search(r"(\d+)", boards[-1].stem).group(1), "sub": esc(rv["subtitle"]), "mv": mv,
                     "specs": "".join("<div><b>%s</b><span>%s</span></div>" % (esc(v), esc(k)) for v, k in specs),
                     "board": board, "notes": "".join("<li>%s</li>" % esc(n) for n in rv["notes"])}
    return job["model"], block, mv, base64.b64encode(glb.read_bytes()).decode()


def build(dest, job_ids):
    parts = [model_block(j) for j in job_ids]
    title = parts[0][0] if len(parts) == 1 else " / ".join(p[0] for p in parts)
    sub = "Front relief GLB." if len(parts) == 1 else "%d front relief GLBs." % len(parts)
    page = HEAD % {"title": html.escape(title), "date": datetime.date.today().strftime("%-d %B %Y"), "sub": sub}
    page += "".join(p[1] for p in parts) + TAIL % {"glbs": json.dumps({p[2]: p[3] for p in parts})}
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(page)
    return dest.stat().st_size


if __name__ == "__main__":
    dest = Path(sys.argv[1]).expanduser()
    print(dest, round(build(dest, sys.argv[2:]) / 1e6, 2), "MB")
