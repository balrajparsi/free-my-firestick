<#
.SYNOPSIS
  Free up space on an Amazon Fire TV Stick and tidy it up, over ADB from your PC.

.DESCRIPTION
  A menu-driven tool. Nothing happens without you choosing it, and every removal asks first.
    1. Storage report      - free space and the biggest apps (app + data + cache)
    2. Clear all caches    - frees cache space for every app (no logins or settings lost)
    3. Remove apps         - pick apps YOU installed to uninstall
    4. Turn off extras     - turn off optional Amazon ads/telemetry apps (reversible)
    5. Restore extras      - turn back on everything option 4 turned off
  Never touches: the Amazon home screen, Settings, Wi-Fi, keyboard, inputs, or system updates.

.EXAMPLE
  .\FireStickCleanup.ps1 -Ip 192.168.1.50
  Older Fire OS ("ADB debugging" switch): connects on port 5555.

.EXAMPLE
  .\FireStickCleanup.ps1 -Ip 192.168.1.50 -Port 41235 -PairPort 37099
  Newer Fire OS ("Wireless debugging"): -Port is the port under "IP address & port", -PairPort the one shown
  after "Pair device with pairing code". The script asks for the 6-digit code. Pairing is needed only once.
#>
param(
    [Parameter(Mandatory = $true)][string]$Ip,
    [int]$Port = 5555,
    [int]$PairPort = 0
)

$ErrorActionPreference = 'Stop'
$Target = "${Ip}:$Port"
$LogFile = Join-Path $PSScriptRoot "firestick-turned-off.json"

# Optional Amazon extras. Each is only touched if it exists on your Fire Stick.
$Extras = [ordered]@{
    'com.amazon.kso'                  = 'Special Offers ad service (sponsored banners / screensaver ads)'
    'com.amazon.device.sale.service'  = 'Deals and promotions service'
    'com.amazon.hedwig'               = 'Amazon promo push notifications'
    'com.amazon.client.metrics'       = 'Usage metrics upload (telemetry)'
    'com.amazon.device.crashmanager'  = 'Crash report upload (telemetry)'
    'com.amazon.bueller.photos'       = 'Amazon Photos app'
    'com.amazon.ags.app'              = 'Amazon GameCircle (old games service)'
    'com.amazon.awvflingreceiver'     = 'Fling video from phone (rarely used)'
}

# Never offered for removal, whatever the user picks.
$Protected = @(
    'com.amazon.tv.launcher', 'com.amazon.tv.settings', 'com.amazon.tv.settings.v2',
    'com.amazon.device.software.ota', 'com.amazon.tv.forcedotaupdater.v2',
    'com.amazon.wifilocker', 'com.amazon.tv.ime', 'com.amazon.tv.inputpreference.service',
    'com.amazon.device.messaging', 'com.android.settings', 'com.android.systemui'
)

function Write-Title($text) { Write-Host ""; Write-Host "== $text ==" -ForegroundColor Cyan }

function Invoke-Adb {
    param([Parameter(ValueFromRemainingArguments = $true)][string[]]$AdbArgs)
    $out = & adb -s $Target @AdbArgs 2>&1
    return ($out | Out-String).Trim()
}

function Sh([string]$cmd) { Invoke-Adb shell $cmd }

function Format-Size([double]$bytes) {
    if ($bytes -ge 1GB) { return "{0:N2} GB" -f ($bytes / 1GB) }
    if ($bytes -ge 1MB) { return "{0:N0} MB" -f ($bytes / 1MB) }
    return "{0:N0} KB" -f ($bytes / 1KB)
}

function Confirm-Yes([string]$question) {
    $a = Read-Host "$question [y/N]"
    return ($a -match '^(y|yes)$')
}

function Connect-FireStick {
    if (-not (Get-Command adb -ErrorAction SilentlyContinue)) {
        Write-Host "adb was not found. Install it with:  winget install Google.PlatformTools" -ForegroundColor Red
        Write-Host "then close and reopen PowerShell." -ForegroundColor Red
        exit 1
    }
    if ($PairPort -gt 0) {
        $code = Read-Host "Pairing code shown on the TV"
        $pair = (& adb pair "${Ip}:$PairPort" $code 2>&1 | Out-String).Trim()
        Write-Host $pair
        if ($pair -notmatch 'Successfully paired') {
            Write-Host "Pairing failed. Open 'Pair device with pairing code' again on the TV and use the new port and code." -ForegroundColor Red
            exit 1
        }
    }
    Write-Host "Connecting to $Target ... (if the TV asks to allow debugging, tick 'Always allow' and choose Allow)"
    & adb connect $Target | Out-Null
    for ($i = 0; $i -lt 15; $i++) {
        $state = (& adb -s $Target get-state 2>&1 | Out-String).Trim()
        if ($state -eq 'device') { break }
        Start-Sleep -Seconds 2
    }
    if ($state -ne 'device') {
        Write-Host "Could not connect ($state). Check the IP, that ADB debugging is ON, and accept the prompt on the TV." -ForegroundColor Red
        exit 1
    }
    $model = Sh "getprop ro.product.model"
    $fireos = Sh "getprop ro.build.version.name"
    Write-Host "Connected: $model  ($fireos)" -ForegroundColor Green
}

function Get-FreeSpace {
    # df -k /data -> Filesystem 1K-blocks Used Available Use% Mounted (read from the end: long names can wrap)
    $f = ((Sh "df -k /data") -split '\s+') | Where-Object { $_ }
    $n = $f.Count
    return [pscustomobject]@{ Total = [double]$f[$n - 5] * 1KB; Used = [double]$f[$n - 4] * 1KB; Free = [double]$f[$n - 3] * 1KB }
}

function Show-Space([string]$label) {
    $s = Get-FreeSpace
    Write-Host ("{0}: {1} free of {2} ({3:N0}% used)" -f $label, (Format-Size $s.Free), (Format-Size $s.Total), (100 * $s.Used / $s.Total))
    return $s
}

function Get-UserApps {
    # Skip Amazon's resource overlays (e.g. ...settings.v2.overlay.localisation.common): listed as user apps on
    # Fire OS 8, but they hold system menu text, not anything you installed.
    (Sh "pm list packages -3") -split "`n" | ForEach-Object { $_.Trim() -replace '^package:', '' } |
        Where-Object { $_ -and $_ -notmatch '\.overlay\.' } | Sort-Object
}

function Get-AppSizes {
    # dumpsys diskstats lists every package with its app, data and cache sizes (refreshed by Fire OS now and then).
    $raw = Sh "dumpsys diskstats"
    $get = {
        param($name)
        $m = [regex]::Match($raw, "$name\s*:\s*(\[.*?\])", 'Singleline')
        if ($m.Success) { return ,($m.Groups[1].Value | ConvertFrom-Json) } else { return ,@() }
    }
    $names = & $get 'Package Names'; $app = & $get 'App Sizes'; $data = & $get 'App Data Sizes'; $cache = & $get 'Cache Sizes'
    $list = for ($i = 0; $i -lt $names.Count; $i++) {
        [pscustomobject]@{
            Package = $names[$i]
            App     = [double]$app[$i]
            Data    = [double]$data[$i]
            Cache   = [double]$cache[$i]
            Total   = [double]$app[$i] + [double]$data[$i] + [double]$cache[$i]
        }
    }
    return $list
}

function Show-Report {
    Write-Title "Storage report"
    Show-Space "Internal storage" | Out-Null
    $user = Get-UserApps
    $sizes = Get-AppSizes
    if (-not $sizes) { Write-Host "This Fire OS version doesn't report app sizes; showing the app list only."; $user | ForEach-Object { "  $_" }; return }
    Write-Host ""
    Write-Host "Biggest 20 apps (* = installed by you, can be removed with option 3):"
    $sizes | Sort-Object Total -Descending | Select-Object -First 20 | ForEach-Object {
        $mark = if ($user -contains $_.Package) { '*' } else { ' ' }
        Write-Host ("  {0} {1,-48} {2,9}  (cache {3})" -f $mark, $_.Package, (Format-Size $_.Total), (Format-Size $_.Cache))
    }
    $cacheTotal = ($sizes | Measure-Object Cache -Sum).Sum
    Write-Host ""
    Write-Host ("Cache across all apps: about {0} (option 2 clears it)." -f (Format-Size $cacheTotal))
}

function Clear-Caches {
    Write-Title "Clear all app caches"
    Write-Host "This deletes only temporary cache files. Apps stay signed in and keep their settings."
    if (-not (Confirm-Yes "Clear caches now?")) { return }
    $before = Get-FreeSpace
    # Asking Android to keep a huge amount free makes it delete every app's cache.
    Write-Host (Sh "pm trim-caches 999G")
    Start-Sleep -Seconds 2
    $after = Get-FreeSpace
    Write-Host ("Freed {0}. Now {1} free." -f (Format-Size ([math]::Max(0, $after.Free - $before.Free))), (Format-Size $after.Free)) -ForegroundColor Green
}

function Remove-UserApps {
    Write-Title "Remove apps you installed"
    $user = @(Get-UserApps | Where-Object { $Protected -notcontains $_ })
    if (-not $user) { Write-Host "No removable apps found."; return }
    $sizes = Get-AppSizes
    for ($i = 0; $i -lt $user.Count; $i++) {
        $s = $sizes | Where-Object Package -eq $user[$i] | Select-Object -First 1
        $size = if ($s) { Format-Size $s.Total } else { '' }
        Write-Host ("  [{0,2}] {1,-48} {2}" -f ($i + 1), $user[$i], $size)
    }
    $pick = Read-Host "Numbers to remove, separated by commas (e.g. 2,5,7), or Enter to cancel"
    if (-not $pick) { return }
    $before = Get-FreeSpace
    foreach ($n in ($pick -split ',' | ForEach-Object { $_.Trim() } | Where-Object { $_ -match '^\d+$' })) {
        $idx = [int]$n - 1
        if ($idx -lt 0 -or $idx -ge $user.Count) { Write-Host "  skip $n (not in the list)"; continue }
        $pkg = $user[$idx]
        if (Confirm-Yes "  Uninstall $pkg ? Its data and logins are deleted.") {
            Write-Host ("  {0}: {1}" -f $pkg, (Invoke-Adb uninstall $pkg))
        }
    }
    $after = Get-FreeSpace
    Write-Host ("Freed {0}. Now {1} free." -f (Format-Size ([math]::Max(0, $after.Free - $before.Free))), (Format-Size $after.Free)) -ForegroundColor Green
}

function Read-Log {
    if (Test-Path $LogFile) { return @(Get-Content $LogFile -Raw | ConvertFrom-Json) }
    return @()
}

function Save-Log($entries) { $entries | ConvertTo-Json -Depth 3 | Set-Content -Path $LogFile -Encoding UTF8 }

function Disable-Extras {
    Write-Title "Turn off optional Amazon extras"
    Write-Host "These are turned off for your profile only, not deleted. Option 5 brings them all back."
    Write-Host "The record of what was turned off is saved next to this script: $LogFile"
    $installed = (Sh "pm list packages") -split "`n" | ForEach-Object { $_.Trim() -replace '^package:', '' }
    $disabled = (Sh "pm list packages -d") -split "`n" | ForEach-Object { $_.Trim() -replace '^package:', '' }
    $log = [System.Collections.ArrayList]@(Read-Log)
    $found = $false
    foreach ($pkg in $Extras.Keys) {
        if ($installed -notcontains $pkg -or $disabled -contains $pkg) { continue }
        $found = $true
        if (-not (Confirm-Yes ("  Turn off {0}  ({1})?" -f $pkg, $Extras[$pkg]))) { continue }
        $r = Sh "pm disable-user --user 0 $pkg"
        $method = 'disable'
        if ($r -notmatch 'new state: disabled') {
            # Newer Fire OS refuses disable-user for Amazon apps; removing for user 0 is the reversible alternative.
            Write-Host "    Fire OS refused to turn it off ($r)."
            if (-not (Confirm-Yes "    Remove it for your profile instead? (reversible with option 5)")) { continue }
            $r = Sh "pm uninstall -k --user 0 $pkg"
            $method = 'uninstall-user'
            if ($r -notmatch 'Success') { Write-Host "    Not possible on this Fire Stick: $r" -ForegroundColor Yellow; continue }
        }
        [void]$log.Add([pscustomobject]@{ Package = $pkg; Method = $method; When = (Get-Date).ToString('s') })
        Save-Log $log
        Write-Host "    Done." -ForegroundColor Green
    }
    if (-not $found) { Write-Host "Nothing to do: none of the extras are on, or this Fire Stick doesn't have them." }
}

function Restore-Extras {
    Write-Title "Restore Amazon extras"
    $log = Read-Log
    if (-not $log) { Write-Host "Nothing recorded in $LogFile, so nothing to restore."; return }
    foreach ($e in $log) {
        if ($e.Method -eq 'uninstall-user') { $r = Sh "cmd package install-existing $($e.Package)" }
        else { $r = Sh "pm enable $($e.Package)" }
        Write-Host ("  {0}: {1}" -f $e.Package, $r)
    }
    Remove-Item $LogFile
    Write-Host "All restored. Restart the Fire Stick (Settings > My Fire TV > Restart) to be safe." -ForegroundColor Green
}

# ---- main ----
Connect-FireStick
Show-Space "Internal storage" | Out-Null
while ($true) {
    Write-Title "Fire Stick cleanup"
    Write-Host "  1) Storage report"
    Write-Host "  2) Clear all app caches"
    Write-Host "  3) Remove apps you installed"
    Write-Host "  4) Turn off optional Amazon ads/telemetry extras"
    Write-Host "  5) Restore everything option 4 turned off"
    Write-Host "  Q) Quit"
    switch ((Read-Host "Choose").Trim().ToUpper()) {
        '1' { Show-Report }
        '2' { Clear-Caches }
        '3' { Remove-UserApps }
        '4' { Disable-Extras }
        '5' { Restore-Extras }
        'Q' { & adb disconnect $Target | Out-Null; Write-Host "Disconnected. Bye!"; return }
        default { Write-Host "Pick 1-5 or Q." }
    }
}
