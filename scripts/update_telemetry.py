"""Rotating 7-day GitHub portfolio & embedded ecosystem auditing engine.

Replaces identical daily timestamp updates with a live, GitHub-API-driven
7-day engineering audit cycle (Monday-Sunday) and a smart contribution check
that avoids duplicate automated commits on days with manual coding activity.
"""

import argparse
import json
import os
import re
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Callable

GITHUB_USER = "sherifred-singh"
REPO_ROOT = Path(__file__).resolve().parent.parent
TELEMETRY_DIR = REPO_ROOT / "telemetry"
HISTORY_DIR = TELEMETRY_DIR / "history"
COMMIT_MSG_FILE = REPO_ROOT / ".git" / "TELEMETRY_COMMIT_MSG"

NON_FIRMWARE_REPOS = {
    "Awesome-Embedded",
    "c-programming-interview-preparation",
    "leetcode-solutions",
    "sherifred-singh",
    "sherifred-singh.github.io",
    "theEmbeddedNewTestament.github.io",
}

DAY_SCHEDULE = {
    1: "CI & Workflow Health Audit",
    2: "Repository Metrics & Velocity Report",
    3: "Profile Links & Badge Health Audit",
    4: "Actions & Toolchain Version Audit",
    5: "Open Issues & Maintenance Triage",
    6: "Weekly Snapshot & Telemetry Index",
    7: "Profile README Dashboard Sync",
}


def get_ist_utc_now() -> tuple[datetime, datetime]:
    """Return current UTC and IST datetimes."""
    utc_now = datetime.now(timezone.utc)
    ist_tz = timezone(timedelta(hours=5, minutes=30))
    return utc_now, utc_now.astimezone(ist_tz)


def _github_headers() -> dict[str, str]:
    headers = {
        "User-Agent": "Sherifred-Ecosystem-Auditor/2.0",
        "Accept": "application/vnd.github+json",
    }
    token = os.environ.get("GITHUB_TOKEN", "").strip()
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return headers


_API_CACHE: dict[str, Any] = {}


def github_api_get(endpoint: str, timeout: int = 15) -> Any:
    """Fetch JSON from a GitHub REST API endpoint or full URL with in-process caching."""
    url = endpoint if endpoint.startswith("http") else f"https://api.github.com{endpoint}"
    if url in _API_CACHE:
        return _API_CACHE[url]
    req = urllib.request.Request(url, headers=_github_headers())
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        data = json.loads(resp.read().decode("utf-8"))
    _API_CACHE[url] = data
    return data


def fetch_text(url: str, timeout: int = 12, use_browser_ua: bool = False) -> str:
    """Fetch raw text content from a URL."""
    ua = "Mozilla/5.0" if use_browser_ua else "Sherifred-Ecosystem-Auditor/2.0"
    req = urllib.request.Request(url, headers={"User-Agent": ua})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.read().decode("utf-8", errors="ignore")


def fetch_all_repos() -> list[dict[str, Any]]:
    """Retrieve all public repositories for GITHUB_USER sorted by latest push."""
    repos = github_api_get(f"/users/{GITHUB_USER}/repos?per_page=100&sort=pushed")
    return [r for r in repos if not r.get("fork")]


def filter_embedded_repos(repos: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Filter repositories representing embedded firmware and HIL test projects."""
    return sorted(
        [r for r in repos if r["name"] not in NON_FIRMWARE_REPOS],
        key=lambda r: r["name"],
    )


def has_contributed_today(utc_now: datetime) -> tuple[bool, str]:
    """Check whether any contribution is already recorded on GitHub for today (UTC).

    Checks both GitHub's native contribution calendar and recent repo push timestamps.
    """
    today_utc = utc_now.strftime("%Y-%m-%d")

    try:
        html = fetch_text(
            f"https://github.com/users/{GITHUB_USER}/contributions",
            use_browser_ua=True,
        )
        match = re.search(rf'data-date="{today_utc}"[^>]*data-level="(\d+)"', html)
        if not match:
            match = re.search(rf'data-level="(\d+)"[^>]*data-date="{today_utc}"', html)
        if match and int(match.group(1)) > 0:
            return True, f"GitHub contribution graph already shows level {match.group(1)} for {today_utc} UTC"
    except Exception as exc:
        print(f"Warning: could not check GitHub contributions page ({exc})", file=sys.stderr)

    try:
        repos = fetch_all_repos()
        pushed_today = [r["name"] for r in repos if str(r.get("pushed_at", "")).startswith(today_utc)]
        if pushed_today:
            return True, f"Repository push already recorded today ({today_utc} UTC): {', '.join(pushed_today)}"
    except Exception as exc:
        print(f"Warning: could not check recent repo pushes ({exc})", file=sys.stderr)

    return False, f"No contribution recorded yet for {today_utc} UTC"


def audit_embedded_ci(embedded_repos: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """Query latest GitHub Actions run for each embedded firmware repository."""
    results = []
    passing = 0
    failing = 0
    no_ci = 0

    for repo in embedded_repos:
        name = repo["name"]
        entry = {
            "name": name,
            "language": repo.get("language") or "N/A",
            "workflow": "N/A",
            "status": "NO_WORKFLOW_RUNS",
            "last_run_utc": "N/A",
            "run_url": repo.get("html_url", ""),
        }
        try:
            data = github_api_get(f"/repos/{GITHUB_USER}/{name}/actions/runs?per_page=1")
            runs = data.get("workflow_runs", [])
            if runs:
                run = runs[0]
                conclusion = run.get("conclusion") or run.get("status") or "unknown"
                entry["workflow"] = run.get("name") or "CI"
                entry["status"] = conclusion.upper()
                entry["last_run_utc"] = run.get("created_at", "N/A")
                entry["run_url"] = run.get("html_url") or entry["run_url"]
                if conclusion == "success":
                    passing += 1
                elif conclusion in {"failure", "timed_out", "action_required"}:
                    failing += 1
            else:
                no_ci += 1
        except Exception as exc:
            entry["status"] = f"API_ERROR ({type(exc).__name__})"
        results.append(entry)

    ci_enabled = passing + failing
    pass_rate = f"{(passing / ci_enabled * 100.0):.1f}%" if ci_enabled > 0 else "N/A"
    summary = {
        "total_repositories": len(embedded_repos),
        "ci_enabled_repositories": ci_enabled,
        "passing_ci_runs": passing,
        "failing_ci_runs": failing,
        "repositories_without_ci": no_ci,
        "ci_health_rate": pass_rate,
    }
    return results, summary


def write_text_file(path: Path, content: str) -> None:
    """Ensure parent directories exist and write UTF-8 text."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def write_commit_message(message: str) -> None:
    """Write the day-specific commit message into .git/TELEMETRY_COMMIT_MSG if in a git repo."""
    if COMMIT_MSG_FILE.parent.is_dir():
        COMMIT_MSG_FILE.write_text(message + "\n", encoding="utf-8")


def run_day_1_ci_health(utc_now: datetime, ist_now: datetime) -> str:
    """Day 1 (Mon): Audit live GitHub Actions workflow runs across embedded repos."""
    repos = fetch_all_repos()
    embedded = filter_embedded_repos(repos)
    ci_results, metrics = audit_embedded_ci(embedded)

    overall_status = (
        "ALL CI WORKFLOWS PASSING"
        if metrics["failing_ci_runs"] == 0 and metrics["passing_ci_runs"] > 0
        else f"{metrics['failing_ci_runs']} FAILING CI WORKFLOW(S)"
    )

    payload = {
        "engineer": "Sherifred Singh",
        "profile": f"https://github.com/{GITHUB_USER}",
        "domain": "Automotive & Safety-Critical Embedded Firmware",
        "audit_day": "Day 1 - Live CI & Workflow Health",
        "last_sync_utc": utc_now.strftime("%Y-%m-%d %H:%M:%S UTC"),
        "last_sync_ist": ist_now.strftime("%Y-%m-%d %I:%M:%S %p IST"),
        "status": overall_status,
        "metrics": metrics,
        "monitored_repositories": ci_results,
    }
    write_text_file(TELEMETRY_DIR / "ecosystem_status.json", json.dumps(payload, indent=2) + "\n")

    lines = [
        "# 🛡️ Embedded Firmware Live CI Health Audit",
        "",
        f"**Audit Timestamp:** `{ist_now.strftime('%d-%b-%Y %I:%M:%S %p IST')}` (`{utc_now.strftime('%Y-%m-%d %H:%M:%S UTC')}`)",
        f"- **Embedded Repositories Audited:** `{metrics['total_repositories']}`",
        f"- **CI-Enabled Repositories:** `{metrics['ci_enabled_repositories']}`",
        f"- **Passing / Failing:** `{metrics['passing_ci_runs']} passing` / `{metrics['failing_ci_runs']} failing` (`{metrics['ci_health_rate']}`)",
        "",
        "| Repository | Language | Workflow | Latest Run (UTC) | Status |",
        "| :--- | :--- | :--- | :--- | :--- |",
    ]
    for item in ci_results:
        icon = "✅" if item["status"] == "SUCCESS" else ("⚠️" if "ERROR" in item["status"] or item["status"] == "NO_WORKFLOW_RUNS" else "❌")
        lines.append(
            f"| [`{item['name']}`](https://github.com/{GITHUB_USER}/{item['name']}) | "
            f"{item['language']} | {item['workflow']} | `{item['last_run_utc']}` | "
            f"[{icon} `{item['status']}`]({item['run_url']}) |"
        )
    lines.extend(["", "---", "*Generated dynamically from GitHub Actions REST API (`/actions/runs`).*"])
    write_text_file(TELEMETRY_DIR / "ci_health.md", "\n".join(lines) + "\n")

    return "chore(ci-audit): verify live GitHub Actions health across embedded repos [skip ci]"


def run_day_2_repo_metrics(utc_now: datetime, ist_now: datetime) -> str:
    """Day 2 (Tue): Aggregate live portfolio metrics, language mix, and recent pushes."""
    user = github_api_get(f"/users/{GITHUB_USER}")
    repos = fetch_all_repos()
    portfolio = [r for r in repos if r["name"] != GITHUB_USER]

    lang_stats: dict[str, dict[str, int]] = {}
    total_stars = 0
    total_forks = 0
    total_size_kb = 0

    for repo in portfolio:
        lang = repo.get("language") or "Documentation/Other"
        size = int(repo.get("size") or 0)
        lang_stats.setdefault(lang, {"count": 0, "size_kb": 0})
        lang_stats[lang]["count"] += 1
        lang_stats[lang]["size_kb"] += size
        total_stars += int(repo.get("stargazers_count") or 0)
        total_forks += int(repo.get("forks_count") or 0)
        total_size_kb += size

    lines = [
        "# 📊 Embedded Portfolio Metrics & Language Footprint",
        "",
        f"**Audit Timestamp:** `{ist_now.strftime('%d-%b-%Y %I:%M:%S %p IST')}` (`{utc_now.strftime('%Y-%m-%d %H:%M:%S UTC')}`)",
        f"- **Public Repositories:** `{user.get('public_repos', len(repos))}` (`{len(portfolio)}` project repos)",
        f"- **Followers / Following:** `{user.get('followers', 0)}` / `{user.get('following', 0)}`",
        f"- **Total Stars / Forks:** `{total_stars}` ⭐ / `{total_forks}` 🍴",
        f"- **Tracked Codebase Size:** `{total_size_kb:,} KB`",
        "",
        "## 💻 Language Distribution",
        "",
        "| Primary Language | Repositories | Footprint (KB) |",
        "| :--- | :---: | :---: |",
    ]
    for lang, data in sorted(lang_stats.items(), key=lambda x: (-x[1]["count"], -x[1]["size_kb"])):
        lines.append(f"| `{lang}` | {data['count']} | {data['size_kb']:,} |")

    lines.extend([
        "",
        "## 🚀 Most Recently Updated Repositories",
        "",
        "| Repository | Language | Size (KB) | Stars | Forks | Last Push (UTC) |",
        "| :--- | :--- | :---: | :---: | :---: | :--- |",
    ])
    for repo in portfolio[:15]:
        lines.append(
            f"| [`{repo['name']}`]({repo['html_url']}) | {repo.get('language') or 'Other'} | "
            f"{repo.get('size', 0):,} | {repo.get('stargazers_count', 0)} | "
            f"{repo.get('forks_count', 0)} | `{repo.get('pushed_at', 'N/A')}` |"
        )
    lines.extend(["", "---", "*Generated dynamically from GitHub Users & Repositories REST API.*"])
    write_text_file(TELEMETRY_DIR / "repo_metrics.md", "\n".join(lines) + "\n")

    return "docs(telemetry): refresh live embedded repository metrics & language footprint [skip ci]"


def _check_url_health(url: str) -> tuple[str, str, int]:
    """Perform an HTTP health check returning (state, detail, latency_ms)."""
    headers = {"User-Agent": "Mozilla/5.0 (compatible; PortfolioLinkAuditor/1.0)"}
    start = time.monotonic()
    for method in ("HEAD", "GET"):
        req = urllib.request.Request(url, headers=headers, method=method)
        try:
            with urllib.request.urlopen(req, timeout=10) as resp:
                ms = int((time.monotonic() - start) * 1000)
                return "OK", f"HTTP {resp.getcode()}", ms
        except urllib.error.HTTPError as exc:
            ms = int((time.monotonic() - start) * 1000)
            if exc.code == 405 and method == "HEAD":
                continue
            if exc.code in {403, 999} and "linkedin.com" in url:
                return "BOT_PROTECTED", f"HTTP {exc.code} (LinkedIn Bot Guard)", ms
            return "HTTP_ERROR", f"HTTP {exc.code} {exc.reason}", ms
        except Exception as exc:
            ms = int((time.monotonic() - start) * 1000)
            return "TIMEOUT/ERROR", type(exc).__name__, ms
    return "UNKNOWN", "No response", 0


def _extract_readme_urls(readme_text: str) -> list[str]:
    """Extract unique HTTPS URLs from HTML attributes and Markdown links intact."""
    pattern = re.compile(
        r'(?:src|href)=["\'](https://[^"\']+)["\']'
        r'|\]\((https://[^\s)]+(?:\([^\s)]*\)[^\s)]*)*)\)'
    )
    urls = [m.group(1) or m.group(2) for m in pattern.finditer(readme_text)]
    return list(dict.fromkeys(u.rstrip(".,;") for u in urls))


def run_day_3_link_audit(utc_now: datetime, ist_now: datetime) -> str:
    """Day 3 (Wed): Verify HTTP availability of URLs and badges in README.md."""
    readme_text = (REPO_ROOT / "README.md").read_text(encoding="utf-8")
    unique_urls = _extract_readme_urls(readme_text)

    results = []
    ok_count = 0
    warn_count = 0
    err_count = 0

    for url in unique_urls:
        state, detail, ms = _check_url_health(url)
        if state == "OK":
            ok_count += 1
        elif state == "BOT_PROTECTED":
            warn_count += 1
        else:
            err_count += 1
        results.append((url, state, detail, ms))

    lines = [
        "# 🔗 Profile README Links & Badge Availability Audit",
        "",
        f"**Audit Timestamp:** `{ist_now.strftime('%d-%b-%Y %I:%M:%S %p IST')}` (`{utc_now.strftime('%Y-%m-%d %H:%M:%S UTC')}`)",
        f"- **Unique HTTPS Endpoints Checked:** `{len(results)}`",
        f"- **Healthy (`2xx/3xx`):** `{ok_count}` | **Bot-Guarded:** `{warn_count}` | **Timeout/Error:** `{err_count}`",
        "",
        "| Endpoint | Status | Response | Latency |",
        "| :--- | :---: | :--- | :---: |",
    ]
    for url, state, detail, ms in results:
        icon = "✅" if state == "OK" else ("🛡️" if state == "BOT_PROTECTED" else "⚠️")
        short_url = url if len(url) <= 78 else url[:75] + "..."
        lines.append(f"| [`{short_url}`]({url}) | {icon} `{state}` | {detail} | {ms} ms |")

    lines.extend(["", "---", "*Verified dynamically against live endpoints referenced in `README.md`.*"])
    write_text_file(TELEMETRY_DIR / "link_audit.md", "\n".join(lines) + "\n")

    return "chore(audit): verify profile README links, badges & portfolio availability [skip ci]"


def run_day_4_toolchain_audit(utc_now: datetime, ist_now: datetime) -> str:
    """Day 4 (Thu): Inspect workflow YAMLs across embedded repos for runners & actions."""
    embedded = filter_embedded_repos(fetch_all_repos())
    rows = []
    legacy_flags = 0

    for repo in embedded:
        name = repo["name"]
        try:
            items = github_api_get(f"/repos/{GITHUB_USER}/{name}/contents/.github/workflows")
        except Exception:
            rows.append((name, "None", "N/A", "N/A", "ℹ️ No workflow files"))
            continue

        if not isinstance(items, list):
            continue

        for wf in items:
            if not wf["name"].endswith((".yml", ".yaml")):
                continue
            dl_url = wf.get("download_url")
            if not dl_url:
                continue
            try:
                yaml_text = fetch_text(dl_url)
            except Exception:
                rows.append((name, wf["name"], "N/A", "N/A", "⚠️ Fetch error"))
                continue

            runners = sorted(set(re.findall(r"runs-on:\s*([^\s#]+)", yaml_text)))
            actions = sorted(set(re.findall(r"uses:\s*([^\s#]+)", yaml_text)))
            tools = sorted(
                t for t in ("gcc", "arm-none-eabi-gcc", "pytest", "cppcheck", "make", "cmake")
                if re.search(rf"\b{re.escape(t)}\b", yaml_text)
            )
            deprecated = [a for a in actions if re.search(r"@v[123]\b", a)]
            if deprecated:
                legacy_flags += 1
                status = f"⚠️ Update {', '.join(deprecated)}"
            else:
                status = "✅ Modern actions"

            rows.append((
                name,
                wf["name"],
                ", ".join(runners) or "N/A",
                ", ".join(tools) or "N/A",
                status,
            ))

    lines = [
        "# 🔧 CI Workflow Actions & Embedded Build Toolchain Audit",
        "",
        f"**Audit Timestamp:** `{ist_now.strftime('%d-%b-%Y %I:%M:%S %p IST')}` (`{utc_now.strftime('%Y-%m-%d %H:%M:%S UTC')}`)",
        f"- **Workflow Files Inspected:** `{len(rows)}`",
        f"- **Legacy Action Version Flags (`@v1/@v2/@v3`):** `{legacy_flags}`",
        "",
        "| Repository | Workflow File | Runner | Detected Toolchains | Audit |",
        "| :--- | :--- | :--- | :--- | :--- |",
    ]
    for name, wf_name, runner, tools, status in rows:
        lines.append(
            f"| [`{name}`](https://github.com/{GITHUB_USER}/{name}) | `{wf_name}` | "
            f"`{runner}` | `{tools}` | {status} |"
        )
    lines.extend(["", "---", "*Audited directly from live `.github/workflows/*.yml` definitions across embedded repos.*"])
    write_text_file(TELEMETRY_DIR / "toolchain_audit.md", "\n".join(lines) + "\n")

    return "chore(toolchain): audit CI workflow actions & embedded build runners [skip ci]"


def run_day_5_maintenance_triage(utc_now: datetime, ist_now: datetime) -> str:
    """Day 5 (Fri): Audit open issues, PRs, descriptions, licenses, and staleness."""
    repos = [r for r in fetch_all_repos() if r["name"] != GITHUB_USER]
    open_items = []
    hygiene_notes = []

    for repo in repos:
        name = repo["name"]
        issue_count = int(repo.get("open_issues_count") or 0)
        if issue_count > 0:
            try:
                issues = github_api_get(f"/repos/{GITHUB_USER}/{name}/issues?state=open&per_page=10")
                for iss in issues:
                    kind = "PR" if "pull_request" in iss else "Issue"
                    open_items.append((name, kind, iss["number"], iss["title"], iss["html_url"]))
            except Exception:
                open_items.append((name, "Issue/PR", 0, f"{issue_count} open item(s)", repo["html_url"]))

        missing = []
        if not repo.get("description"):
            missing.append("description")
        if not repo.get("license"):
            missing.append("license")
        pushed_str = str(repo.get("pushed_at", ""))
        age_days = -1
        if pushed_str:
            pushed_dt = datetime.fromisoformat(pushed_str.replace("Z", "+00:00"))
            age_days = (utc_now - pushed_dt).days
        hygiene_notes.append((name, repo.get("default_branch", "main"), age_days, ", ".join(missing) or "Clean"))

    lines = [
        "# 🧹 Portfolio Open Issues & Repository Hygiene Triage",
        "",
        f"**Audit Timestamp:** `{ist_now.strftime('%d-%b-%Y %I:%M:%S %p IST')}` (`{utc_now.strftime('%Y-%m-%d %H:%M:%S UTC')}`)",
        f"- **Repositories Audited:** `{len(repos)}`",
        f"- **Open Issues / Pull Requests:** `{len(open_items)}`",
        "",
        "## 📌 Open Issues & Pull Requests",
        "",
    ]
    if open_items:
        lines.extend(["| Repository | Type | # | Title |", "| :--- | :---: | :---: | :--- |"])
        for name, kind, num, title, url in open_items:
            lines.append(f"| [`{name}`](https://github.com/{GITHUB_USER}/{name}) | {kind} | [#{num}]({url}) | {title} |")
    else:
        lines.append("✅ No open issues or pull requests across public repositories.")

    lines.extend([
        "",
        "## 📋 Repository Hygiene Check",
        "",
        "| Repository | Default Branch | Days Since Push | Metadata Hygiene |",
        "| :--- | :---: | :---: | :--- |",
    ])
    for name, branch, age, status in sorted(hygiene_notes, key=lambda x: x[0]):
        badge = "✅ Clean" if status == "Clean" else f"📝 Missing: `{status}`"
        lines.append(f"| [`{name}`](https://github.com/{GITHUB_USER}/{name}) | `{branch}` | {age}d | {badge} |")

    lines.extend(["", "---", "*Generated dynamically via GitHub Repositories & Issues REST API.*"])
    write_text_file(TELEMETRY_DIR / "maintenance_triage.md", "\n".join(lines) + "\n")

    return "docs(maintenance): audit open issues, PRs & repo hygiene across portfolio [skip ci]"


def run_day_6_weekly_snapshot(utc_now: datetime, ist_now: datetime) -> str:
    """Day 6 (Sat): Save immutable weekly JSON snapshot and update telemetry/README.md."""
    iso_year, iso_week, _ = ist_now.isocalendar()
    week_id = f"{iso_year}-W{iso_week:02d}"

    user = github_api_get(f"/users/{GITHUB_USER}")
    repos = fetch_all_repos()
    embedded = filter_embedded_repos(repos)
    _, ci_metrics = audit_embedded_ci(embedded)

    snapshot = {
        "week": week_id,
        "recorded_utc": utc_now.strftime("%Y-%m-%d %H:%M:%S UTC"),
        "recorded_ist": ist_now.strftime("%Y-%m-%d %I:%M:%S %p IST"),
        "public_repos": user.get("public_repos", len(repos)),
        "followers": user.get("followers", 0),
        "total_stars": sum(int(r.get("stargazers_count") or 0) for r in repos),
        "total_forks": sum(int(r.get("forks_count") or 0) for r in repos),
        "total_codebase_kb": sum(int(r.get("size") or 0) for r in repos if r["name"] != GITHUB_USER),
        "embedded_ci": ci_metrics,
    }
    write_text_file(HISTORY_DIR / f"{week_id}.json", json.dumps(snapshot, indent=2) + "\n")

    history_files = sorted(HISTORY_DIR.glob("*.json"), reverse=True) if HISTORY_DIR.exists() else []
    history_links = ", ".join(f"[`{f.stem}`](./history/{f.name})" for f in history_files[:12]) or "None yet"

    readme_lines = [
        "# 📡 Embedded Firmware Ecosystem Telemetry (7-Day Rotating Audit)",
        "",
        f"**Last Automated Verification:** `{ist_now.strftime('%d-%b-%Y %I:%M:%S %p IST')}` (`{utc_now.strftime('%Y-%m-%d %H:%M:%S UTC')}`)",
        f"- **Engineer:** [Sherifred Singh](https://github.com/{GITHUB_USER})",
        f"- **Embedded Repositories Audited:** `{ci_metrics['total_repositories']}`",
        f"- **CI Health Rate:** `{ci_metrics['ci_health_rate']}` (`{ci_metrics['passing_ci_runs']}` passing / `{ci_metrics['failing_ci_runs']}` failing)",
        f"- **Total Public Stars / Forks:** `{snapshot['total_stars']}` ⭐ / `{snapshot['total_forks']}` 🍴",
        "",
        "### 📅 Weekly Rotating Audit Schedule",
        "",
        "| Day | Audit Focus | Report File |",
        "| :--- | :--- | :--- |",
        "| **Monday** | Live CI & Workflow Health | [`ci_health.md`](./ci_health.md) · [`ecosystem_status.json`](./ecosystem_status.json) |",
        "| **Tuesday** | Portfolio Metrics & Language Mix | [`repo_metrics.md`](./repo_metrics.md) |",
        "| **Wednesday** | Profile Links & Badge Health | [`link_audit.md`](./link_audit.md) |",
        "| **Thursday** | Actions & Build Toolchain Check | [`toolchain_audit.md`](./toolchain_audit.md) |",
        "| **Friday** | Open Issues & Repo Hygiene Triage | [`maintenance_triage.md`](./maintenance_triage.md) |",
        "| **Saturday** | Weekly Immutable Snapshot & Index | [`README.md`](./README.md) · [`history/`](./history) |",
        "| **Sunday** | Profile Dashboard & Badge Sync | [`../README.md`](../README.md) |",
        "",
        "### 🗂️ Historical Weekly Snapshots",
        f"- {history_links}",
        "",
        "---",
        "*Automated smart-fallback scheduler: executes only when no manual repository activity is recorded for the day, capping automated commits at max 1/day.*",
    ]
    write_text_file(TELEMETRY_DIR / "README.md", "\n".join(readme_lines) + "\n")

    return f"chore(archive): record weekly embedded ecosystem snapshot ({week_id}) [skip ci]"


def run_day_7_profile_sync(utc_now: datetime, ist_now: datetime) -> str:
    """Day 7 (Sun): Refresh profile README.md badge cache busters once per week."""
    readme_path = REPO_ROOT / "README.md"
    if readme_path.exists():
        content = readme_path.read_text(encoding="utf-8")
        cache_buster = ist_now.strftime("%m%d%H%M")
        updated = re.sub(r"(&v=)\d+", rf"\g<1>{cache_buster}", content)
        if updated != content:
            readme_path.write_text(updated, encoding="utf-8")
            print(f"Updated README.md badge cache buster to v={cache_buster}")
        else:
            print("README.md cache buster pattern not found or unchanged.")

    return "docs(profile): weekly profile dashboard & streak badge sync [skip ci]"


DAY_HANDLERS: dict[int, Callable[[datetime, datetime], str]] = {
    1: run_day_1_ci_health,
    2: run_day_2_repo_metrics,
    3: run_day_3_link_audit,
    4: run_day_4_toolchain_audit,
    5: run_day_5_maintenance_triage,
    6: run_day_6_weekly_snapshot,
    7: run_day_7_profile_sync,
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="7-day rotating embedded ecosystem audit")
    parser.add_argument(
        "--skip-if-active",
        action="store_true",
        help="Skip execution if a GitHub contribution is already recorded today (UTC).",
    )
    parser.add_argument(
        "--day",
        type=int,
        choices=range(1, 8),
        help="Override weekday index (1=Mon .. 7=Sun). Defaults to current IST weekday.",
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Run all 7 day handlers sequentially (useful for initial bootstrap/testing).",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    utc_now, ist_now = get_ist_utc_now()

    if args.skip_if_active and not args.all and not args.day:
        active, reason = has_contributed_today(utc_now)
        print(f"Smart-fallback check: {reason}")
        if active:
            print("Skipping automated audit to avoid redundant commits.")
            return 0

    if args.all:
        for day_num in range(1, 8):
            print(f"Running Day {day_num}: {DAY_SCHEDULE[day_num]}...")
            msg = DAY_HANDLERS[day_num](utc_now, ist_now)
            print(f"  Completed -> {msg}")
        write_commit_message("chore(telemetry): initialize 7-day rotating embedded ecosystem audit suite [skip ci]")
        return 0

    day_num = args.day if args.day else ist_now.isoweekday()
    print(f"Executing Day {day_num} ({ist_now.strftime('%A')}): {DAY_SCHEDULE[day_num]}")
    commit_msg = DAY_HANDLERS[day_num](utc_now, ist_now)
    write_commit_message(commit_msg)
    print(f"Audit completed for {ist_now.strftime('%Y-%m-%d %H:%M:%S IST')}")
    print(f"Suggested commit message: {commit_msg}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
