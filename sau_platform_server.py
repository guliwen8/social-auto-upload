from __future__ import annotations

import argparse

from sau_platform.app import create_app


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="sau-platform", description="Minimal control plane for social-auto-upload.")
    parser.add_argument("--host", default="127.0.0.1", help="Bind host")
    parser.add_argument("--port", default=5510, type=int, help="Bind port")
    parser.add_argument("--debug", action="store_true", help="Enable debug mode")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    app = create_app()
    app.run(host=args.host, port=args.port, debug=args.debug)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
