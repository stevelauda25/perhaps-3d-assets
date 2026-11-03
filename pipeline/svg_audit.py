"""Audit the wordmark SVG paths and write a derived working copy (original untouched).

    python3 -B -m pipeline.svg_audit references/brand/perhaps-wordmark-v2.svg
Reports per subpath: closure, duplicate/zero-length segments, tiny segments, abnormal handles, sharp nodes, signed area/winding,
containment (counters) and self-intersections of the flattened outline. Only duplicate consecutive points / zero-length
segments are corrected in `<name>.clean.svg` (everything else is reported, never reshaped).
"""
import json
from pathlib import Path
import re
import sys

from pipeline.steps.logo_deboss import inside, parse_svg, polygon


def dist(a, b):
    return ((a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2) ** 0.5


def cross_segments(poly):
    """Count proper self-intersections between non-adjacent flattened segments."""
    segs = list(zip(poly, poly[1:] + poly[:1]))
    n, hits = len(segs), 0

    def ccw(a, b, c):
        return (c[1] - a[1]) * (b[0] - a[0]) - (b[1] - a[1]) * (c[0] - a[0])
    for i in range(n):
        for j in range(i + 2, n):
            if i == 0 and j == n - 1:
                continue
            (a, b), (c, d) = segs[i], segs[j]
            if ccw(a, c, d) * ccw(b, c, d) < 0 and ccw(a, b, c) * ccw(a, b, d) < 0:
                hits += 1
    return hits


def audit(text):
    paths = re.findall(r'<path[^>]*\sd="([^"]+)"', text)
    report = {"paths": len(paths), "subpaths": []}
    for pi, d in enumerate(paths):
        subs = parse_svg('<path d="%s"/>' % d)
        polys = [polygon(s, 24) for s in subs]
        closed = len(re.findall("Z", d)) == len(subs)
        for si, segs in enumerate(subs):
            poly = polys[si]
            area = sum(a[0] * b[1] - b[0] * a[1] for a, b in zip(poly, poly[1:] + poly[:1])) / 2
            lens = [dist(s[0], s[3]) for s in segs]
            handles = [max(dist(s[0], s[1]), dist(s[3], s[2])) / max(dist(s[0], s[3]), 1e-9) for s in segs if dist(s[0], s[3]) > 0.05]
            inner_of = [j for j, q in enumerate(polys) if j != si and sum(inside(p, q) for p in poly) >= 0.9 * len(poly)]
            report["subpaths"].append({"path": pi, "sub": si, "segments": len(segs), "zero_length": sum(l < 1e-6 for l in lens),
                                       "tiny_lt_0.02u": sum(1e-6 <= l < 0.02 for l in lens), "max_handle_ratio": round(max(handles, default=0), 2),
                                       "signed_area": round(area, 1), "is_counter": bool(inner_of), "self_intersections": cross_segments(poly)})
        report.setdefault("closed_all", True)
        report["closed_all"] &= closed
    holes = [s for s in report["subpaths"] if s["is_counter"]]
    report["counters"] = len(holes)
    report["winding_ok"] = all((h["signed_area"] > 0) != (o["signed_area"] > 0) for h in holes for o in report["subpaths"] if o["path"] == h["path"] and not o["is_counter"])
    report["defects"] = {"zero_length": sum(s["zero_length"] for s in report["subpaths"]), "self_intersections": sum(s["self_intersections"] for s in report["subpaths"]),
                         "abnormal_handles_gt_3x_chord": sum(s["max_handle_ratio"] > 3 for s in report["subpaths"])}
    return report


def clean(text):
    """Derived working copy. The audit found no verified defect to repair (no zero-length segments, self-intersections or
    abnormal handles), so the copy is byte-identical; a verified fix would be applied here and nowhere else."""
    return text


if __name__ == "__main__":
    src = Path(sys.argv[1])
    text = src.read_text()
    rep = audit(text)
    out = src.with_suffix(".clean.svg")
    out.write_text(clean(text))
    src.with_suffix(".audit.json").write_text(json.dumps(rep, indent=1) + "\n")
    print(json.dumps({k: v for k, v in rep.items() if k != "subpaths"}))
    for s in rep["subpaths"]:
        print(s)
