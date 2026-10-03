"""JSON reports; exit 0 actionable plan, 2 invalid input, 3 infeasible."""
import argparse
import json
import sys
from pathlib import Path
from . import load_manifest, assess, plan, LineageError
from .model import hash_file


def main(argv=None):
    parser = argparse.ArgumentParser(prog="lineagefrontier", description="Local provenance impact and conditional rebuild planner; does not execute recipes.")
    sub = parser.add_subparsers(dest="command", required=True)
    digest = sub.add_parser("digest", help="SHA-256 one root-relative local file")
    digest.add_argument("--root", required=True)
    digest.add_argument("path")
    audit = sub.add_parser("plan", help="Verify current bytes, explain staleness and plan requested deliverables")
    audit.add_argument("manifest")
    audit.add_argument("--root", required=True)
    audit.add_argument("--request", action="append", required=True)
    audit.add_argument("--revoke", action="append", default=[], metavar="ID=REASON")
    audit.add_argument("--exact-limit", type=int, default=18)
    args = parser.parse_args(argv)
    try:
        if args.command == "digest":
            from .model import _relative
            report = {"sha256": hash_file(Path(args.root), _relative(args.path, "path"))}
            status = 0
        else:
            revocations = {}
            for entry in args.revoke:
                aid, sep, reason = entry.partition("=")
                if not sep or not reason or aid in revocations:
                    raise LineageError("--revoke needs unique ID=REASON entries")
                revocations[aid] = reason
            manifest = load_manifest(args.manifest)
            assessment = assess(manifest, args.root, revocations)
            decision = plan(manifest, assessment, args.request, exact_limit=args.exact_limit)
            report = {"assessment": assessment, "plan": decision}
            status = 3 if decision["status"] == "INFEASIBLE" else 0
        print(json.dumps(report, indent=2, sort_keys=True))
        return status
    except (LineageError, OSError) as exc:
        print(json.dumps({"error": str(exc)}, sort_keys=True), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
