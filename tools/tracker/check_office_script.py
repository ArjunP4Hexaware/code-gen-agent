"""Check an Office Script for the rules Excel's Office Scripts compiler enforces and plain
`tsc` does not (tools/tracker/README.md). Run on every script BEFORE giving it to Soham:

    python3 tools/tracker/check_office_script.py tools/tracker/<script>.ts

Exit 1 with line:column findings, 0 when clean. Heuristic (regex), not a parser.
"""
from __future__ import annotations

import re
import sys

ARRAY_METHODS = ("map", "filter", "some", "every", "find", "findIndex", "forEach",
                 "reduce", "reduceRight", "sort", "flatMap")
# a callback passed BY NAME: .filter(isFilled) / .some(this.check) / .sort(byName)
BY_NAME = re.compile(r"\.(" + "|".join(ARRAY_METHODS) + r")\(\s*([A-Za-z_$][\w$.]*)\s*[,)]")
# an old-style function expression as a callback: .map(function (x) {...})
FUNCTION_EXPR = re.compile(r"\.(" + "|".join(ARRAY_METHODS) + r")\(\s*function\b")
ANY = re.compile(r":\s*any\b|<any>|\bas\s+any\b")
RULES = [
    (BY_NAME, "array method callback passed by name - write an arrow function in place "
              "(Office Scripts: 'Only arrow functions may be used in array method callbacks')"),
    (FUNCTION_EXPR, "function expression as an array callback - use an arrow function"),
    (ANY, "explicit 'any' - Office Scripts rejects it; give the type"),
]


def check(path: str) -> list[str]:
    findings = []
    with open(path, encoding="utf-8") as handle:
        for number, line in enumerate(handle, start=1):
            code = line.split("//", 1)[0]
            for pattern, message in RULES:
                for match in pattern.finditer(code):
                    findings.append(f"{path}:{number}:{match.start() + 1}: {message}")
    return findings


def main(argv: list[str]) -> int:
    findings = [f for path in argv for f in check(path)]
    print("\n".join(findings) if findings else f"clean: {', '.join(argv)}")
    return 1 if findings else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
