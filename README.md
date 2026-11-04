# Free My Fire Stick

Free up space on your Amazon Fire TV Stick and make it look cleaner. It runs from your Windows PC over Wi-Fi with ADB. You don't need root, and everything it turns off can be turned back on.

Inspired by [Free My TV](https://github.com/simbasjungles/free-my-tv). © 2026 Balraj Parsi, all rights reserved: free to run on your own devices, but not to copy or redistribute. See [LICENSE](LICENSE).

## Why not Free My TV?

[Free My TV](https://github.com/simbasjungles/free-my-tv) installs on a Fire Stick, but only as an app you open. Amazon's home screen keeps the Home button, and the project won't turn off any Amazon app. It also doesn't free any space, because it's a home screen, not a cleaner. This tool covers the part it leaves out.

## 1. One-time setup

**On the Fire Stick**
1. Settings → **My Fire TV** → **About** → select your device name **7 times** until it says you're a developer.
2. Settings → My Fire TV → **Developer options**. Your Stick has one of two switches:
   - **ADB debugging** (older Fire OS): turn it on. Then Settings → My Fire TV → About → **Network** and write down the **IP address** (e.g. `192.168.1.50`).
   - **Wireless debugging** (newer Fire OS): turn it on. If it asks *Allow wireless debugging on this network?*, tick *Always allow on this network* and choose **Allow**. Then open **Wireless debugging** and write down the **IP address & port** (e.g. `192.168.1.50:41235`).

**On your PC** (PowerShell):
```powershell
winget install Google.PlatformTools
```
Close and reopen PowerShell afterwards.

## 2. Run it

From the folder this file is in:
```powershell
powershell -ExecutionPolicy Bypass -File .\FireStickCleanup.ps1 -Ip 192.168.1.50
```
The first time, the TV asks **Allow USB debugging?**: tick *Always allow* and choose OK.

**With Wireless debugging**, you pair once first. On the TV, open Wireless debugging → **Pair device with pairing code**. It shows an IP address & port and a 6-digit code. Leave that screen open, then run the script with both ports: `-Port` is the one from the main Wireless debugging screen, and `-PairPort` is the one from the pairing screen.
```powershell
powershell -ExecutionPolicy Bypass -File .\FireStickCleanup.ps1 -Ip 192.168.1.50 -Port 41235 -PairPort 37099
```
Type the code when the script asks for it. After that, you can leave out `-PairPort`. The main port can change after a restart, so check it on the Wireless debugging screen each time.

**Try the simple way first.** On a Fire TV Stick 4K with Fire OS 8.1, choosing *Allow* on the Wireless debugging prompt was enough: the plain command (no `-Port`, no pairing) connected on port 5555.

If you just installed adb and PowerShell still says it can't find it, the script looks in winget's folder by itself, so you don't have to reopen PowerShell.

| Option | What it does | Risk |
|---|---|---|
| 1 Storage report | Free space, the 20 biggest apps, total cache size, and leftover installer files (`.apk`) from Downloader | None |
| 2 Clear all caches | Deletes temporary cache files for every app | None (apps stay signed in) |
| 3 Remove apps you installed | Lists your apps with their sizes and uninstalls the ones you pick, asking for each one | Deletes that app's data |
| 4 Turn off Amazon extras | Goes through the groups below and asks about each one | Low. Saved to `firestick-turned-off.json` |
| 5 Restore | Turns back on everything options 4 and 6 changed | None |
| 6 Faster menus | Sets menu and transition animations to 0.5x | None |

### What option 4 offers

| Group | What's in it | Suggested |
|---|---|---|
| Ads and promotions | Special Offers, advertising ID, ad deep-links, on-screen content recognition, deals, promo notifications, autoplaying trailers | Yes |
| Amazon Shopping | The Shopping app and its background service | Yes |
| Usage and diagnostics uploads | 11 metrics, telemetry, performance and log collectors | Yes |
| Tutorials and release notes | Setup tutorials, "what's new" notes, early-access popups | Yes |
| Ambient Experience | The art and widget screensaver. On the test Stick it was the biggest RAM user and took 1 GB of storage | Yes |
| Amazon apps you may not use | Photos, Music, miniTV, Games hub, GameCircle, Fling, Silk Browser, Live TV tab. Asked one at a time | Your call |
| Smart Home and Echo audio extras | Smart-home camera map, Echo speaker audio settings | Only without Echo or cameras |
| Amazon Kids | Kids profiles and time limits | Only if no kids use the TV |
| Alexa alert and notification popups | Timers, reminders and notifications on the TV. Voice search keeps working | Your call |

It never touches the Amazon home screen, Settings, Wi-Fi, the keyboard, inputs, the Appstore, or system updates. If you lose `firestick-turned-off.json`, an Amazon reset (Settings → My Fire TV → Reset to Factory Defaults) brings everything back.

Fire OS protects a few of these (on the test Stick: crash reports, two diagnostics services, and ad deep-links). The script says so and leaves them on. If Fire OS refuses for another reason, it offers to remove the app for your profile instead (`pm uninstall --user 0`), which option 5 can undo.

### Tested on

A Fire TV Stick 4K (model AFTKRT, Fire OS 8.1.8.5) with 14 apps installed:
- 610 MB of storage freed (400 MB of cache and 3 unused apps), plus a 66 MB leftover installer found.
- 27 Amazon parts turned off. Free RAM went up even before a restart.
- The home screen, voice search, the Appstore and all the streaming apps kept working.

## 3. Make it look cleaner (on the TV, 2 minutes)

ADB can't change these settings, so set them with the remote:

- **Stop autoplaying trailers:** Settings → Preferences → **Featured Content** → turn off *Allow Video Autoplay* and *Allow Audio Autoplay*.
- **Fewer targeted ads:** Settings → Preferences → **Privacy Settings** → turn off *Device Usage Data*, *Collect App Usage Data*, and *Interest-based Ads*.
- **Quieter notifications:** Settings → Preferences → **Notification Settings** → turn off notifications for apps you don't want hearing from.
- **Put your favorite apps first:** hold **Home** → **Apps**, highlight an app, press **☰ (menu)** → *Move to front*. Do your least favorite first and your top favorite last, so it ends up first. Amazon doesn't let a PC set this order.
- **Delete leftover installers:** open **Downloader** → **Files**, select the `.apk` file, and choose **Delete**.
- **Restart after cleaning:** Settings → My Fire TV → **Restart**, so the Stick starts without what you turned off.
- **When you're done:** turn **ADB debugging** or **Wireless debugging** back off in Developer options, so other devices on your Wi-Fi can't connect to the Stick.
- **Less storage creep:** Settings → Applications → **Manage Installed Applications** shows what's using space, if you want to check without a PC.

### Want a fully ad-free home screen?

On Fire OS 7.6 and later, Amazon blocks replacing its home screen. What you can do is install a launcher app such as Projectivy Launcher or Wolf Launcher from the Amazon Appstore and open it as your main screen. Free My TV can also run on the Stick as an app this way. Pressing Home will still go back to Amazon's screen, though, so expect a workaround rather than a full replacement.
