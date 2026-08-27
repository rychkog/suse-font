#!/usr/bin/env bash
# Regenerate EVERY review image from the CURRENT build, so nothing shown is
# stale. Reviewing an image rendered before the last fix wastes a round.
#
# It said EVERY and regenerated four, which is the same lie as a stale picture
# and worse for being automated. It then said EVERY and regenerated eleven --
# of which six were the same four rows over and over, one per letter, because
# a PNG could not hold them all at once.
#
# It can now. `specimen.py` is those six merged: the alphabet, the case pairs,
# the prose, the code, the mixed lines and the reading sizes, in one SVG that
# the reader zooms into rather than six files they have to find. Ask it for one
# letter with `--letters Зз` when one letter is the question.
#
# Everything below the specimen draws a MEASUREMENT rather than a letter, which
# is why none of it merged: the question each answers is the thing that would
# be lost.
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")/.."

./venv/bin/python tools/specimen.py
./venv/bin/python tools/signature_sheet.py >/dev/null
./venv/bin/python tools/outlines.py >/dev/null

# gd_donors, de_arm and de_vs_d stood here until 2026-08-27, drawing the
# evidence behind the cursive г and д. Both letters are approved and their
# questions are settled, so the three were retired with nine other
# settled-letter probes -- METHOD section 4 lists what each established. A probe
# that redraws a decided answer every build is a stale picture with a cron job.

echo "regenerated: specimen.svg signature outlines"
