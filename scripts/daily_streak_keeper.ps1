# ==============================================================================
# 7-Day Rotating GitHub Ecosystem Audit & Smart Streak Keeper
# Engineer: Sherifred Singh <ssherifred@gmail.com>
# Purpose: Runs today's rotating engineering audit (Mon-Sun) only if no manual
#          GitHub contribution is recorded yet today, preventing duplicate commits.
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
    Write-Log "Starting 7-Day Smart Ecosystem Audit..."

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

    # 2. Clear previous commit message file and run smart-fallback audit
    $MsgFile = "$RepoDir\.git\TELEMETRY_COMMIT_MSG"
    if (Test-Path $MsgFile) { Remove-Item $MsgFile -Force }

    Write-Log "Running scripts/update_telemetry.py --skip-if-active..."
    & python scripts\update_telemetry.py --skip-if-active 2>&1 | ForEach-Object { Write-Log "  $_" }

    # 3. Stage telemetry and README changes
    & git add telemetry/ README.md

    # 4. Commit only if staged changes exist
    $staged = & git diff --staged --name-only
    if ($staged) {
        if (Test-Path $MsgFile) {
            $commitMessage = (Get-Content $MsgFile -Raw).Trim()
        } else {
            $todayStr = (Get-Date).ToString("MMM dd")
            $commitMessage = "chore(telemetry): embedded ecosystem audit for $todayStr [skip ci]"
        }
        Write-Log "Staged changes in: $($staged -join ', ')"
        Write-Log "Committing: $commitMessage"

        & git commit -m "$commitMessage" --author="Sherifred singh <ssherifred@gmail.com>" 2>&1 | ForEach-Object { Write-Log "  $_" }
        & git push origin main 2>&1 | ForEach-Object { Write-Log "  $_" }

        Write-Log "SUCCESS: Ecosystem audit successfully pushed to GitHub!"
    } else {
        Write-Log "INFO: Contribution already active today or no report delta. Skipping push."
    }
}
catch {
    Write-Log "ERROR: Exception caught: $($_.Exception.Message)"
}
finally {
    Write-Log "Smart Ecosystem Audit finished."
}
