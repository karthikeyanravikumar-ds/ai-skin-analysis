"""Command-line entry point for the explanation service."""

import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from ai.explanation.service import explain_analysis


def main() -> int:
    try:
        raw_input = sys.stdin.read()

        if not raw_input.strip():
            raise ValueError("Empty input")

        context = json.loads(raw_input)

        if not isinstance(context, dict):
            raise ValueError("Input must be a JSON object")

        result = explain_analysis(context)

        print(json.dumps(result, ensure_ascii=False))
        return 0

    except Exception:
        print(
            json.dumps({
                "error": "The educational explanation could not be generated."
            }),
            file=sys.stdout,
        )
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
