"""Where б's widest disc actually sits -- drawn, not reported as a number.

    ./venv/bin/python tools/blob.py            # ours, four weights
    ./venv/bin/python tools/blob.py --panel    # and six faces beside them

`seam.py` says how big the junction's mass is and gives its position as two
fractions of the counter's box. Two fractions are not a picture, and this
letter has now produced four right numbers in the wrong place. The disc is the
thing being measured, so the disc is what gets drawn: the largest circle that
fits in the ink, on the glyph it was measured in, at the same scale for every
face on the sheet.

One render per column and one distance transform per render -- the masks come
from `seam.py`'s blend, so no build is needed and the whole sheet is seconds.
"""

import sys

sys.path.insert(0, __file__.rsplit("/", 1)[0])

import numpy as np
from PIL import Image, ImageDraw, ImageFont

import weights as W
import seam as S

# Six faces that draw б and span the panel's constructions -- the same set the
# junction crop already used, so the two sheets can be read against each other.
REFS = ("DejaVuSansMono", "Inconsolata", "LiberationMono", "RobotoMono",
        "UbuntuMono", "Sudo")

# Side of a zoomed pane, in pixels. Every pane covers the same neighbourhood
# in wall-widths, so this is what makes them the same size on the sheet.
ZOOM_PX = 420


def disc(mask):
    """(radius, x, y) of the largest disc that fits in the ink."""
    d = W.edt(mask)
    y, x = np.unravel_index(int(np.argmax(d)), d.shape)
    return float(d[y, x]), int(x), int(y)


def touch(mask, x, y, r, keep=2):
    """The nearest non-ink points to the disc's centre, one per direction.

    Everything within half a pixel of the radius touches, which on a raster
    is an arc rather than a point, so the arcs are thinned to one point each
    by dropping any candidate that is already within a radius of a kept one.
    """
    e = int(r) + 3
    h, w = mask.shape
    ys, xs = np.mgrid[max(0, y - e):min(h, y + e),
                      max(0, x - e):min(w, x + e)]
    d = np.hypot(xs - x, ys - y)
    hit = (~mask[max(0, y - e):min(h, y + e), max(0, x - e):min(w, x + e)]) \
        & (d <= r + 1.5)
    cand = sorted(zip(d[hit], xs[hit], ys[hit]))
    out = []
    for _dist, cx, cy in cand:
        if all(np.hypot(cx - px, cy - py) > r for px, py in out):
            out.append((int(cx), int(cy)))
        if len(out) == keep:
            break
    return out


def draw(mask, wall, label, pad=16, zoom=0.0):
    """One column: the glyph in grey, its widest disc ringed in red.

    `zoom` crops to that many wall-widths either side of the disc, which is
    the only way six faces can be compared at the junction -- a whole letter
    puts the thing in question into a tenth of the column.
    """
    r, x, y = disc(mask)
    ratio = (2.0 * r - W.BIAS) / wall if wall else 0.0
    if zoom:
        h, w = mask.shape
        e = int(zoom * wall)
        pane = np.zeros((2 * e, 2 * e), bool)
        y0, x0 = y - e, x - e
        ys, xs = slice(max(0, y0), min(h, y + e)), slice(max(0, x0), min(w, x + e))
        pane[ys.start - y0:ys.stop - y0, xs.start - x0:xs.stop - x0] = \
            mask[ys, xs]
        # The window is a fixed number of wall-widths, so it is the same
        # neighbourhood everywhere and a different number of pixels every
        # time. Resampled to one size it is finally comparable by eye.
        k = ZOOM_PX / float(2 * e)
        mask = np.asarray(Image.fromarray(pane).resize(
            (ZOOM_PX, ZOOM_PX), Image.NEAREST))
        r, x, y = r * k, ZOOM_PX // 2, ZOOM_PX // 2
    h, w = mask.shape
    im = Image.new("RGB", (w + 2 * pad, h + 2 * pad + 34), "white")
    ink = Image.fromarray(np.where(mask, 40, 255).astype("uint8")).convert("RGB")
    im.paste(ink, (pad, pad + 34))
    g = ImageDraw.Draw(im)
    cx, cy = pad + x, pad + 34 + y
    # The two edges the disc actually touches, in blue. Which boundaries set
    # the width is the whole question -- a disc at the junction can be big
    # because the strokes merge at a shallow angle, or because there is a
    # fillet, and the ring alone does not tell those two apart.
    for tx, ty in touch(mask, x, y, r):
        g.ellipse([pad + tx - 7, pad + 34 + ty - 7,
                   pad + tx + 7, pad + 34 + ty + 7], fill=(30, 90, 220))
    g.ellipse([cx - r, cy - r, cx + r, cy + r], outline=(220, 30, 30), width=3)
    g.line([cx - 5, cy, cx + 5, cy], fill=(220, 30, 30), width=2)
    g.line([cx, cy - 5, cx, cy + 5], fill=(220, 30, 30), width=2)
    txt = "%s  %.2f" % (label, ratio) if wall else label
    g.text((pad, 8), txt, font=_lab(), fill=(60, 60, 60))
    return im


_LAB = []


def _lab():
    if not _LAB:
        import glob
        from panel import font_dirs
        for d in font_dirs():
            for n in ("DejaVuSans.ttf", "segoeui.ttf",
                      "LiberationSans-Regular.ttf"):
                hit = glob.glob(d + "/" + n)
                if hit:
                    _LAB.append(ImageFont.truetype(hit[0], 22))
                    return _LAB[0]
        _LAB.append(ImageFont.load_default())
    return _LAB[0]


def ours(ch="б"):
    """Our four weights as (label, mask, wall), blended from the two masters.

    Scaled on the face's own o, exactly as `W.render` scales the panel, so a
    stroke on this sheet is the same number of pixels whoever drew it. Scaled
    on the cap instead -- which is what `seam.py` needs and does -- ours come
    out most of a third smaller than the panel's, and the ratios stay right
    while the picture lies about which junction is fatter.
    """
    (a_be, a_o, _a_c), (b_be, b_o, _b_c) = S.masters(ch)
    out = []
    for name, t in S.WEIGHTS:
        o = S.blend(a_o, b_o, t)
        ys = [q[1] for p in o for q in p]
        k = W.XH / (max(ys) - min(ys))
        out.append((name, W.mask_of(S.blend(a_be, b_be, t), k),
                    W.width(W.edt(W.mask_of(o, k)))))
    return out


def refs(ch="б"):
    from panel import families
    want = {n.lower(): None for n in REFS}
    for fam, path in families():
        key = fam.replace(" ", "").lower()
        if key in want and want[key] is None:
            want[key] = path
    out = []
    for n in REFS:
        p = want.get(n.lower())
        if not p:
            continue
        m = W.render(p, ch, W.XH)
        w = W.wall(p, W.XH)
        if m is not None and w:
            out.append((n, m, w))
    return out


def sheet(cols, path, zoom=0.0):
    ims = [draw(m, w, n, zoom=zoom) for n, m, w in cols]
    H = max(i.height for i in ims)
    out = Image.new("RGB", (sum(i.width for i in ims), H), "white")
    x = 0
    for i in ims:
        out.paste(i, (x, 0))
        x += i.width
    out.save(path)
    print("wrote %s" % path)


def main():
    ch = next((a for a in sys.argv[1:] if not a.startswith("-")), "б")
    cols = ours(ch)
    if "--panel" in sys.argv:
        cols = cols + refs(ch)
    zoom = 4.0 if "--zoom" in sys.argv else 0.0
    sheet(cols, "tools/out/be_blob%s.png" % ("_zoom" if zoom else ""), zoom)


if __name__ == "__main__":
    main()
