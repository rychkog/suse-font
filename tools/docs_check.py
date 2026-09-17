"""The docs against the code, so the two cannot drift apart unseen.

    ./venv/bin/python tools/docs_check.py

Fails when:

- a fault ID (`### F12 · ...` in METHOD) is used twice, or is out of order;
- a doc or a code comment cites an F or a § that METHOD does not have;
- AGENTS.md, CLAUDE.md or METHOD.md cites a script, constant or function the
  code no longer has, unless METHOD's *Retired* section lists it;
- a script in `tools/` has no row in METHOD's §4 inventory;
- a doc cites a line number (`recipes.py:1304`) -- they go stale on the next
  edit, so cite the symbol.

APPROVALS.md is checked for F and § only. It is a dated ledger: a name in a
row was true on that row's date, and rewriting it would falsify the record.
"""

import glob
import re
import sys

sys.path.insert(0, __file__.rsplit("/", 1)[0])

METHOD = "docs/METHOD.md"
NAMED = ("AGENTS.md", "CLAUDE.md", METHOD)
LEDGER = "docs/APPROVALS.md"
CODE = (glob.glob("tools/**/*.py", recursive=True) + glob.glob("tools/*.sh")
        + glob.glob("scripts/*") + ["Makefile"])

FAULT = re.compile(r"^### (F\d+b?) · ")
SECTION = re.compile(r"^## (\d+) · ")
CITE_F = re.compile(r"(?<![\w-])F(\d+b?)(?![\w-])")
CITE_S = re.compile(r"§ ?(\d+)")
SCRIPT = re.compile(r"\b([a-z_][a-z0-9_]*\.(?:py|sh))\b")
LINENO = re.compile(r"\b[a-z_]+\.py:\d+")
TICK = re.compile(r"`([^`]+)`")
NAME = re.compile(r"\b([A-Z][A-Z0-9]*_[A-Z0-9_]+|[a-z_][a-z0-9]*_[a-z0-9_]+"
                  r"|[a-z_]\w*(?=\())")


def method_ids(lines):
    faults, sections, retired, listed = [], set(), set(), set()
    in_retired = in_probes = False
    for n, line in enumerate(lines, 1):
        if line.startswith("## "):
            in_probes = line.startswith("## 4 ·")
        if in_probes and line.startswith("| `"):
            listed.update(re.findall(r"`([a-z_]+(?:\.py|\.sh|/))`",
                                     line.split("|")[1]))
        m = FAULT.match(line)
        if m:
            faults.append((m.group(1), n))
        m = SECTION.match(line)
        if m:
            sections.add(m.group(1))
        if line.startswith("#"):
            in_retired = line.startswith("### Retired")
        elif in_retired and line.startswith("| `"):
            retired.update(re.findall(r"`([^`]+)`", line.split("|")[1]))
    return faults, sections, retired, listed


def key(fid):
    return (int(fid[1:].rstrip("b")), fid.endswith("b"))


def main():
    lines = open(METHOD, encoding="utf-8").read().splitlines()
    faults, sections, retired, listed = method_ids(lines)
    retired |= {r.rsplit(".", 1)[0] for r in retired}
    have = {f for f, _ in faults}
    bad = []

    seen = {}
    for fid, n in faults:
        if fid in seen:
            bad.append(f"{METHOD}:{n}: {fid} is already used at line {seen[fid]}")
        seen.setdefault(fid, n)
    for (a, _), (b, n) in zip(faults, faults[1:]):
        if key(b) < key(a):
            bad.append(f"{METHOD}:{n}: {b} comes after {a}")

    corpus = {}
    for p in CODE:
        try:
            corpus[p] = open(p, encoding="utf-8").read()
        except (OSError, UnicodeDecodeError):
            continue
    code = "\n".join(corpus.values())
    scripts = {p.rsplit("/", 1)[-1] for p in corpus}

    for p in sorted(glob.glob("tools/*.py") + glob.glob("tools/*.sh")
                    + glob.glob("tools/*/")):
        name = p.split("tools/", 1)[1].rstrip("/")
        if name.endswith("/") or name in ("__pycache__", "out"):
            continue
        if not any(x == name or x.startswith(name + "/") for x in listed) \
                and name not in retired:
            bad.append(f"{METHOD} §4: tools/{name} has no row in the inventory")

    def cites(path, text, names, only=None):
        for n, line in enumerate(text.splitlines(), 1):
            if only and not any(o in line for o in only):
                continue
            where = f"{path}:{n}"
            for f in CITE_F.findall(line):
                if "F" + f not in have:
                    bad.append(f"{where}: cites F{f}, which METHOD does not have")
            for s in CITE_S.findall(line):
                if s not in sections:
                    bad.append(f"{where}: cites §{s}, which METHOD does not have")
            if not names:
                continue
            for m in LINENO.findall(line):
                bad.append(f"{where}: cites a line number, {m} -- cite the symbol")
            for s in SCRIPT.findall(line):
                if s not in scripts and s not in retired:
                    bad.append(f"{where}: cites {s}, which does not exist")
            for tok in TICK.findall(line):
                for name in NAME.findall(tok):
                    if name not in code and name not in retired:
                        bad.append(f"{where}: cites `{name}`, not in the code")

    for p in NAMED:
        cites(p, open(p, encoding="utf-8").read(), True)
    cites(LEDGER, open(LEDGER, encoding="utf-8").read(), False)
    # code comments cite METHOD too, and those citations drift the same way
    for p, text in corpus.items():
        cites(p, text, False, only=("METHOD", "§"))

    for b in bad:
        print("  !", b)
    if bad:
        print(f"{len(bad)} doc findings")
        return 1
    print(f"docs agree with the code ({len(faults)} faults, "
          f"{len(sections)} sections, {len(retired)} retired names)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
