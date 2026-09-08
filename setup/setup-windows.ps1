<#
.SYNOPSIS
    התקנת סביבת עבודה ל-Claude Code על Windows.

.DESCRIPTION
    מתקין (רק אם חסר): Node.js LTS, Python 3.12, Git, FFmpeg (אופציונלי), Claude Code.
    הסקריפט אידמפוטנטי - אפשר להריץ אותו שוב ושוב בלי נזק.

.PARAMETER SkipFFmpeg
    דילוג על התקנת FFmpeg (לא נדרש ל-Claude Code עצמו).

.PARAMETER SkipClaude
    דילוג על התקנת Claude Code (רק הכלים הבסיסיים).

.EXAMPLE
    powershell -ExecutionPolicy Bypass -File .\setup\setup-windows.ps1

.EXAMPLE
    powershell -ExecutionPolicy Bypass -File .\setup\setup-windows.ps1 -SkipFFmpeg
#>
[CmdletBinding()]
param(
    [switch]$SkipFFmpeg,
    [switch]$SkipClaude
)

$ErrorActionPreference = 'Stop'
$script:Failures = @()

function Write-Step([string]$Text)  { Write-Host "`n==> $Text" -ForegroundColor Cyan }
function Write-Ok([string]$Text)    { Write-Host "    [OK]   $Text" -ForegroundColor Green }
function Write-Skip([string]$Text)  { Write-Host "    [SKIP] $Text" -ForegroundColor DarkGray }
function Write-Fail([string]$Text)  { Write-Host "    [FAIL] $Text" -ForegroundColor Red; $script:Failures += $Text }

function Refresh-Path {
    # מרענן את PATH של התהליך הנוכחי אחרי התקנות, כדי שכלים חדשים יזוהו בלי לפתוח חלון חדש.
    $machine = [Environment]::GetEnvironmentVariable('Path', 'Machine')
    $user    = [Environment]::GetEnvironmentVariable('Path', 'User')
    $env:Path = "$machine;$user"
}

function Test-Command([string]$Name) {
    return [bool](Get-Command $Name -ErrorAction SilentlyContinue)
}

function Install-WingetPackage {
    param(
        [Parameter(Mandatory)] [string]$Id,
        [Parameter(Mandatory)] [string]$DisplayName,
        [Parameter(Mandatory)] [string]$Command
    )
    Write-Step "$DisplayName"
    if (Test-Command $Command) {
        $ver = & $Command --version 2>$null | Select-Object -First 1
        Write-Skip "כבר מותקן ($ver)"
        return
    }
    Write-Host "    מתקין דרך winget: $Id"
    & winget install -e --id $Id --accept-package-agreements --accept-source-agreements --silent
    if ($LASTEXITCODE -ne 0) {
        Write-Fail "$DisplayName - winget החזיר קוד שגיאה $LASTEXITCODE"
        return
    }
    Refresh-Path
    if (Test-Command $Command) {
        $ver = & $Command --version 2>$null | Select-Object -First 1
        Write-Ok "הותקן ($ver)"
    } else {
        Write-Fail "$DisplayName הותקן אבל '$Command' לא נמצא ב-PATH. סגור ופתח מחדש את הטרמינל והרץ שוב."
    }
}

# ---------------------------------------------------------------------------
Write-Host "התקנת סביבת עבודה ל-Claude Code" -ForegroundColor Yellow
Write-Host "-----------------------------------"

Write-Step "בדיקות מקדימות"
if (-not (Test-Command 'winget')) {
    Write-Fail "winget לא נמצא. התקן 'App Installer' מ-Microsoft Store ואז הרץ שוב."
    exit 1
}
Write-Ok "winget זמין"

$isAdmin = ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
if ($isAdmin) { Write-Ok "רץ כמנהל" } else { Write-Host "    [INFO] לא רץ כמנהל - ייתכנו חלונות אישור (UAC) במהלך ההתקנה." -ForegroundColor DarkYellow }

# ---------------------------------------------------------------------------
Install-WingetPackage -Id 'Git.Git'            -DisplayName 'Git'          -Command 'git'
Install-WingetPackage -Id 'OpenJS.NodeJS.LTS'  -DisplayName 'Node.js LTS'  -Command 'node'
Install-WingetPackage -Id 'Python.Python.3.12' -DisplayName 'Python 3.12'  -Command 'python'

if ($SkipFFmpeg) {
    Write-Step "FFmpeg"; Write-Skip "דולג לפי בקשה (-SkipFFmpeg)"
} else {
    Install-WingetPackage -Id 'Gyan.FFmpeg' -DisplayName 'FFmpeg' -Command 'ffmpeg'
}

# ---------------------------------------------------------------------------
# Python - חבילות בסיס לעבודה עם מסמכים (הסקילים של docx / pdf / xlsx משתמשים בהן).
Write-Step "חבילות Python למסמכים"
if (Test-Command 'python') {
    $pyVer = & python --version 2>&1
    if ($pyVer -match 'Microsoft Store') {
        Write-Fail "'python' מפנה ל-Microsoft Store ולא ל-Python האמיתי. כבה את 'App execution aliases' עבור python ב-Settings > Apps > Advanced app settings."
    } else {
        & python -m pip install --quiet --upgrade pip
        & python -m pip install --quiet python-docx openpyxl pypdf
        if ($LASTEXITCODE -eq 0) { Write-Ok "python-docx, openpyxl, pypdf" } else { Write-Fail "pip install נכשל" }
    }
} else {
    Write-Skip "Python לא זמין - מדלג"
}

# ---------------------------------------------------------------------------
if ($SkipClaude) {
    Write-Step "Claude Code"; Write-Skip "דולג לפי בקשה (-SkipClaude)"
} else {
    Write-Step "Claude Code"
    if (Test-Command 'claude') {
        $ver = & claude --version 2>$null | Select-Object -First 1
        Write-Skip "כבר מותקן ($ver)"
    } else {
        $installed = $false
        # דרך 1: המתקין הרשמי (מומלץ, לא תלוי ב-Node).
        try {
            Write-Host "    מתקין דרך המתקין הרשמי..."
            Invoke-Expression (Invoke-RestMethod -Uri 'https://claude.ai/install.ps1')
            Refresh-Path
            $installed = Test-Command 'claude'
        } catch {
            Write-Host "    המתקין הרשמי נכשל: $($_.Exception.Message)" -ForegroundColor DarkYellow
        }
        # דרך 2: npm (גיבוי).
        if (-not $installed -and (Test-Command 'npm')) {
            Write-Host "    מנסה דרך npm..."
            & npm install -g @anthropic-ai/claude-code
            Refresh-Path
            $installed = Test-Command 'claude'
        }
        if ($installed) {
            $ver = & claude --version 2>$null | Select-Object -First 1
            Write-Ok "הותקן ($ver)"
        } else {
            Write-Fail "Claude Code לא הותקן. נסה ידנית: npm install -g @anthropic-ai/claude-code"
        }
    }
}

# ---------------------------------------------------------------------------
Write-Step "סיכום גרסאות"
foreach ($tool in @('git', 'node', 'npm', 'python', 'ffmpeg', 'claude')) {
    if (Test-Command $tool) {
        $ver = (& $tool --version 2>&1 | Select-Object -First 1) -replace 'ffmpeg version (\S+).*', '$1'
        Write-Host ("    {0,-8} {1}" -f $tool, $ver)
    } else {
        Write-Host ("    {0,-8} לא נמצא" -f $tool) -ForegroundColor DarkGray
    }
}

Write-Host ""
if ($script:Failures.Count -eq 0) {
    Write-Host "הכל מוכן. השלב הבא:" -ForegroundColor Green
    Write-Host "    1. סגור ופתח מחדש את הטרמינל (כדי ש-PATH יתעדכן)."
    Write-Host "    2. הרץ:  claude"
    Write-Host "    3. בהפעלה הראשונה, התחבר לחשבון Anthropic דרך הדפדפן."
} else {
    Write-Host "הסתיים עם $($script:Failures.Count) בעיות:" -ForegroundColor Red
    $script:Failures | ForEach-Object { Write-Host "    - $_" -ForegroundColor Red }
    exit 1
}
