"""Subdivision-friendly hard-surface slabs (pure Python; the Blender side only does from_pydata + a SUBSURF modifier).

rounded_slab(outline, z_bottom, z_top, r_bottom, r_top) builds a slab whose outline is any 2D polygon: support rings at distance r from every
edge make Catmull-Clark produce fillets of about that radius. Faces carry a material index: 0 = caps and walls (brushed), 1 = the fillet bands
(polished) so one mesh shows the brushed-face / polished-chamfer contrast of real watch cases and bracelets.
"""
import math


def ccw(poly):
    area = sum(a[0] * b[1] - b[0] * a[1] for a, b in zip(poly, poly[1:] + poly[:1]))
    return poly if area > 0 else poly[::-1]


def inset(poly, d):
    """Move every vertex of a CCW polygon inward by d (mitre); negative d grows it. d may be a list (one distance per vertex)."""
    n, out = len(poly), []
    dists = d if isinstance(d, (list, tuple)) else [d] * n
    for i in range(n):
        d = dists[i]
        p0, p1, p2 = poly[i - 1], poly[i], poly[(i + 1) % n]

        def nrm(a, b):
            dx, dy = b[0] - a[0], b[1] - a[1]
            length = math.hypot(dx, dy) or 1.0
            return (-dy / length, dx / length)
        n1, n2 = nrm(p0, p1), nrm(p1, p2)
        s = d / max(1 + n1[0] * n2[0] + n1[1] * n2[1], 0.45)  # clamp: very sharp corners would shoot outward
        out.append((p1[0] + (n1[0] + n2[0]) * s, p1[1] + (n1[1] + n2[1]) * s))
    return out


def rounded_slab(outline, z_bottom, z_top, r_bottom, r_top, cap_rings=1, cap_step=0.35):
    """-> (verts, faces, material_index). z_* are functions (x, y) -> z evaluated at each ring vertex.
    cap_rings extra insets (cap_step * the smaller half-width) keep the top cap from becoming one high-valence pole."""
    poly = ccw(list(outline))
    n = len(poly)
    xs = [p[0] for p in poly]
    ys = [p[1] for p in poly]
    half = min(max(xs) - min(xs), max(ys) - min(ys)) / 2
    rings = [(inset(poly, r_bottom), "b", 0), (poly, "b", r_bottom), (poly, "t", -r_top), (inset(poly, r_top), "t", 0)]
    for k in range(1, cap_rings + 1):
        rings.append((inset(poly, r_top + k * cap_step * half), "t", 0))
    verts, faces, mats = [], [], []
    for ring, side, dz in rings:
        for x, y in ring:
            verts.append((x, y, (z_bottom(x, y) if side == "b" else z_top(x, y)) + dz))
    faces.append(tuple(range(n - 1, -1, -1)))
    mats.append(0)
    for i in range(len(rings) - 1):
        for k in range(n):
            j = (k + 1) % n
            faces.append((i * n + k, i * n + j, (i + 1) * n + j, (i + 1) * n + k))
            mats.append(1 if i in (0, 2) else 0)
    faces.append(tuple(range((len(rings) - 1) * n, len(rings) * n)))
    mats.append(0)
    return verts, faces, mats


def scallop_outline(w, length, sag, n=6):
    """Link plan outline centred at the origin: convex scalloped end at +y, matching concave end at -y (links nest at pitch = length + gap)."""
    def edge(x, y0):
        return y0 + sag * (1 - (2 * x / w) ** 2)
    bottom = [(-w / 2 + w * i / n, edge(-w / 2 + w * i / n, -length / 2)) for i in range(n + 1)]
    top = [(-w / 2 + w * i / n, edge(-w / 2 + w * i / n, length / 2)) for i in range(n, -1, -1)]
    return bottom + top


def merge(parts):
    """Concatenate (verts, faces, mats) tuples into one."""
    verts, faces, mats = [], [], []
    for v, f, m in parts:
        base = len(verts)
        verts += v
        faces += [tuple(i + base for i in face) for face in f]
        mats += m
    return verts, faces, mats


def faceted_slab(outline, z_bottom, z_top, chamfer, drop):
    """Crisp planar solid (no SubD): vertical flank (mat 0, brushed), a narrow polished chamfer band along the outline (mat 1) and a flat top face
    (mat 0). chamfer(x, y) -> width of the band at an outline vertex (mm), drop = height lost across the band. Matches the real lugs: sloping brushed
    top, polished outer chamfer, razor edges."""
    poly = ccw(list(outline))
    n = len(poly)
    inner = inset(poly, [chamfer(x, y) for x, y in poly])
    verts = [(x, y, z_bottom(x, y)) for x, y in poly] + [(x, y, z_top(x, y) - drop) for x, y in poly] + [(x, y, z_top(x, y)) for x, y in inner]
    faces, mats = [tuple(range(n - 1, -1, -1))], [0]
    for i, m in ((0, 0), (1, 1)):
        for k in range(n):
            j = (k + 1) % n
            faces.append((i * n + k, i * n + j, (i + 1) * n + j, (i + 1) * n + k))
            mats.append(m)
    faces.append(tuple(range(2 * n, 3 * n)))
    mats.append(0)
    return verts, faces, mats
