"""scicodewiki command-line entry."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path


def _repo_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--repo", default=".",
                        help="target repository root (default: cwd)")
    parser.add_argument("--formulas", default=None,
                        help="formulas dir (default: <repo>/formulas)")


def _cmd_verify(args) -> int:
    import os

    from .drift import head_commit
    from .verify import verify_repo

    repo = Path(args.repo).resolve()
    # formula_impl modules locate the target package through this
    os.environ["SCICODEWIKI_REPO"] = str(repo)
    formulas = Path(args.formulas) if args.formulas else repo / "formulas"
    commit = head_commit(repo) or "nogit"
    results = verify_repo(formulas, commit=commit, seed=args.seed,
                          only=args.entry)
    if not results:
        print(f"scicodewiki: no entries under {formulas}", file=sys.stderr)
        return 2
    failed = 0
    for entry, verdict in results:
        line = f"{entry.id}: {verdict.result}"
        if verdict.diagnosis:
            line += f" -- {verdict.diagnosis}"
        print(line)
        failed += verdict.result == "fail"
    return 1 if failed else 0


def _cmd_build(args) -> int:
    from .render import build

    repo = Path(args.repo).resolve()
    formulas = Path(args.formulas) if args.formulas else repo / "formulas"
    out = Path(args.out) if args.out else repo / "wiki"
    for path in build(repo, formulas, out):
        print(path)
    return 0


CONVENTION_SECTION = """<!-- scicodewiki:conventions -->
## scicodewiki 约定

- 本仓库有 formulas/ 注册表：机器可验证的科学断言（公式/约定/文献）。
- 代码绑定清单：formulas/ 各 yaml 的 implements.file。
- 改动绑定代码后：跑 `scicodewiki verify --repo .`，处理 ❌ failing / 🕐 stale 徽章。
- wiki：`scicodewiki build`（输出 wiki/）。
<!-- /scicodewiki:conventions -->
"""


def _cmd_init(args) -> int:
    repo = Path(args.repo).resolve()
    formulas = repo / "formulas"
    formulas.mkdir(exist_ok=True)
    manifest = formulas / "manifest.yaml"
    if not manifest.exists():
        manifest.write_text(f"repo: {repo.name}\nstages: []\n",
                            encoding="utf-8")
        print(f"created {manifest}")
    for name in ("AGENTS.md", "CLAUDE.md"):
        target = repo / name
        existing = target.read_text(encoding="utf-8") if target.exists() else ""
        if "scicodewiki:conventions" in existing:
            print(f"{name}: conventions already present")
            continue
        target.write_text(
            existing + ("\n" if existing.strip() else "") + CONVENTION_SECTION,
            encoding="utf-8")
        print(f"{name}: conventions injected")
    return 0


def _cmd_drift(args) -> int:
    from .drift import badge_state
    from .registry import load_entries

    repo = Path(args.repo).resolve()
    formulas = Path(args.formulas) if args.formulas else repo / "formulas"
    entries = load_entries(formulas)
    if not entries:
        print(f"scicodewiki: no entries under {formulas}", file=sys.stderr)
        return 2
    for entry in entries:
        print(f"{entry.id}: {badge_state(entry, repo)}")
    return 0


def _not_implemented(name: str) -> int:
    print(f"scicodewiki {name}: not implemented yet", file=sys.stderr)
    return 2


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(
        prog="scicodewiki",
        description="Verified scientific documentation layer for "
                    "scientific computing repositories",
    )
    sub = parser.add_subparsers(dest="command")

    p = sub.add_parser("verify", help="run equivalence gates over registry entries")
    _repo_args(p)
    p.add_argument("--entry", help="verify a single entry id")
    p.add_argument("--seed", type=int, default=0,
                   help="holdout sampler seed (gate authority: fresh seed each run)")
    p.set_defaults(fn=_cmd_verify)

    p = sub.add_parser("build", help="render the wiki site")
    _repo_args(p)
    p.add_argument("--out", default=None,
                   help="output dir (default: <repo>/wiki)")
    p.set_defaults(fn=_cmd_build)

    p = sub.add_parser("drift", help="report badge states (verified/stale/failing/unverified)")
    _repo_args(p)
    p.set_defaults(fn=_cmd_drift)

    p = sub.add_parser("on-edit", help="hook entrypoint: read hook JSON on stdin, gate bound entries")
    p.set_defaults(fn=lambda a: __import__(
        "scicodewiki.hookcheck", fromlist=["main"]).main())

    p = sub.add_parser("init", help="seed formulas/ + AGENTS.md conventions in a target repo")
    _repo_args(p)
    p.set_defaults(fn=_cmd_init)

    args = parser.parse_args(argv)
    if args.command is None:
        parser.print_help()
        return 0
    return args.fn(args)


if __name__ == "__main__":
    sys.exit(main())
