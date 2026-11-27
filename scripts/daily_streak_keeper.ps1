# ==============================================================================
# 7-Day Rotating GitHub Ecosystem Audit & Randomized Streak Keeper (1-5 Commits)
# Engineer: Sherifred Singh <ssherifred@gmail.com>
# Purpose: Runs today's rotating audit with randomized 1-5 commits per day,
#          skipping only if real manual repository work was already pushed today.
# ==============================================================================

$RepoDir = "E:\EMBEDDED FILE\LEARNING SOURCE\PRE\ANTIGRAVITY\NOTES\GITHUB_PORTFOLIO_PROJECTS\Sherifred123"
$LogFile = "$RepoDir\scripts\streak_keeper_runner.log"

function Write-Log {
    param([string]$Message)
    $Timestamp = (Get-Date).ToString("yyyy-MM-dd HH:mm:ss")
    $Entry = "[$Timestamp] $Message"
    Write-Output $Entry
    Add-Content -Path $LogFile -Value $Entry -Encoding utf8
}

try {
    Write-Log "----------------------------------------------------"
    Write-Log "Starting 7-Day Randomized Ecosystem Audit (1-5 Commits)..."

    if (-not (Test-Path $RepoDir)) {
        Write-Log "ERROR: Repository path not found: $RepoDir"
        exit 1
    }

    Set-Location -Path $RepoDir

    if (-not (Get-Command git -ErrorAction SilentlyContinue)) {
        Write-Log "ERROR: 'git' is not in PATH."
        exit 1
    }

    # 1. Pull latest to avoid merge collisions
    Write-Log "Pulling origin/main..."
    & git pull --rebase origin main 2>&1 | ForEach-Object { Write-Log "  $_" }

    # 2. Run randomized multi-commit manager
    Write-Log "Running scripts/update_telemetry.py --skip-if-active --commit-and-push..."
    & python scripts\update_telemetry.py --skip-if-active --commit-and-push 2>&1 | ForEach-Object { Write-Log "  $_" }

    Write-Log "SUCCESS: Daily audit manager finished successfully."
}
catch {
    Write-Log "ERROR: Exception caught: $($_.Exception.Message)"
}
finally {
    Write-Log "Randomized Ecosystem Audit completed."
}
