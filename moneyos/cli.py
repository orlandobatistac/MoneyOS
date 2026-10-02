from __future__ import annotations

import argparse
import json
from pathlib import Path

from .orchestrator import MoneyOS
from .report import markdown_report


def main() -> None:
    parser = argparse.ArgumentParser(prog="moneyos")
    parser.add_argument("command", choices=["refresh", "plan", "run", "status"])
    parser.add_argument("--incoming", type=float, default=0.0, help="Optional newly received cash to route")
    args = parser.parse_args()

    app = MoneyOS()
    if args.command == "refresh":
        result = app.refresh()
    elif args.command == "plan":
        result = app.plan(args.incoming)
    elif args.command == "run":
        result = app.run(args.incoming)
        Path("runtime/latest.md").write_text(markdown_report(result), encoding="utf-8")
    else:
        result = app.store.read("latest.json", {})

    print(json.dumps(result, indent=2, default=str))


if __name__ == "__main__":
    main()
