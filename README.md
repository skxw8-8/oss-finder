# oss-finder

A command-line tool that finds real, named open-source **apps** for whatever you need — design, productivity, media, and beyond — searching live from GitHub each time you run it.

## Setup

```bash
pip install -r requirements.txt
```

No API key required for normal use (GitHub allows unauthenticated searches at a lower rate limit — see below).

## Usage

```bash
python oss_finder.py "video editing"
python oss_finder.py "note taking" --limit 8
python oss_finder.py "password manager" --strict
python oss_finder.py "design tools" --json
```

### Options

| Flag        | What it does                                                                 |
|-------------|-------------------------------------------------------------------------------|
| `--limit N` | Max number of results (default: 10)                                          |
| `--strict`  | Only show results flagged as verified (drops unverified matches)             |
| `--json`    | Print raw JSON instead of a formatted table                                  |

## How "verified" is determined

A project is flagged **✔ verified** if both are true:
- It has a real open-source license attached on GitHub (MIT, GPL, Apache, etc.)
- It has at least 200 GitHub stars

This is a heuristic for "real, actively-used project" — not a legal or security audit. Unverified results may still be perfectly legitimate (newer or smaller projects); always check the repo, license, and recent commit activity yourself before adopting a tool for anything serious.

## Rate limits

GitHub allows ~10 unauthenticated search requests per minute per IP address. For casual use this is plenty. If you run into a rate-limit error, either wait a minute or set a free personal access token:

```bash
# PowerShell
$env:GITHUB_TOKEN = "your_token_here"

# macOS/Linux
export GITHUB_TOKEN="your_token_here"
```

Generate a token at github.com → Settings → Developer settings → Personal access tokens (no special scopes needed for public search).

## Optional: make it a global command

To run it as `oss-finder` instead of `python oss_finder.py`:

```bash
chmod +x oss_finder.py
sudo mv oss_finder.py /usr/local/bin/oss-finder
```

Then just run:
```bash
oss-finder "note taking"
```
