#!/usr/bin/env python3
"""
oss-finder — find verified, open-source APPS (real named projects, not articles)
for a given need, live from GitHub's public search API.

Usage:
    python oss_finder.py "video editing"
    python oss_finder.py "note taking" --limit 8
    python oss_finder.py "password manager" --strict
    python oss_finder.py "design tools" --json

No API key required (GitHub allows unauthenticated search at a lower rate limit).
If you hit rate limits, set a GITHUB_TOKEN environment variable with a free
personal access token to raise the limit — see README.

Setup:
    pip install -r requirements.txt
"""

import argparse
import json
import os
import sys
from dataclasses import dataclass, asdict

try:
    import requests
except ImportError:
    print("Missing dependency. Run: pip install -r requirements.txt", file=sys.stderr)
    sys.exit(1)

try:
    from rich.console import Console
    from rich.table import Table
    from rich import box
    HAS_RICH = True
except ImportError:
    HAS_RICH = False


GITHUB_API_URL = "https://api.github.com/search/repositories"

# A repo is flagged "verified" if it has a real OSI-style license attached
# AND meets a minimum popularity bar — both are strong signals it's a real,
# actively-used open-source app rather than a toy or abandoned fork.
MIN_STARS_FOR_VERIFIED = 200


@dataclass
class AppResult:
    name: str
    full_name: str
    url: str
    description: str
    stars: int
    license: str
    language: str
    verified: bool


def build_headers() -> dict:
    headers = {"Accept": "application/vnd.github+json"}
    token = os.environ.get("GITHUB_TOKEN")
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return headers


def search_apps(need: str, limit: int = 10, strict: bool = False) -> list[AppResult]:
    query = f"{need} in:name,description,readme"
    params = {
        "q": query,
        "sort": "stars",
        "order": "desc",
        "per_page": min(max(limit * 2, 15), 50),
    }

    resp = requests.get(GITHUB_API_URL, headers=build_headers(), params=params, timeout=15)

    if resp.status_code == 403:
        raise RuntimeError(
            "GitHub API rate limit hit. Wait a bit, or set a GITHUB_TOKEN "
            "environment variable to raise the limit (see README)."
        )
    resp.raise_for_status()

    data = resp.json()
    items = data.get("items", [])

    results: list[AppResult] = []
    for item in items:
        license_info = item.get("license") or {}
        license_name = license_info.get("spdx_id") or license_info.get("name") or "Unknown"
        stars = item.get("stargazers_count", 0)
        has_license = license_name not in ("Unknown", "NOASSERTION", None)
        verified = has_license and stars >= MIN_STARS_FOR_VERIFIED

        if strict and not verified:
            continue

        results.append(AppResult(
            name=item.get("name", ""),
            full_name=item.get("full_name", ""),
            url=item.get("html_url", ""),
            description=(item.get("description") or "").strip(),
            stars=stars,
            license=license_name,
            language=item.get("language") or "—",
            verified=verified,
        ))

        if len(results) >= limit:
            break

    return results


def print_results(need: str, results: list[AppResult], as_json: bool):
    if as_json:
        print(json.dumps([asdict(r) for r in results], indent=2))
        return

    if not results:
        print(f"No open-source apps found for '{need}'. Try a broader or different term.")
        return

    if HAS_RICH:
        console = Console()
        table = Table(title=f"Open-source apps for: {need}", box=box.ROUNDED, show_lines=True)
        table.add_column("Status", width=10)
        table.add_column("App", style="bold")
        table.add_column("★ Stars", justify="right")
        table.add_column("License")
        table.add_column("Lang")
        table.add_column("Link", overflow="fold")
        table.add_column("Description", overflow="fold")

        for r in results:
            status = "[green]✔ verified[/green]" if r.verified else "[yellow]unverified[/yellow]"
            table.add_row(
                status, r.name, f"{r.stars:,}", r.license, r.language, r.url,
                r.description[:100] + ("…" if len(r.description) > 100 else "")
            )

        console.print(table)
        console.print(
            f"\n[dim]'verified' = has a real open-source license AND {MIN_STARS_FOR_VERIFIED}+ GitHub stars. "
            "Unverified apps may still be legitimate — just less established or missing license metadata. "
            "Always check the repo yourself before adopting a tool.[/dim]"
        )
    else:
        print(f"\nOpen-source apps for: {need}\n" + "-" * 50)
        for r in results:
            tag = "[VERIFIED]" if r.verified else "[unverified]"
            print(f"{tag} {r.name}  (★{r.stars:,}, {r.license}, {r.language})")
            print(f"  {r.url}")
            print(f"  {r.description[:150]}\n")


def main():
    parser = argparse.ArgumentParser(
        description="Find verified, open-source APPS for a given need, live from GitHub."
    )
    parser.add_argument("need", help='What you need an app for, e.g. "video editing", "note taking"')
    parser.add_argument("--limit", type=int, default=10, help="Max number of results (default: 10)")
    parser.add_argument(
        "--strict", action="store_true",
        help="Only show results flagged as verified (real license + popularity threshold)"
    )
    parser.add_argument("--json", action="store_true", help="Output raw JSON instead of a table")

    args = parser.parse_args()

    try:
        results = search_apps(args.need, limit=args.limit, strict=args.strict)
    except Exception as e:
        print(f"Search failed: {e}", file=sys.stderr)
        sys.exit(1)

    print_results(args.need, results, as_json=args.json)


if __name__ == "__main__":
    main()
