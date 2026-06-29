from __future__ import annotations

import argparse
import json
import time

from sau_platform.service import platform_service


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="sau-platform-worker",
        description="Run due tasks for the minimal control plane.",
    )
    parser.add_argument("--limit", default=10, type=int, help="Max due tasks to run once")
    parser.add_argument("--loop", action="store_true", help="Run forever with a fixed interval")
    parser.add_argument("--interval", default=30, type=int, help="Loop interval seconds")
    parser.add_argument("--max-iterations", default=0, type=int, help="Stop after N loops, 0 means forever")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    iteration = 0
    while True:
        results = platform_service.run_due_tasks(limit=args.limit)
        print(json.dumps(results, ensure_ascii=False, indent=2, default=str))

        if not args.loop:
            break

        iteration += 1
        if args.max_iterations and iteration >= args.max_iterations:
            break
        time.sleep(max(1, int(args.interval)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
