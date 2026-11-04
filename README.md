<div align="center">

# Free My Fire Stick

**Free up space and clear the clutter on your Amazon Fire TV.**

Fewer ads, no telemetry, faster menus, and only the apps you actually use.<br>
Mac, Windows or Linux. No root. Every change can be undone.

[Install](#install) · [What it does](#what-it-does) · [Make it look cleaner](#make-it-look-cleaner) · [Undo](#undo-everything) · [For AI assistants](CLAUDE.md)

</div>

## What you get

- **More space.** Clears every app's cache (often a few hundred MB), shows the biggest apps, and finds leftover
  installer files from Downloader.
- **Only your apps.** Lists the apps you installed, with their sizes, and uninstalls the ones you pick.
- **Fewer ads.** Turns off Special Offers, the advertising ID, ad tracking of what's on screen, promo
  notifications, and trailers that autoplay on the home screen.
- **Less spying.** Turns off the background services that upload usage, performance and log data to Amazon.
- **Less clutter.** Turns off Amazon Shopping, tutorials, "what's new" popups, and any Amazon apps you don't use
  (Photos, Music, miniTV, Games, Silk, Live TV), each one only if you say yes.
- **Faster.** The Ambient Experience screensaver is often the biggest memory user; turning it off frees RAM and
  about 1 GB. Menus can animate twice as fast.
- **Safe.** Amazon apps are turned off, never uninstalled. The home screen, Settings, the Appstore, system updates,
  Wi-Fi, the remote and voice search are never touched. One command turns it all back on.
- **Easy.** It finds your Fire TV on the Wi-Fi by itself, and downloads Google's official adb if you don't have it.

Tested on a Fire TV Stick 4K (Fire OS 8.1) with 14 apps: 610 MB freed, 27 Amazon extras turned off, more free RAM,
and the home screen, Alexa, the Appstore and every streaming app kept working.

## Install

About five minutes. You need a Fire TV and a computer (Mac, Windows or Linux) on the same Wi-Fi.

### On the Fire TV (every way)

1. Settings → **My Fire TV** → **About** → select your device's name **7 times**, until it says you're a developer.
2. Settings → My Fire TV → **Developer options** → turn on **ADB debugging**, or **Wireless debugging** on newer
   Fire OS. If it asks *Allow wireless debugging on this network?*, tick *Always allow on this network* and choose
   **Allow**. If it asks to restart, let it.

### The easy way: an AI assistant

Open an AI coding assistant ([Claude Code](https://claude.com/claude-code), Codex or another) on your computer and
say:

> Clean up my Fire Stick with Free My Fire Stick (github.com/balrajparsi/free-my-firestick).

It downloads the tool, finds your Fire TV, shows you what's taking space, and asks before changing anything. When
the TV asks *Allow USB debugging?*, tick *Always allow* and choose **Allow**.

### Double-click

1. Download this project: the green **Code** button → **Download ZIP**, then unzip it.
2. Open the folder and double-click:
   - **Mac:** `start.command` (the first time, right-click → **Open**, since it isn't from the App Store).
   - **Windows:** `start.bat` (if Python is missing, it installs it; then double-click again).
3. When the TV asks *Allow USB debugging?*, tick *Always allow* and choose **Allow**.

If adb (Android's debugging tool) isn't on your computer, it offers to download Google's official copy into the
folder. Nothing else to install.

### The terminal way

```bash
git clone https://github.com/balrajparsi/free-my-firestick && cd free-my-firestick
python3 firestick.py
```
On Windows, use `py -3 firestick.py`. It finds the Fire TV by itself; if it can't, it asks for the IP address
(Settings → My Fire TV → About → **Network**), or give it with `--ip 192.168.1.50`.

**Wireless debugging and pairing.** Usually choosing *Allow* is enough. If it won't connect, pair once: on the TV,
Wireless debugging → **Pair device with pairing code** (keep that screen open), then:
```bash
python3 firestick.py --ip 192.168.1.50 --port 41235 --pair-port 37099
```
`--port` is the port on the main Wireless debugging screen, `--pair-port` the one on the pairing screen, and you type
the 6-digit code when asked.

**On a Mac**, if it says `No route to host`, macOS is blocking the terminal from your network: allow it in System
Settings → Privacy & Security → **Local Network**, then try again.

## What it does

The menu:

| Option | What it does | Risk |
|---|---|---|
| 1 Storage report | Free space, the 20 biggest apps, cache size, leftover installer files, Amazon extras still on | None: changes nothing |
| 2 Clear all app caches | Deletes temporary cache files for every app | None: apps stay signed in |
| 3 Uninstall apps you installed | Lists your apps with sizes, uninstalls the ones you pick, asking for each | Deletes that app's data |
| 4 Turn off Amazon extras | Goes through the groups below, asking about each | Low: recorded, undo with 5 |
| 5 Restore | Turns back on everything 4 and 6 changed | None |
| 6 Faster menus | Menu and transition animations at 0.5x | None: undo with 5 |

Option 4's groups:

| Group | What's in it | Suggested |
|---|---|---|
| Ads and promotions | Special Offers, advertising ID, ad deep-links, on-screen content recognition, deals, promo notifications, autoplaying trailers | Yes |
| Amazon Shopping | The Shopping app and its background service | Yes |
| Usage and diagnostics uploads | 11 metrics, telemetry, performance and log collectors | Yes |
| Tutorials and release notes | Setup tutorials, "what's new" notes, early-access popups | Yes |
| Ambient Experience | The art and widget screensaver (~1 GB, often the biggest RAM user) | Yes |
| Amazon apps you may not use | Photos, Music, miniTV, Games hub, GameCircle, Fling, Silk Browser, Live TV tab, asked one at a time | Your call |
| Smart Home and Echo audio extras | Smart-home camera map, Echo speaker audio settings | Only without Echo or cameras |
| Amazon Kids | Kids profiles and time limits | Only if no kids use the TV |
| Alexa alert and notification popups | Timers, reminders and notifications on the TV (voice search keeps working) | Your call |

Fire OS protects a few of these (crash reports, some diagnostics, ad deep-links). The tool says so and leaves them on.

**One task at a time**, for scripts and AI assistants:

```bash
python3 firestick.py report                          # changes nothing
python3 firestick.py clean                           # clear caches
python3 firestick.py apps                            # list your apps, pick some to uninstall
python3 firestick.py uninstall com.example.app       # uninstall by package name
python3 firestick.py extras --list                   # what's still on
python3 firestick.py extras --only ads telemetry     # turn off these groups
python3 firestick.py fast-menus
python3 firestick.py restore                         # undo everything
python3 firestick.py find                            # Fire TVs on the Wi-Fi
```

## Make it look cleaner

Amazon doesn't let a computer change these, so use the remote (two minutes):

- **Your apps first:** hold **Home** → **Apps**, highlight an app, press **☰** → **Move to front**. Do your least
  favorite first and your top favorite last, so it ends up first.
- **No autoplaying trailers:** Settings → Preferences → **Featured Content** → turn off *Video Autoplay* and
  *Audio Autoplay*.
- **Fewer targeted ads:** Settings → Preferences → **Privacy Settings** → turn off *Device Usage Data*, *Collect App
  Usage Data* and *Interest-based Ads*.
- **Leftover installers:** open **Downloader** → **Files**, select the `.apk`, and choose **Delete**.
- **Restart** when you're done: Settings → My Fire TV → **Restart**.
- **Close the door:** turn **ADB debugging** / **Wireless debugging** back off in Developer options, so other devices
  on your Wi-Fi can't connect to the Fire TV. Turn it on again the next time you clean.

**A fully different home screen?** Since Fire OS 7.6, Amazon blocks replacing its home screen. A launcher app from
the Appstore (Projectivy, Wolf Launcher) or [Free My TV](https://github.com/simbasjungles/free-my-tv) can run as an
app you open, but the Home button still goes back to Amazon's.

## Undo everything

```bash
python3 firestick.py restore
```
or option 5 in the menu. It turns back on everything recorded in `firestick-turned-off.json`, next to the script,
including the animation speed. Keep that file. Without it, Settings → My Fire TV → **Reset to Factory Defaults**
also brings everything back (and erases your apps).

## Why not Free My TV?

[Free My TV](https://github.com/simbasjungles/free-my-tv), which inspired this project, is a new home screen for
Google TV, LG and Samsung. On Fire TV it can only run as an app you open, since Amazon keeps the Home button, and it
doesn't free space or turn off Amazon's extras. This tool does that part.

## License

© 2026 Balraj Parsi. All rights reserved. You may run it on devices you own for personal use; copying, modifying or
redistributing it needs permission. See [LICENSE](LICENSE). Not affiliated with Amazon. Use at your own risk.
