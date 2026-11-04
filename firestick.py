#!/usr/bin/env python3
"""Free My Fire Stick: free up space and declutter an Amazon Fire TV over ADB.

Works on macOS, Windows and Linux with Python 3.8+ and nothing else: it finds adb (or downloads Google's official
platform-tools after asking), finds the Fire TV on your Wi-Fi, and walks you through a menu. Nothing is removed
without asking, and everything it turns off can be turned back on (option 5 / `restore`).

    python3 firestick.py                     # menu; finds the Fire TV by itself
    python3 firestick.py --ip 192.168.1.50   # or say where it is
    python3 firestick.py report              # one task, then exit (see --help)

Copyright (c) 2026 Balraj Parsi. All rights reserved. See LICENSE.
"""
import argparse
import datetime
import glob
import json
import os
import platform
import re
import shutil
import stat
import subprocess
import sys
import time
import urllib.request
import zipfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
RECORD = HERE / "firestick-turned-off.json"
PLATFORM_TOOLS = HERE / "platform-tools"
YES = False  # --yes: skip confirmations (only after the person agreed to the exact change)

# Optional Amazon extras, in groups. Only packages that exist and are on get offered. Tested on a Fire TV Stick 4K
# (Fire OS 8.1): the home screen, voice search, the Appstore and updates keep working with all of these off.
# Fire OS protects a few (crash reports, some diagnostics, ad deep-links): those are reported and stay on.
EXTRA_GROUPS = [
    {"key": "ads", "name": "Ads and promotions", "rec": True,
     "info": "Special Offers, advertising ID, ad deep-links, on-screen content recognition, deals, promo "
             "notifications, autoplaying trailers",
     "packages": ["com.amazon.kso", "com.amazon.kso.blackbird", "com.amazon.hybridadidservice", "com.amazon.tv.acr",
                  "com.amazon.ftvads.deeplinking", "com.amazon.device.sale.service", "com.amazon.hedwig",
                  "com.amazon.sneakpeek"]},
    {"key": "shopping", "name": "Amazon Shopping", "rec": True,
     "info": "The Shopping app and its background service",
     "packages": ["com.amazon.shoptv.firetv.client", "com.amazon.shoptv.client"]},
    {"key": "telemetry", "name": "Usage and diagnostics uploads", "rec": True,
     "info": "Metrics, telemetry, performance and log collectors that send data to Amazon",
     "packages": ["com.amazon.client.metrics", "com.amazon.device.crashmanager", "com.amazon.device.metrics",
                  "com.amazon.device.telemetry.emitter", "com.amazon.wirelessmetrics.service",
                  "com.amazon.perfcollection", "com.amazon.perfc", "com.amazon.device.logmanager",
                  "com.amazon.dp.logger", "com.amazon.neo.minerva.logcat", "com.amazon.logan"]},
    {"key": "tutorials", "name": "Tutorials and release notes", "rec": True,
     "info": "Setup tutorials, \"what's new\" notes, early-access popups",
     "packages": ["com.amazon.storm.lightning.tutorial", "com.amazon.tmm.tutorial", "com.amazon.tv.releasenotes",
                  "com.amazon.tv.earlyaccess"]},
    {"key": "ambient", "name": "Ambient Experience", "rec": True,
     "info": "The art and widget screensaver: often the biggest RAM user and ~1 GB of storage. "
             "The plain screensaver takes over",
     "packages": ["com.amazon.tv.ftvambient"]},
    {"key": "apps", "name": "Amazon apps you may not use", "rec": False, "per_item": True,
     "info": "Asked one by one",
     "packages": ["com.amazon.bueller.photos", "com.amazon.bueller.music", "com.amazon.minitv.android.app",
                  "com.amazon.gamehub", "com.amazon.ags.app", "com.amazon.awvflingreceiver", "com.amazon.cloud9",
                  "com.amazon.spiderpork", "com.amazon.tv.livetv"]},
    {"key": "smarthome", "name": "Smart Home and Echo audio extras", "rec": False,
     "info": "Smart-home camera map and Echo speaker audio settings. Keep them if you have Echo speakers or cameras",
     "packages": ["com.amazon.smarthomemapviewapp", "com.amazon.audiohome"]},
    {"key": "kids", "name": "Amazon Kids", "rec": False,
     "info": "Kids profiles and time limits. Turn off only if no kids use this TV",
     "packages": ["com.amazon.tahoe"]},
    {"key": "alexa-popups", "name": "Alexa alert and notification popups", "rec": False,
     "info": "Timers, reminders and notifications on the TV. Voice search keeps working",
     "packages": ["com.amazon.tv.alexaalerts", "com.amazon.tv.alexanotifications"]},
]

# Never turned off or removed, whatever is asked.
PROTECTED = {
    "com.amazon.tv.launcher", "com.amazon.tv.settings", "com.amazon.tv.settings.v2", "com.amazon.venezia",
    "com.amazon.device.software.ota", "com.amazon.tv.forcedotaupdater.v2", "com.amazon.wifilocker",
    "com.amazon.tv.ime", "com.amazon.tv.inputpreference.service", "com.amazon.device.messaging",
    "com.android.settings", "com.android.systemui",
}

# Refused with "Cannot disable a protected package" on Fire OS 8.1: still tried (older Fire OS may allow it), but not
# counted as clutter that's "still on".
FIRE_OS_PROTECTED = {"com.amazon.device.crashmanager", "com.amazon.device.metrics", "com.amazon.device.logmanager",
                     "com.amazon.ftvads.deeplinking"}

NAMES = {
    "com.amazon.bueller.photos": "Amazon Photos", "com.amazon.bueller.music": "Amazon Music",
    "com.amazon.minitv.android.app": "Amazon miniTV", "com.amazon.gamehub": "Games hub (Luna)",
    "com.amazon.ags.app": "GameCircle", "com.amazon.awvflingreceiver": "Fling from phone",
    "com.amazon.cloud9": "Silk Browser", "com.amazon.spiderpork": "Silk Browser launcher",
    "com.amazon.tv.livetv": "Live TV tab", "com.amazon.tv.ftvambient": "Ambient Experience",
    "com.amazon.tv.launcher": "Amazon home screen", "com.amazon.firebat": "Prime Video",
    "com.amazon.firetv.youtube": "YouTube", "com.netflix.ninja": "Netflix", "com.hulu.plus": "Hulu",
    "com.hbo.hbonow": "HBO Max", "com.wbd.stream": "Max", "com.disney.disneyplus": "Disney+",
    "com.peacock.peacockfiretv": "Peacock", "com.spotify.tv.android": "Spotify", "com.esaba.downloader": "Downloader",
    "com.plexapp.android": "Plex", "org.xbmc.kodi": "Kodi", "com.cbs.ott": "Paramount+",
    "com.apple.atve.amazon.appletv": "Apple TV", "com.surfshark.vpnclient.android": "Surfshark",
    "com.nordvpn.android": "NordVPN", "tv.twitch.android.viewer": "Twitch", "com.pluto.tv": "Pluto TV",
    "com.tubitv": "Tubi", "com.sling": "Sling TV", "com.fubo.firetv.screen": "fuboTV",
    "com.google.android.youtube.tvunplugged": "YouTube TV", "com.zee5.amazon": "ZEE5", "ahaflix.tv": "aha",
}

ANIMATION_KEYS = ["window_animation_scale", "transition_animation_scale", "animator_duration_scale"]

# ---------------------------------------------------------------------------------------------------------------- ui

if os.name == "nt":
    os.system("")  # turns on ANSI colors in the Windows console
_TTY = sys.stdout.isatty()


def color(text, code):
    return f"\033[{code}m{text}\033[0m" if _TTY else text


def title(text):
    print()
    print(color(f"== {text} ==", "36"))


def ok(text):
    print(color(text, "32"))


def warn(text):
    print(color(text, "33"))


def fail(text):
    print(color(text, "31"))


def ask(question):
    if YES:
        print(f"{question} [y/N] y (--yes)")
        return True
    try:
        return input(f"{question} [y/N] ").strip().lower() in ("y", "yes")
    except EOFError:
        return False


def size(n):
    n = float(n)
    if n >= 1024 ** 3:
        return f"{n / 1024 ** 3:.2f} GB"
    if n >= 1024 ** 2:
        return f"{n / 1024 ** 2:,.0f} MB"
    return f"{n / 1024:,.0f} KB"


def name(pkg):
    return f"{NAMES[pkg]} ({pkg})" if pkg in NAMES else pkg


# --------------------------------------------------------------------------------------------------------------- adb

def find_adb():
    """adb from this folder, PATH, or where installers usually put it (PATH may not be refreshed yet)."""
    exe = "adb.exe" if os.name == "nt" else "adb"
    home = Path.home()
    candidates = [PLATFORM_TOOLS / exe]
    found = shutil.which("adb")
    if found:
        candidates.append(Path(found))
    for var in ("ANDROID_HOME", "ANDROID_SDK_ROOT"):
        if os.environ.get(var):
            candidates.append(Path(os.environ[var]) / "platform-tools" / exe)
    if os.name == "nt":
        local = Path(os.environ.get("LOCALAPPDATA", home / "AppData" / "Local"))
        candidates += [Path(p) for p in glob.glob(str(local / "Microsoft" / "WinGet" / "Packages" /
                                                       "Google.PlatformTools*" / "platform-tools" / exe))]
        candidates.append(local / "Android" / "Sdk" / "platform-tools" / exe)
    elif sys.platform == "darwin":
        candidates += [Path("/opt/homebrew/bin/adb"), Path("/usr/local/bin/adb"),
                       home / "Library" / "Android" / "sdk" / "platform-tools" / "adb"]
    else:
        candidates += [home / "Android" / "Sdk" / "platform-tools" / "adb", Path("/usr/bin/adb")]
    for c in candidates:
        if c.is_file():
            return str(c)
    return None


def download_adb():
    """Google's official platform-tools, into ./platform-tools (only after asking)."""
    osname = {"win32": "windows", "darwin": "darwin"}.get(sys.platform, "linux")
    url = f"https://dl.google.com/android/repository/platform-tools-latest-{osname}.zip"
    print("adb (Android's debugging tool, from Google) isn't on this computer.")
    print(f"I can download Google's official copy (about 7 MB) into this folder:\n  {url}")
    if not ask("Download it now?"):
        print("Or install it yourself, then run this again:")
        print({"windows": "  winget install Google.PlatformTools",
               "darwin": "  brew install --cask android-platform-tools"}.get(osname, "  sudo apt install adb"))
        sys.exit(1)
    zpath = HERE / "platform-tools.zip"
    urllib.request.urlretrieve(url, zpath)
    with zipfile.ZipFile(zpath) as z:
        z.extractall(HERE)
    zpath.unlink()
    adb = PLATFORM_TOOLS / ("adb.exe" if os.name == "nt" else "adb")
    if os.name != "nt":
        adb.chmod(adb.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
    ok(f"adb is ready: {adb}")
    return str(adb)


def run(adb, *args, timeout=60):
    try:
        p = subprocess.run([adb, *args], capture_output=True, text=True, timeout=timeout,
                           encoding="utf-8", errors="replace")
        return (p.stdout + p.stderr).strip()
    except subprocess.TimeoutExpired:
        return "timeout"


def discover(adb):
    """Fire TVs announcing themselves on the Wi-Fi (mDNS), as [(name, 'ip:port', kind)]."""
    run(adb, "start-server")
    found = []
    for _ in range(3):
        out = run(adb, "mdns", "services", timeout=15)
        for line in out.splitlines():
            m = re.match(r"(\S+)\s+(_adb(?:-tls-connect)?\._tcp)\.?\s+(\d+\.\d+\.\d+\.\d+:\d+)", line.strip())
            if m and m.group(3) not in [f[1] for f in found]:
                found.append((m.group(1), m.group(3), "tls" if "tls" in m.group(2) else "plain"))
        if found:
            break
        time.sleep(2)
    # Plain ADB (port 5555) first: it needs no pairing.
    return sorted(found, key=lambda f: f[2] != "plain")


class FireTV:
    def __init__(self, adb, target, runner=None):
        self.adb, self.target = adb, target
        self._run = runner or (lambda *a: run(self.adb, "-s", self.target, *a))

    def sh(self, cmd):
        return self._run("shell", cmd)

    # -- facts
    def model(self):
        return f"{self.sh('getprop ro.product.model')} ({self.sh('getprop ro.build.version.name')})"

    def free_space(self):
        """(total, used, free) bytes of /data. Read from the end: long filesystem names can wrap."""
        f = self.sh("df -k /data").split()
        return tuple(float(f[-i]) * 1024 for i in (5, 4, 3))

    def packages(self, flags=""):
        return [l.strip()[len("package:"):] for l in self.sh(f"pm list packages {flags}").splitlines()
                if l.strip().startswith("package:")]

    def user_apps(self):
        # Fire OS 8 lists Amazon's resource overlays (...overlay.localisation.common) as user apps: they hold
        # system menu text, so never offer them.
        return sorted(p for p in self.packages("-3") if ".overlay." not in p and p not in PROTECTED)

    def app_sizes(self):
        """{package: (app, data, cache)} from dumpsys diskstats (Fire OS refreshes it now and then)."""
        raw = self.sh("dumpsys diskstats")

        def arr(label):
            m = re.search(label + r"\s*:\s*(\[.*?\])", raw, re.S)
            return json.loads(m.group(1)) if m else []
        names, app, data, cache = arr("Package Names"), arr("App Sizes"), arr("App Data Sizes"), arr("Cache Sizes")
        return {n: (app[i], data[i], cache[i]) for i, n in enumerate(names)
                if i < len(app) and i < len(data) and i < len(cache)}

    def leftover_installers(self):
        """[(bytes, path)] of .apk/.xapk files on the shared storage. Trailing slash: /sdcard is a symlink."""
        out = self.sh("find /sdcard/ -type f \\( -iname '*.apk' -o -iname '*.xapk' -o -iname '*.apks' \\) "
                      "-exec ls -l {} \\; 2>/dev/null")
        files = []
        for line in out.splitlines():
            p = line.split()
            if len(p) >= 8 and p[4].isdigit():
                files.append((int(p[4]), " ".join(p[7:])))
        return files

    # -- changes
    def disable(self, pkg):
        """'disabled', 'protected' or the error. Never for PROTECTED packages."""
        if pkg in PROTECTED:
            return "protected"
        r = self.sh(f"pm disable-user --user 0 {pkg}")
        if "new state: disabled" in r:
            return "disabled"
        return "protected" if "protected package" in r else r


# ------------------------------------------------------------------------------------------------------------ record

def read_record():
    if not RECORD.exists():
        return []
    data = json.loads(RECORD.read_text(encoding="utf-8-sig") or "[]")  # utf-8-sig: older PowerShell wrote a BOM
    return data if isinstance(data, list) else [data]


def save_record(entries):
    RECORD.write_text(json.dumps(entries, indent=2), encoding="utf-8")


def remember(entry):
    entries = read_record()
    entry["When"] = datetime.datetime.now().replace(microsecond=0).isoformat()
    entries.append(entry)
    save_record(entries)


# ----------------------------------------------------------------------------------------------------------- connect

MAC_LOCAL_NETWORK = ("On a Mac, macOS may be blocking adb from your network (Local Network privacy). Allow your "
                     "terminal app in System Settings > Privacy & Security > Local Network, then run this again.")


def connect(adb, ip=None, port=5555, pair_port=None):
    run(adb, "start-server")
    if not ip:
        print("Looking for your Fire TV on the Wi-Fi...")
        found = discover(adb)
        if found and len({f[1].split(":")[0] for f in found}) == 1:  # one TV (maybe listed twice: plain + tls)
            ip, port = found[0][1].split(":")
        elif found:
            for i, f in enumerate(found, 1):
                print(f"  [{i}] {f[0]}  {f[1]}")
            pick = input("Which one? ").strip()
            ip, port = found[int(pick) - 1][1].split(":") if pick.isdigit() else (None, None)
        if not ip:
            print("Couldn't find it by itself. On the TV: Settings > My Fire TV > About > Network shows the IP address.")
            ip = input("Fire TV IP address (e.g. 192.168.1.50): ").strip()
        port = int(port)
    target = f"{ip}:{port}"
    if pair_port:
        code = input("Pairing code shown on the TV: ").strip()
        out = run(adb, "pair", f"{ip}:{pair_port}", code)
        print(out)
        if "Successfully paired" not in out:
            fail("Pairing didn't work. Open 'Pair device with pairing code' again and use the new port and code.")
            sys.exit(1)
    print(f"Connecting to {target}. If the TV asks to allow debugging, tick 'Always allow' and choose Allow.")
    out = run(adb, "connect", target, timeout=20)
    if "No route to host" in out and sys.platform == "darwin":
        warn(MAC_LOCAL_NETWORK)
    state = ""
    for _ in range(20):
        state = run(adb, "-s", target, "get-state", timeout=10)
        if state == "device":
            break
        if "unauthorized" in state or "authenticate" in out:
            print("  Waiting for you to choose Allow on the TV...")
        time.sleep(3)
        if "connected" not in out:
            out = run(adb, "connect", target, timeout=20)
    if state != "device":
        fail(f"Couldn't connect ({state or out}).")
        print("Check: Developer options > ADB debugging (or Wireless debugging) is ON, the TV and this computer are on "
              "the same Wi-Fi, and you chose Allow on the TV.")
        print("With Wireless debugging, you may need to pair once: run again with --pair-port (see README).")
        sys.exit(1)
    tv = FireTV(adb, target)
    ok(f"Connected: {tv.model()}")
    return tv


# ------------------------------------------------------------------------------------------------------------- tasks

def show_space(tv, label="Storage"):
    total, used, free = tv.free_space()
    print(f"{label}: {size(free)} free of {size(total)} ({100 * used / total:.0f}% used)")
    return free


def task_report(tv):
    title("Storage report")
    show_space(tv)
    user = set(tv.user_apps())
    installed = set(tv.packages())
    off = set(tv.packages("-d"))
    # diskstats is refreshed only now and then: drop apps that are gone since.
    sizes = {p: v for p, v in tv.app_sizes().items() if p in installed}
    if sizes:
        print("\nBiggest 20 apps (* = installed by you, removable with option 3; 'off' = turned off):")
        top = sorted(sizes.items(), key=lambda kv: -sum(kv[1]))[:20]
        for pkg, (a, d, c) in top:
            mark = "*" if pkg in user else " "
            state = "  off" if pkg in off else ""
            print(f"  {mark} {name(pkg)[:56]:<56} {size(a + d + c):>9}  (cache {size(c)}){state}")
        print(f"\nCache across all apps: about {size(sum(v[2] for v in sizes.values()))} (option 2 clears it).")
    files = tv.leftover_installers()
    if files:
        print("\nLeftover installer files (safe to delete once the app is installed):")
        for b, path in files:
            print(f"  {size(b):>9}  {path}")
        print("  Delete them on the TV: open Downloader > Files, select the file, and choose Delete.")
    on = set(tv.packages("-e")) - FIRE_OS_PROTECTED
    left = [g["name"] for g in EXTRA_GROUPS if any(p in on for p in g["packages"])]
    if left:
        print("\nAmazon extras still on (option 4): " + ", ".join(left))


def task_clean(tv):
    title("Clear all app caches")
    print("Deletes only temporary cache files. Apps stay signed in and keep their settings.")
    if not ask("Clear caches now?"):
        return
    before = tv.free_space()[2]
    tv.sh("pm trim-caches 999G")  # asking Android to keep this much free makes it drop every app's cache
    time.sleep(3)
    after = show_space(tv, "Now")
    ok(f"Freed {size(max(0, after - before))}.")


def task_apps(tv, remove=None):
    title("Apps you installed")
    apps = tv.user_apps()
    sizes = tv.app_sizes()
    for i, p in enumerate(apps, 1):
        print(f"  [{i:>2}] {name(p)[:56]:<56} {size(sum(sizes[p])) if p in sizes else '':>9}")
    if remove is None:
        pick = input("Numbers to uninstall, separated by commas (e.g. 2,5), or Enter to cancel: ").strip()
        remove = [apps[int(n) - 1] for n in re.split(r"[,\s]+", pick) if n.isdigit() and 0 < int(n) <= len(apps)]
    if not remove:
        return
    before = tv.free_space()[2]
    for p in remove:
        if p not in apps:
            warn(f"  {p}: not an app you installed; skipped.")
            continue
        if ask(f"  Uninstall {name(p)}? Its data and logins are deleted."):
            print(f"  {name(p)}: {tv._run('uninstall', p)}")
    after = show_space(tv, "Now")
    ok(f"Freed {size(max(0, after - before))}.")


def task_extras(tv, only=None, list_only=False):
    title("Turn off Amazon extras")
    print("Turned off, not deleted. Option 5 (restore) brings everything back.")
    on = set(tv.packages("-e"))
    done = 0
    for g in EXTRA_GROUPS:
        if only and g["key"] not in only:
            continue
        present = [p for p in g["packages"] if p in on]
        if not [p for p in present if p not in FIRE_OS_PROTECTED]:
            continue  # nothing left here but what Fire OS won't let go
        tag = " [recommended]" if g["rec"] else ""
        print(f"\n{g['name']}{tag} (--only {g['key']}): {g['info']}")
        if list_only:
            for p in present:
                print(f"    {name(p)}")
            continue
        if g.get("per_item"):
            chosen = [p for p in present if ask(f"  Turn off {name(p)}?")]
        else:
            chosen = present if ask(f"  Turn off this group ({len(present)} part(s))?") else []
        for p in chosen:
            r = tv.disable(p)
            if r == "disabled":
                remember({"Package": p, "Method": "disable"})
                done += 1
            elif r == "protected":
                warn(f"    {name(p)} is protected by Fire OS; it stays on.")
            else:
                warn(f"    {name(p)}: Fire OS refused ({r.splitlines()[0] if r else 'no answer'}).")
    if not list_only:
        print()
        ok(f"Turned off {done} part(s). Restart the Fire TV to get the full benefit.")


def task_fast_menus(tv):
    title("Faster menus")
    print("Halves the time menus and screen transitions take to animate (1x to 0.5x). Restore sets it back.")
    if not ask("Make menus faster?"):
        return
    for k in ANIMATION_KEYS:
        old = tv.sh(f"settings get global {k}")
        if old == "0.5":
            continue
        tv.sh(f"settings put global {k} 0.5")
        remember({"Package": f"global {k}", "Method": "setting", "Value": old if old not in ("", "null") else "1.0"})
    ok("Menus now animate at 0.5x.")


def task_restore(tv):
    title("Restore")
    entries = read_record()
    if not entries:
        print(f"Nothing recorded in {RECORD.name}, so nothing to restore.")
        return
    if not ask(f"Turn back on the {len(entries)} change(s) recorded in {RECORD.name}?"):
        return
    for e in entries:
        if e.get("Method") == "setting":
            tv.sh(f"settings put {e['Package']} {e['Value']}")
            r = f"set back to {e['Value']}"
        elif e.get("Method") == "uninstall-user":
            r = tv.sh(f"cmd package install-existing {e['Package']}")
        else:
            r = tv.sh(f"pm enable {e['Package']}")
        print(f"  {e['Package']}: {r}")
    RECORD.unlink()
    ok("All restored. Restart the Fire TV (Settings > My Fire TV > Restart).")


# -------------------------------------------------------------------------------------------------------------- main

def menu(tv):
    show_space(tv)
    while True:
        title("Free My Fire Stick")
        print("  1) Storage report")
        print("  2) Clear all app caches")
        print("  3) Uninstall apps you installed")
        print("  4) Turn off Amazon ads, telemetry and unused extras")
        print("  5) Restore everything 4 and 6 changed")
        print("  6) Faster menus")
        print("  Q) Quit")
        try:
            choice = input("Choose: ").strip().upper()
        except EOFError:
            choice = "Q"
        actions = {"1": task_report, "2": task_clean, "3": task_apps, "4": task_extras, "5": task_restore,
                   "6": task_fast_menus}
        if choice == "Q":
            print("Done. When you've finished, you can turn ADB/Wireless debugging off in Developer options.")
            return
        if choice in actions:
            actions[choice](tv)
        else:
            print("Pick 1-6 or Q.")


def main(argv=None):
    global YES
    ap = argparse.ArgumentParser(
        prog="firestick.py", description="Free up space and declutter an Amazon Fire TV over ADB.",
        epilog="Without a task, opens the menu. Everything turned off is recorded in firestick-turned-off.json and "
               "can be undone with 'restore'.")
    ap.add_argument("task", nargs="?", choices=["report", "clean", "apps", "uninstall", "extras", "fast-menus",
                                                "restore", "find"],
                    help="report: storage and clutter (changes nothing); clean: clear caches; apps: list/uninstall "
                         "your apps; uninstall PKG...; extras: turn off Amazon extras; fast-menus; restore; "
                         "find: list Fire TVs on the Wi-Fi")
    ap.add_argument("packages", nargs="*", help="for 'uninstall': package names")
    ap.add_argument("--ip", help="the Fire TV's IP address (found by itself when left out)")
    ap.add_argument("--port", type=int, default=5555, help="ADB port (Wireless debugging shows it), default 5555")
    ap.add_argument("--pair-port", type=int, help="the port on 'Pair device with pairing code' (one-time pairing)")
    ap.add_argument("--only", nargs="+", metavar="GROUP", help="for 'extras': only these groups ("
                    + ", ".join(g["key"] for g in EXTRA_GROUPS) + ")")
    ap.add_argument("--list", action="store_true", help="for 'extras': only show what's still on")
    ap.add_argument("--yes", action="store_true", help="don't ask before each change (use only when you mean it)")
    a = ap.parse_args(argv)
    YES = a.yes

    adb = find_adb() or download_adb()
    if a.task == "find":
        for f in discover(adb):
            print(f"{f[0]}  {f[1]}  ({'needs pairing' if f[2] == 'tls' else 'ready'})")
        return
    tv = connect(adb, a.ip, a.port, a.pair_port)
    {
        None: menu, "report": task_report, "clean": task_clean, "fast-menus": task_fast_menus,
        "restore": task_restore, "apps": task_apps,
        "uninstall": lambda t: task_apps(t, remove=a.packages),
        "extras": lambda t: task_extras(t, only=a.only, list_only=a.list),
    }[a.task](tv)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nStopped.")
