# Free My Fire Stick: notes for AI assistants

A cleanup tool for Amazon Fire TV (Fire TV Stick, Cube, and TVs with Fire OS built in). One Python 3 file,
`firestick.py`, standard library only, for macOS, Windows and Linux. It talks to the Fire TV over ADB on the Wi-Fi:
storage report, clearing caches, uninstalling apps the person installed, turning off Amazon ads, telemetry and
unused extras (never uninstalling them), and faster menus. Everything it turns off is written to
`firestick-turned-off.json` (git-ignored) and `restore` brings it back.

The person you're helping may not be technical. Keep it short and friendly, say what you're about to change on their
TV before you do it, and let them do the taps on the TV.

## Always

- Run `python3 firestick.py report` first. It changes nothing, and it's the list to talk through with them.
- Ask before each change, naming it: which app to uninstall (its data and logins go with it), which group to turn
  off. `--yes` skips the script's own prompts, so use it only for exactly what they agreed to.
- Never uninstall or clear the data of Amazon or system apps. Only `pm disable-user --user 0`, through the script, so
  `restore` can bring them back. The `PROTECTED` set (home screen, Settings, Appstore, updates, Wi-Fi, keyboard,
  inputs) is never touched.
- Never delete their files (photos, downloads, leftover `.apk` installers). The report lists the installers; they
  delete them on the TV (Downloader > Files > Delete).
- Never change their network, account, picture or sound settings.
- Keep `firestick-turned-off.json` next to the script. Without it, `restore` doesn't know what to turn back on (a
  factory reset does).
- Never commit `firestick-turned-off.json`, `platform-tools/` or anything that names their network, IP or device ID.
- Before you push, run `python3 -m unittest discover -s tests`. Pull requests run it on macOS, Windows and Linux
  (`.github/workflows/check.yml`).

## Cleaning someone's Fire TV

They'll usually say something like "Clean up my Fire Stick" or "Free up space on my Fire TV at 192.168.1.50".

1. **Python 3.8+.** `python3 --version` (Windows: `py -3 --version`). If it's missing: Mac `xcode-select --install`
   or `brew install python`; Windows `winget install -e --id Python.Python.3.12`; Linux the package manager.
2. **On the TV**, they turn on developer mode: Settings > My Fire TV > About > select the device name 7 times. Then
   Settings > My Fire TV > Developer options > **ADB debugging** ON (older Fire OS) or **Wireless debugging** ON
   (newer). If it asks *Allow wireless debugging on this network?*, they tick *Always allow on this network* and
   choose Allow. If it asks to restart, let it.
3. **adb.** The script finds it (PATH, winget's and Homebrew's folders, Android SDK) or offers to download Google's
   official platform-tools into `platform-tools/`. Interactive prompt: run that step in their terminal, or install
   adb first (`brew install --cask android-platform-tools`, `winget install Google.PlatformTools`, `apt install adb`).
4. **Find and connect.** `python3 firestick.py find` lists Fire TVs on the Wi-Fi (mDNS). Every other task connects by
   itself: one TV found is used, several are listed, none asks for the IP (Settings > My Fire TV > About > Network).
   The TV then asks *Allow USB debugging?*: they tick *Always allow* and choose Allow; the script waits a minute.
   - On a Fire TV Stick 4K (Fire OS 8.1), Wireless debugging still answered on port 5555 after *Allow*, without
     pairing. If only a `tls` port shows up in `find`, pair once: on the TV, Wireless debugging > *Pair device with
     pairing code*, then `python3 firestick.py --ip <IP> --port <port on the main screen> --pair-port <port on the
     pairing screen> report` and they type the code (it expires in a minute or two).
   - On a Mac, `No route to host` while the TV is on means macOS's Local Network privacy is blocking adb: they allow
     their terminal app in System Settings > Privacy & Security > Local Network.
5. **Report**, then go through it with them:
   - `clean`: clears every app's cache (`pm trim-caches`). Logins stay. Usually a few hundred MB.
   - `apps` lists what they installed, with sizes; `uninstall <package>...` removes the ones they name.
   - `extras --list` shows the groups still on; `extras --only <group>...` turns off the ones they pick
     (`ads`, `shopping`, `telemetry`, `tutorials`, `ambient` are the usual yes; `apps` is asked one by one;
     `smarthome`, `kids`, `alexa-popups` only if they don't use them).
   - `fast-menus`: animations at 0.5x.
6. **Finish:** they restart the Fire TV (Settings > My Fire TV > Restart). Suggest the tidy-up on the TV (README,
   "Make it look cleaner"), and turning ADB/Wireless debugging off again when they're done.
7. **Undo:** `python3 firestick.py restore` turns everything in the record back on, settings included.

## Fire OS notes

- Fire OS 8 refuses `disable-user` for some packages with "Cannot disable a protected package" (crash reports,
  device metrics, log manager, ad deep-links): `FIRE_OS_PROTECTED`, tried but not counted as clutter.
- Fire OS 8 lists Amazon's resource overlays (`*.overlay.localisation.common`) as user apps. They hold the system's
  menu text: `user_apps()` skips anything with `.overlay.`.
- `dumpsys diskstats` is refreshed only now and then: uninstalled apps can linger in it, so the report keeps only
  installed packages.
- `/sdcard` is a symlink: `find /sdcard/` needs the trailing slash.
- `df -k /data` can wrap a long filesystem name onto its own line: read the numbers from the end.
- Amazon's launcher keeps the Home button (Fire OS 7.6+ blocks replacing it), so the home screen's order is set on
  the TV: Home (hold) > Apps > highlight > Menu > Move to front.

## The code

- `firestick.py`: everything. `EXTRA_GROUPS` (what option 4 offers), `PROTECTED` (never touched),
  `FIRE_OS_PROTECTED`, `NAMES` (friendly names), `FireTV` (all adb shell calls go through `sh`, so tests can fake
  it), `task_*` (one per menu entry / command), `main` (argparse).
- `start.command` (macOS/Linux, double-click on a Mac) and `start.bat` (Windows, double-click) just run it.
- `tests/test_firestick.py`: offline tests with a fake TV that answers like the Fire OS 8.1 Stick did.
- `docs/`: the project page, published to GitHub Pages by `.github/workflows/pages.yml` on a push to `main`.
