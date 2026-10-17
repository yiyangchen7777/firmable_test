"""CLI: one subcommand per pipeline stage."""

import argparse


def main() -> None:
    parser = argparse.ArgumentParser(prog="firm", description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("triage", help="Part 1: rank datasets likely to contain AU businesses")

    p_onboard = sub.add_parser("onboard", help="Part 2: agent maps one source to the ontology")
    p_onboard.add_argument("dataset_id", help="CKAN dataset id or name")
    p_onboard.add_argument(
        "--decide", default=None,
        help='human review decision: "approve", "reject: <comment>", or "abandon"',
    )

    p_extract = sub.add_parser("extract", help="Part 2: run the engine over a source")
    p_extract.add_argument("source_id", help="source id (config must exist)")
    p_extract.add_argument("--limit", type=int, default=1000, help="rows to sample (default 1000)")
    p_extract.add_argument(
        "--seeded", action="store_true",
        help="big files: half head rows, half rows whose ABN appears in another source",
    )

    sub.add_parser("resolve", help="Part 3: link records across sources")

    p_profile = sub.add_parser("profile", help="Part 4: assemble company profiles")
    p_profile.add_argument("--drop-source", default=None, help="exclude one source and report the diff")

    args = parser.parse_args()

    if args.command == "triage":
        from .triage import run_triage

        run_triage()
    elif args.command == "onboard":
        from .agent.graph import run_onboard

        run_onboard(args.dataset_id, decide=args.decide)
    elif args.command == "extract":
        from .engine import run_extract

        run_extract(args.source_id, limit=args.limit, seeded=args.seeded)
    elif args.command == "resolve":
        from .resolve import run_resolve

        run_resolve()
    elif args.command == "profile":
        from .profiles import run_profile

        run_profile(drop_source=args.drop_source)


if __name__ == "__main__":
    main()
