"""Stroke weight of the upper storey against the lower, on the face's own stacked letters."""
import numpy as np
from fontTools.ttLib import TTFont
from fontTools.pens.recordingPen import DecomposingRecordingPen
from PIL import Image, ImageDraw
from scipy import ndimage
from vform import _Flat
def mask(path, ch, k=0.5):
    f = TTFont(path); gs = f.getGlyphSet(); g = gs[f.getBestCmap()[ord(ch)]]
    pen = _Flat(gs); g.draw(pen)
    polys = pen.polys if hasattr(pen, "polys") else pen.out
    xs = [p[0] for c in polys for p in c]; ys = [p[1] for c in polys for p in c]
    x0, y0, y1 = min(xs) - 20, min(ys) - 20, max(ys) + 20
    W = int((max(xs) + 20 - x0) * k); H = int((y1 - y0) * k)
    img = Image.new("1", (W, H), 0); d = ImageDraw.Draw(img)
    for c in polys:
        d.polygon([((p[0] - x0) * k, (y1 - p[1]) * k) for p in c], fill=1, outline=1)
    # evenodd
    m = np.zeros((H, W), bool)
    for c in polys:
        im = Image.new("1", (W, H), 0); ImageDraw.Draw(im).polygon([((p[0] - x0) * k, (y1 - p[1]) * k) for p in c], fill=1)
        m ^= np.asarray(im)
    return m, k
for style in ("ThinItalic", "ExtraBoldItalic"):
    for ch in "8BВ3":
        m, k = mask("fonts/ttf/SUSEMono-%s.ttf" % style, ch)
        d = ndimage.distance_transform_edt(m)
        ridge = (d >= ndimage.maximum_filter(d, size=3)) & (d > 2)
        ys, xs = np.nonzero(ridge); H = m.shape[0]
        w = 2 * d[ridge] / k
        top = w[ys < H * 0.38]; bot = w[ys > H * 0.62]
        print("%-16s %s  upper %.0f  lower %.0f  ratio %.2f" % (style, ch, np.median(top), np.median(bot), np.median(top) / np.median(bot)))
