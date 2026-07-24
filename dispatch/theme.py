"""Shared visual tokens for every rendered page.

One palette, many renderings — the daily digest (E2) and the portfolio
board (E2b) are the same publication family and must not drift apart.
Component CSS stays with each renderer; only the tokens live here.

Byte-sensitive: the E2 golden renders pin the digest's exact output, so any
edit here that changes a token value will fail those tests by design.
"""

TOKENS = """
:root {
  --paper: #f6f8f7; --ink: #1c2422; --muted: #5b6a66; --line: #d8e0dd;
  --card: #ffffff; --accent: #0f6b63; --accent-ink: #0a4f49;
  --good: #1a7a3c; --good-bg: #e5f3ea; --bad: #a33a2a; --bad-bg: #f6e4e0;
  --warn: #8a5a00; --warn-bg: #f6edd8; --code-bg: #eef2f0;
  --mono: ui-monospace, "SF Mono", SFMono-Regular, Menlo, Consolas, monospace;
  --sans: "Seravek", "Avenir Next", "Segoe UI", system-ui, -apple-system, sans-serif;
}
@media (prefers-color-scheme: dark) {
  :root {
    --paper: #151a19; --ink: #e4eae8; --muted: #93a39e; --line: #2c3634;
    --card: #1d2422; --accent: #4fb3a7; --accent-ink: #6ecabe;
    --good: #5cc981; --good-bg: #1a2f22; --bad: #e08573; --bad-bg: #33201b;
    --warn: #d9a94a; --warn-bg: #322a17; --code-bg: #10514c22;
  }
}
"""
