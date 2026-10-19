# ==============================================================================
# Daily GitHub Streak Keeper & Ecosystem Telemetry Automation
# Engineer: Sherifred Singh <ssherifred@gmail.com>
# Purpose: Auto-sync telemetry, bump README cache busters, and push to GitHub
#          Runs daily at 09:00 AM IST via Windows Task Scheduler.
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
    Write-Log "Starting Daily Streak Keeper execution..."

    if (-not (Test-Path $RepoDir)) {
        Write-Log "ERROR: Repository path not found: $RepoDir"
        exit 1
    }

    Set-Location -Path $RepoDir

    # Check git executable
    if (-not (Get-Command git -ErrorAction SilentlyContinue)) {
        Write-Log "ERROR: 'git' is not in PATH."
        exit 1
    }

    # 1. Pull latest to avoid merge collisions
    Write-Log "Pulling origin/main..."
    & git pull --rebase origin main 2>&1 | ForEach-Object { Write-Log "  $_" }

    # 2. Run telemetry and badge update script
    Write-Log "Running scripts/update_telemetry.py..."
    & python scripts\update_telemetry.py 2>&1 | ForEach-Object { Write-Log "  $_" }

    # 3. Stage telemetry and README changes
    & git add telemetry/ README.md

    # 4. Check if there are changes to commit
    $staged = & git diff --staged --name-only
    if ($staged) {
        $todayStr = (Get-Date).ToString("MMM dd")
        $commitMessage = "chore(telemetry): daily embedded ecosystem health check & streak keeper for $todayStr [skip ci]"
        Write-Log "Staged changes in: $($staged -join ', ')"
        Write-Log "Committing: $commitMessage"

        & git commit -m "$commitMessage" --author="Sherifred singh <ssherifred@gmail.com>" 2>&1 | ForEach-Object { Write-Log "  $_" }
        & git push origin main 2>&1 | ForEach-Object { Write-Log "  $_" }

        Write-Log "SUCCESS: Streak and telemetry successfully pushed to GitHub!"
    } else {
        Write-Log "INFO: Telemetry and streak are already up to date for today. No push needed."
    }
}
catch {
    Write-Log "ERROR: Exception caught: $($_.Exception.Message)"
}
finally {
    Write-Log "Daily Streak Keeper finished."
}
