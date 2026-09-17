"""The cursive д, drawn here along a path taken from Lilex.

Frozen: this data is the source. Its generator, de_from_lilex.py, was
retired 2026-09-17 so the font needs no other face installed;
it is in git history under scripts/.
Lilex is under the SIL Open Font License 1.1, which is what
lets it be an outline donor here. Held as data rather than read
from the donor at build time so the repository builds without a
font that lives outside it.

ONE contour plus o's own counter: the bowl is this face's o and
the arm is a stroke of this face's own weight grown out of its
right-hand wall, spliced so the wall carries on into it without
a seam. Nothing of the donor's own outline survives -- only the
line its arm travels along.

The notch between bowl and arm has a cusp at Thin, and closes at
ExtraBold. The node that draws its tip is still needed there for
node parity, so ExtraBold's next on-curve sits a little further
along its own curve and leaves that node a segment with length.

UN-SHEARED, like every outline a recipe sees. One entry per
master, in source order: contours of (x, y, type, smooth).
"""

DE = [
    # the donor's own Thin to Bold at +0.000
    [
        [
            (408.0, 452.3, 'offcurve', False),
            (347.8, 482.0, 'offcurve', False),
            (279.7, 482.0, 'curve', True),
            (134.7, 482.0, 'offcurve', False),
            (57.3, 351.0, 'offcurve', False),
            (100.5, 178.0, 'curve', True),
            (128.6, 65.0, 'offcurve', False),
            (218.3, -10.0, 'offcurve', False),
            (326.3, -10.0, 'curve', True),
            (438.3, -10.0, 'offcurve', False),
            (508.3, 72.1, 'offcurve', False),
            (512.1, 193.2, 'curve', True),
            (517.8, 370.6, 'offcurve', False),
            (410.4, 566.1, 'offcurve', False),
            (258.3, 630.7, 'curve', True),
            (220.0, 646.9, 'offcurve', False),
            (196.9, 653.9, 'offcurve', False),
            (156.7, 664.1, 'curve', False),
            (150.9, 640.8, 'line', False),
            (190.0, 630.9, 'offcurve', False),
            (211.8, 624.1, 'offcurve', False),
            (248.8, 608.4, 'curve', True),
            (327.1, 575.1, 'offcurve', False),
            (403.1, 495.6, 'offcurve', False),
            (449.4, 402.3, 'curve', False),
        ],
    ],
    # the donor's own Thin to Bold at +0.000
    [
        [
            (264.5, 503.0, 'offcurve', False),
            (259.1, 502.8, 'offcurve', False),
            (253.8, 502.5, 'curve', True),
            (107.1, 493.8, 'offcurve', False),
            (28.2, 366.1, 'offcurve', False),
            (68.8, 203.0, 'curve', True),
            (107.7, 47.0, 'offcurve', False),
            (230.0, -10.0, 'offcurve', False),
            (330.0, -10.0, 'curve', True),
            (456.5, -10.0, 'offcurve', False),
            (539.5, 80.4, 'offcurve', False),
            (542.7, 202.5, 'curve', True),
            (548.4, 419.1, 'offcurve', False),
            (326.9, 657.9, 'offcurve', False),
            (182.2, 706.0, 'curve', True),
            (160.5, 713.2, 'offcurve', False),
            (146.6, 716.3, 'offcurve', False),
            (124.6, 721.8, 'curve', False),
            (94.8, 602.2, 'line', False),
            (113.8, 597.4, 'offcurve', False),
            (124.6, 594.5, 'offcurve', False),
            (143.1, 588.3, 'curve', True),
            (177.0, 577.0, 'offcurve', False),
            (224.1, 545.1, 'offcurve', False),
            (270.9, 503.0, 'curve', False),
        ],
    ],
]
