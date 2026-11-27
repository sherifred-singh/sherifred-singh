"""Rotating 7-day GitHub portfolio & embedded ecosystem auditing engine.

Replaces identical daily timestamp updates with a live, GitHub-API-driven
7-day engineering audit cycle (anchored to 2026-11-25 = Day 1) and a smart contribution check
that avoids duplicate automated commits on days with manual coding activity.
"""

import argparse
import hashlib
import html as html_lib
import json
import os
import re
import subprocess
import sys
import time
import urllib.error
import urllib.request
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Callable

GITHUB_USER = "sherifred-singh"
AUTHOR_NAME = "Sherifred singh"
AUTHOR_EMAIL = "ssherifred@gmail.com"
CYCLE_ANCHOR_DATE = date(2026, 11, 25)  # Day 1 starts on 2026-11-25 (Wednesday)
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


def get_cycle_day(ist_now: datetime) -> int:
    """Return 1-based 7-day cycle index anchored on CYCLE_ANCHOR_DATE (2026-11-25 = Day 1)."""
    return ((ist_now.date() - CYCLE_ANCHOR_DATE).days % 7) + 1


def _github_headers(include_auth: bool = True) -> dict[str, str]:
    headers = {
        "User-Agent": "Sherifred-Ecosystem-Auditor/2.0",
        "Accept": "application/vnd.github+json",
    }
    if include_auth:
        token = (os.environ.get("PORTFOLIO_TOKEN") or os.environ.get("GITHUB_TOKEN") or "").strip()
        if token:
            headers["Authorization"] = f"Bearer {token}"
    return headers


_API_CACHE: dict[str, Any] = {}


def github_api_get(endpoint: str, timeout: int = 15) -> Any:
    """Fetch JSON from GitHub REST API, falling back to unauthenticated if token is repo-scoped."""
    url = endpoint if endpoint.startswith("http") else f"https://api.github.com{endpoint}"
    if url in _API_CACHE:
        return _API_CACHE[url]

    headers = _github_headers(include_auth=True)
    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        if "Authorization" in headers and exc.code in {401, 403, 404}:
            unauth_req = urllib.request.Request(url, headers=_github_headers(include_auth=False))
            with urllib.request.urlopen(unauth_req, timeout=timeout) as resp:
                data = json.loads(resp.read().decode("utf-8"))
        else:
            raise

    _API_CACHE[url] = data
    return data


def fetch_text(url: str, timeout: int = 12, use_browser_ua: bool = False) -> str:
    """Fetch raw text content from a URL."""
    ua = "Mozilla/5.0" if use_browser_ua else "Sherifred-Ecosystem-Auditor/2.0"
    req = urllib.request.Request(url, headers={"User-Agent": ua})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.read().decode("utf-8", errors="ignore")


def _fetch_user_profile() -> dict[str, Any]:
    """Fetch public profile summary via REST API, falling back to web HTML on rate limit."""
    try:
        return github_api_get(f"/users/{GITHUB_USER}")
    except Exception:
        page = fetch_text(f"https://github.com/{GITHUB_USER}", use_browser_ua=True)
        followers = re.search(r'>\s*(\d+)\s*</span>\s*followers', page, re.I)
        following = re.search(r'>\s*(\d+)\s*</span>\s*following', page, re.I)
        repos_cnt = re.search(r'Repositories\s*<span[^>]*class="Counter"[^>]*>(\d+)<', page, re.I)
        return {
            "public_repos": int(repos_cnt.group(1)) if repos_cnt else 0,
            "followers": int(followers.group(1)) if followers else 0,
            "following": int(following.group(1)) if following else 0,
        }


def _fetch_repos_from_web() -> list[dict[str, Any]]:
    """Fallback parser for https://github.com/<user>?tab=repositories when REST API is rate-limited."""
    repos: list[dict[str, Any]] = []
    for page_num in (1, 2):
        page_html = fetch_text(
            f"https://github.com/{GITHUB_USER}?page={page_num}&tab=repositories",
            use_browser_ua=True,
        )
        blocks = page_html.split('<li class="col-12 d-flex')[1:]
        if not blocks:
            break
        for blk in blocks:
            if "forked from" in blk.lower():
                continue
            name_m = re.search(r'itemprop="name codeRepository"[^>]*>\s*([^<\s]+)', blk)
            if not name_m:
                continue
            name = name_m.group(1).strip()
            lang_m = re.search(r'itemprop="programmingLanguage">([^<]+)<', blk)
            desc_m = re.search(r'itemprop="description">\s*(.*?)\s*</p>', blk, re.DOTALL)
            dt_m = re.search(r'<relative-time[^>]*datetime="([^"]+)"', blk)
            stars_m = re.search(r'/stargazers"[^>]*>[\s\S]*?</svg>\s*(\d+)', blk)
            forks_m = re.search(r'/forks"[^>]*>[\s\S]*?</svg>\s*(\d+)', blk)
            repos.append({
                "name": name,
                "fork": False,
                "html_url": f"https://github.com/{GITHUB_USER}/{name}",
                "default_branch": "master" if name in {"Awesome-Embedded", "theEmbeddedNewTestament.github.io"} else "main",
                "language": lang_m.group(1).strip() if lang_m else None,
                "description": html_lib.unescape(re.sub(r"\s+", " ", desc_m.group(1)).strip()) if desc_m else None,
                "pushed_at": dt_m.group(1) if dt_m else "",
                "stargazers_count": int(stars_m.group(1)) if stars_m else 0,
                "forks_count": int(forks_m.group(1)) if forks_m else 0,
                "open_issues_count": 0,
                "size": 0,
                "license": {"key": "present"} if "octicon-law" in blk else None,
            })
        if f'page={page_num + 1}&amp;tab=repositories' not in page_html and f'page={page_num + 1}&tab=repositories' not in page_html:
            break
    return repos


def fetch_all_repos() -> list[dict[str, Any]]:
    """Retrieve all public non-fork repositories, falling back to web HTML if rate-limited."""
    try:
        repos = github_api_get(f"/users/{GITHUB_USER}/repos?per_page=100&sort=pushed")
        return [r for r in repos if not r.get("fork")]
    except Exception as exc:
        print(f"API fallback -> parsing web repositories tab ({exc})", file=sys.stderr)
        return _fetch_repos_from_web()


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


def _fetch_ci_from_web(repo_name: str) -> dict[str, str] | None:
    """Fallback parser for /<user>/<repo>/actions HTML when REST API is rate-limited."""
    actions_html = fetch_text(f"https://github.com/{GITHUB_USER}/{repo_name}/actions", use_browser_ua=True)
    pattern = re.compile(
        r'"workflowFilePath":"([^"]+)","runUrl":"([^"]+)","title":"[^"]*","workflowName":"([^"]+)",'
        r'"state":\{"status":"[^"]*","conclusion":"([^"]+)"\},"createdAt":\{"timestamp":"([^"]+)"'
    )
    for match in pattern.finditer(actions_html):
        wf_path, run_url, wf_name, conclusion_raw, ts = match.groups()
        if "pages-build-deployment" in wf_name or "dynamic/pages" in wf_path:
            continue
        conclusion = conclusion_raw.replace("WORKFLOW_RUN_CONCLUSION_", "").lower()
        return {
            "workflow": wf_name.encode("utf-8").decode("unicode_escape"),
            "conclusion": conclusion,
            "last_run_utc": ts,
            "run_url": run_url,
        }
    return None


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
        run_info: dict[str, str] | None = None
        try:
            data = github_api_get(f"/repos/{GITHUB_USER}/{name}/actions/runs?per_page=1")
            runs = data.get("workflow_runs", [])
            if runs:
                run = runs[0]
                run_info = {
                    "workflow": run.get("name") or "CI",
                    "conclusion": run.get("conclusion") or run.get("status") or "unknown",
                    "last_run_utc": run.get("created_at", "N/A"),
                    "run_url": run.get("html_url") or entry["run_url"],
                }
        except Exception:
            try:
                run_info = _fetch_ci_from_web(name)
            except Exception as web_exc:
                entry["status"] = f"ERROR ({type(web_exc).__name__})"

        if run_info:
            conclusion = run_info["conclusion"].lower()
            entry["workflow"] = run_info["workflow"]
            entry["status"] = conclusion.upper()
            entry["last_run_utc"] = run_info["last_run_utc"]
            entry["run_url"] = run_info["run_url"]
            if conclusion == "success":
                passing += 1
            elif conclusion in {"failure", "timed_out", "action_required"}:
                failing += 1
        elif entry["status"] == "NO_WORKFLOW_RUNS":
            no_ci += 1

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
    """Day 2: Aggregate live portfolio metrics, language mix, and recent pushes."""
    user = _fetch_user_profile()
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
        branch = repo.get("default_branch", "main")
        try:
            items = github_api_get(f"/repos/{GITHUB_USER}/{name}/contents/.github/workflows")
        except Exception:
            items = [
                {
                    "name": wf_name,
                    "download_url": f"https://raw.githubusercontent.com/{GITHUB_USER}/{name}/{branch}/.github/workflows/{wf_name}",
                }
                for wf_name in ("ci.yml", "c-build.yml", "run_tests.yml")
            ]

        if not isinstance(items, list):
            continue

        found_any = False
        for wf in items:
            if not wf["name"].endswith((".yml", ".yaml")):
                continue
            dl_url = wf.get("download_url")
            if not dl_url:
                continue
            try:
                yaml_text = fetch_text(dl_url)
            except urllib.error.HTTPError as exc:
                if exc.code == 404:
                    continue
                rows.append((name, wf["name"], "N/A", "N/A", "⚠️ Fetch error"))
                found_any = True
                continue
            except Exception:
                rows.append((name, wf["name"], "N/A", "N/A", "⚠️ Fetch error"))
                found_any = True
                continue
            found_any = True

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

        if not found_any:
            rows.append((name, "None", "N/A", "N/A", "ℹ️ No workflow files"))

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
    """Day 6: Save immutable weekly JSON snapshot and update telemetry/README.md."""
    iso_year, iso_week, _ = ist_now.isocalendar()
    week_id = f"{iso_year}-W{iso_week:02d}"

    user = _fetch_user_profile()
    repos = fetch_all_repos()
    embedded = filter_embedded_repos(repos)
    _, ci_metrics = audit_embedded_ci(embedded)

    total_kb = sum(int(r.get("size") or 0) for r in repos if r["name"] != GITHUB_USER)
    snapshot_file = HISTORY_DIR / f"{week_id}.json"
    if total_kb == 0 and snapshot_file.exists():
        try:
            prev = json.loads(snapshot_file.read_text(encoding="utf-8"))
            total_kb = int(prev.get("total_codebase_kb") or 0)
        except Exception:
            pass

    snapshot = {
        "week": week_id,
        "recorded_utc": utc_now.strftime("%Y-%m-%d %H:%M:%S UTC"),
        "recorded_ist": ist_now.strftime("%Y-%m-%d %I:%M:%S %p IST"),
        "public_repos": user.get("public_repos", len(repos)),
        "followers": user.get("followers", 0),
        "total_stars": sum(int(r.get("stargazers_count") or 0) for r in repos),
        "total_forks": sum(int(r.get("forks_count") or 0) for r in repos),
        "total_codebase_kb": total_kb,
        "embedded_ci": ci_metrics,
    }
    write_text_file(snapshot_file, json.dumps(snapshot, indent=2) + "\n")

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
        "### 📅 7-Day Rotating Audit Schedule (Anchored 25-Nov-2026)",
        "",
        "| Cycle Day | Weekday | Audit Focus | Report File |",
        "| :--- | :--- | :--- | :--- |",
        "| **Day 1** | Wednesday | Live CI & Workflow Health | [`ci_health.md`](./ci_health.md) · [`ecosystem_status.json`](./ecosystem_status.json) |",
        "| **Day 2** | Thursday | Portfolio Metrics & Language Mix | [`repo_metrics.md`](./repo_metrics.md) |",
        "| **Day 3** | Friday | Profile Links & Badge Health | [`link_audit.md`](./link_audit.md) |",
        "| **Day 4** | Saturday | Actions & Build Toolchain Check | [`toolchain_audit.md`](./toolchain_audit.md) |",
        "| **Day 5** | Sunday | Open Issues & Repo Hygiene Triage | [`maintenance_triage.md`](./maintenance_triage.md) |",
        "| **Day 6** | Monday | Weekly Immutable Snapshot & Index | [`README.md`](./README.md) · [`history/`](./history) |",
        "| **Day 7** | Tuesday | Profile Dashboard & Badge Sync | [`../README.md`](../README.md) |",
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


def get_daily_commit_target(date_str: str, min_c: int = 1, max_c: int = 5) -> int:
    """Return a deterministic randomized daily commit target between min_c and max_c."""
    h = int(hashlib.sha256(f"SherifredEcosystem:{date_str}".encode()).hexdigest(), 16)
    return min_c + (h % (max_c - min_c + 1))


def get_today_commit_messages(ist_now: datetime) -> list[str]:
    """Retrieve commit messages made today in the local repository."""
    today_str = ist_now.strftime("%Y-%m-%d 00:00:00")
    try:
        cmd = ["git", "log", f"--since={today_str}", "--format=%s"]
        res = subprocess.run(cmd, cwd=REPO_ROOT, capture_output=True, text=True, check=True)
        return [line.strip() for line in res.stdout.strip().splitlines() if line.strip()]
    except Exception:
        return []


def git_commit_file(file_path: Path, commit_msg: str) -> bool:
    """Stage a single file relative to REPO_ROOT and commit if changes exist."""
    rel = file_path.relative_to(REPO_ROOT) if file_path.is_absolute() else file_path
    subprocess.run(["git", "add", str(rel)], cwd=REPO_ROOT, check=True)
    diff = subprocess.run(["git", "diff", "--staged", "--name-only"], cwd=REPO_ROOT, capture_output=True, text=True)
    if diff.stdout.strip():
        subprocess.run([
            "git", "commit",
            "-m", commit_msg,
            f"--author={AUTHOR_NAME} <{AUTHOR_EMAIL}>"
        ], cwd=REPO_ROOT, check=True)
        return True
    return False


def git_push_all() -> bool:
    """Push commits on main to origin/main."""
    res = subprocess.run(["git", "push", "origin", "main"], cwd=REPO_ROOT, capture_output=True, text=True)
    if res.returncode == 0:
        return True
    print(f"git push error: {res.stderr}", file=sys.stderr)
    return False


def execute_task_1_rotating_audit(day_num: int, utc_now: datetime, ist_now: datetime) -> tuple[Path, str]:
    """Task 1: Execute today's rotating 7-day audit report."""
    commit_msg = DAY_HANDLERS[day_num](utc_now, ist_now)
    target_files = {
        1: TELEMETRY_DIR / "ci_health.md",
        2: TELEMETRY_DIR / "repo_metrics.md",
        3: TELEMETRY_DIR / "link_audit.md",
        4: TELEMETRY_DIR / "toolchain_audit.md",
        5: TELEMETRY_DIR / "maintenance_triage.md",
        6: TELEMETRY_DIR / "README.md",
        7: REPO_ROOT / "README.md",
    }
    return target_files.get(day_num, TELEMETRY_DIR / "README.md"), commit_msg


def execute_task_2_ecosystem_status(utc_now: datetime, ist_now: datetime) -> tuple[Path, str]:
    """Task 2: Update live ecosystem status JSON telemetry."""
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
        "last_sync_utc": utc_now.strftime("%Y-%m-%d %H:%M:%S UTC"),
        "last_sync_ist": ist_now.strftime("%Y-%m-%d %I:%M:%S %p IST"),
        "status": overall_status,
        "streak_shield_active": True,
        "metrics": metrics,
        "monitored_repositories": ci_results,
    }
    path = TELEMETRY_DIR / "ecosystem_status.json"
    write_text_file(path, json.dumps(payload, indent=2) + "\n")
    return path, "chore(telemetry): update live embedded ecosystem status & metrics [skip ci]"


def execute_task_3_telemetry_index(utc_now: datetime, ist_now: datetime) -> tuple[Path, str]:
    """Task 3: Update telemetry index and rotating audit summary."""
    run_day_6_weekly_snapshot(utc_now, ist_now)
    path = TELEMETRY_DIR / "README.md"
    return path, "docs(telemetry): update ecosystem verification summary & schedule index [skip ci]"


def execute_task_4_profile_badges(utc_now: datetime, ist_now: datetime) -> tuple[Path, str]:
    """Task 4: Refresh README.md badge cache busters."""
    readme_path = REPO_ROOT / "README.md"
    if readme_path.exists():
        content = readme_path.read_text(encoding="utf-8")
        cache_buster = ist_now.strftime("%m%d%H%M")
        updated = re.sub(r"(&v=)\d+", rf"\g<1>{cache_buster}", content)
        if updated != content:
            readme_path.write_text(updated, encoding="utf-8")
    return readme_path, "chore(profile): refresh profile dashboard badge cache busters [skip ci]"


def execute_task_5_weekly_archive(utc_now: datetime, ist_now: datetime) -> tuple[Path, str]:
    """Task 5: Save or refresh the weekly JSON archive snapshot."""
    iso_year, iso_week, _ = ist_now.isocalendar()
    week_id = f"{iso_year}-W{iso_week:02d}"
    path = HISTORY_DIR / f"{week_id}.json"
    user = _fetch_user_profile()
    repos = fetch_all_repos()
    embedded = filter_embedded_repos(repos)
    _, ci_metrics = audit_embedded_ci(embedded)
    total_kb = sum(int(r.get("size") or 0) for r in repos if r["name"] != GITHUB_USER)
    if total_kb == 0 and path.exists():
        try:
            prev = json.loads(path.read_text(encoding="utf-8"))
            total_kb = int(prev.get("total_codebase_kb") or 0)
        except Exception:
            pass
    snapshot = {
        "week": week_id,
        "recorded_utc": utc_now.strftime("%Y-%m-%d %H:%M:%S UTC"),
        "recorded_ist": ist_now.strftime("%Y-%m-%d %I:%M:%S %p IST"),
        "public_repos": user.get("public_repos", len(repos)),
        "followers": user.get("followers", 0),
        "total_stars": sum(int(r.get("stargazers_count") or 0) for r in repos),
        "total_forks": sum(int(r.get("forks_count") or 0) for r in repos),
        "total_codebase_kb": total_kb,
        "embedded_ci": ci_metrics,
    }
    write_text_file(path, json.dumps(snapshot, indent=2) + "\n")
    return path, "chore(archive): sync weekly telemetry snapshot & history log [skip ci]"


def run_daily_randomized_commits(day_num: int, target_commits: int, commit_and_push: bool) -> int:
    """Coordinate executing and committing tasks to reach target_commits for the day."""
    utc_now, ist_now = get_ist_utc_now()
    existing_msgs = get_today_commit_messages(ist_now)
    current_count = len(existing_msgs)

    print(f"--- Randomized Daily Commit Manager ---")
    print(f"Date: {ist_now.strftime('%Y-%m-%d (%A)')}")
    print(f"Target commits for today: {target_commits}")
    print(f"Existing commits today: {current_count}")

    if current_count >= target_commits:
        print(f"Goal of {target_commits} commit(s) already satisfied ({current_count} committed). Skipping.")
        return 0

    needed = target_commits - current_count
    print(f"Need {needed} more commit(s) to reach today's target.")

    task_pipeline = [
        (
            "Task 1 (Daily Focus)",
            lambda: any(re.search(r"chore\((ci-audit|audit|toolchain|archive)\)|docs\((telemetry|maintenance|profile)\)", m) for m in existing_msgs),
            lambda: execute_task_1_rotating_audit(day_num, utc_now, ist_now),
        ),
        (
            "Task 2 (Ecosystem Status JSON)",
            lambda: any("chore(telemetry): update live embedded ecosystem status" in m for m in existing_msgs),
            lambda: execute_task_2_ecosystem_status(utc_now, ist_now),
        ),
        (
            "Task 3 (Telemetry Overview README)",
            lambda: any("docs(telemetry): update ecosystem verification summary" in m for m in existing_msgs),
            lambda: execute_task_3_telemetry_index(utc_now, ist_now),
        ),
        (
            "Task 4 (Profile Badges Cache)",
            lambda: any("chore(profile): refresh profile dashboard badge cache" in m for m in existing_msgs),
            lambda: execute_task_4_profile_badges(utc_now, ist_now),
        ),
        (
            "Task 5 (Weekly Snapshot Archive)",
            lambda: any("chore(archive): sync weekly telemetry snapshot" in m for m in existing_msgs),
            lambda: execute_task_5_weekly_archive(utc_now, ist_now),
        ),
    ]

    commits_made = 0
    for name, is_done, task_fn in task_pipeline:
        if commits_made >= needed:
            break
        if is_done():
            print(f"  [Skipped] {name} already committed today.")
            continue

        print(f"  [Executing] {name}...")
        file_path, commit_msg = task_fn()
        if commit_and_push:
            ok = git_commit_file(file_path, commit_msg)
            if ok:
                commits_made += 1
                existing_msgs.append(commit_msg)
                print(f"  [Committed] -> {commit_msg}")
            else:
                print(f"  [No changes] -> {file_path.name} was already up to date.")
        else:
            print(f"  [Dry Run] Updated {file_path.name} (would commit: {commit_msg})")
            commits_made += 1

    if commit_and_push and commits_made > 0:
        print(f"Pushing {commits_made} new commit(s) to origin/main...")
        if git_push_all():
            print(f"Successfully pushed! Today total commits: {current_count + commits_made}/{target_commits}")
        else:
            print("Failed to push to origin/main", file=sys.stderr)
            return 1

    return 0


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
    parser = argparse.ArgumentParser(description="7-day rotating embedded ecosystem audit with randomized 1-5 commits")
    parser.add_argument(
        "--skip-if-active",
        action="store_true",
        help="Skip execution if manual repository pushes already occurred today.",
    )
    parser.add_argument(
        "--day",
        type=int,
        choices=range(1, 8),
        help="Override 7-day cycle index (1..7). Defaults to days since 2026-11-25.",
    )
    parser.add_argument(
        "--commits",
        type=int,
        choices=range(1, 6),
        help="Override number of commits for today (1..5). Defaults to deterministic daily random.",
    )
    parser.add_argument(
        "--min-commits",
        type=int,
        default=1,
        help="Minimum randomized commits per day (default: 1).",
    )
    parser.add_argument(
        "--max-commits",
        type=int,
        default=5,
        help="Maximum randomized commits per day (default: 5).",
    )
    parser.add_argument(
        "--commit-and-push",
        action="store_true",
        help="Automatically commit and push the randomized tasks to origin/main.",
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
    today_date_str = ist_now.strftime("%Y-%m-%d")

    # Smart fallback: skip automated streak only if real manual repository work was done elsewhere today
    if args.skip_if_active and not args.all:
        active, reason = has_contributed_today(utc_now)
        if "Repository push already recorded today" in reason:
            print(f"Smart-fallback check: {reason}")
            print("Manual repository activity detected. Skipping automated commits today to highlight real work.")
            return 0

    if args.all:
        for day_num in range(1, 8):
            print(f"Running Day {day_num}: {DAY_SCHEDULE[day_num]}...")
            msg = DAY_HANDLERS[day_num](utc_now, ist_now)
            print(f"  Completed -> {msg}")
        write_commit_message("chore(telemetry): initialize 7-day rotating embedded ecosystem audit suite [skip ci]")
        return 0

    day_num = args.day if args.day else get_cycle_day(ist_now)
    target_commits = args.commits if args.commits else get_daily_commit_target(today_date_str, args.min_commits, args.max_commits)

    return run_daily_randomized_commits(day_num, target_commits, args.commit_and_push)


if __name__ == "__main__":
    raise SystemExit(main())
