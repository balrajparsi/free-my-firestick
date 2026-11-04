# Free My Fire Stick

Free up space on your Amazon Fire TV Stick and make it look cleaner. It runs from your Windows PC over Wi-Fi with ADB. You don't need root, and everything it turns off can be turned back on.

Inspired by [Free My TV](https://github.com/simbasjungles/free-my-tv). MIT licensed.

## Why not Free My TV?

[Free My TV](https://github.com/simbasjungles/free-my-tv) installs on a Fire Stick, but only as an app you open. Amazon's home screen keeps the Home button, and the project won't turn off any Amazon app. It also doesn't free any space, because it's a home screen, not a cleaner. This tool covers the part it leaves out.

## 1. One-time setup

**On the Fire Stick**
1. Settings → **My Fire TV** → **About** → select your device name **7 times** until it says you're a developer.
2. Settings → My Fire TV → **Developer options** → turn on **ADB debugging**.
3. Settings → My Fire TV → About → **Network**: write down the **IP address** (e.g. `192.168.1.50`).

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

| Option | What it does | Risk |
|---|---|---|
| 1 Storage report | Free space, the 20 biggest apps, total cache size | None |
| 2 Clear all caches | Deletes temporary cache files for every app | None (apps stay signed in) |
| 3 Remove apps you installed | Lists your apps with their sizes and uninstalls the ones you pick, asking for each one | Deletes that app's data |
| 4 Turn off Amazon extras | Asks about each optional ad/telemetry app (Special Offers ads, deals, promo notifications, metrics, crash uploads, Photos, GameCircle, Fling) | Low. Saved to `firestick-turned-off.json` |
| 5 Restore extras | Turns back on everything option 4 turned off | None |

It never touches the Amazon home screen, Settings, Wi-Fi, the keyboard, inputs, or system updates. If you lose `firestick-turned-off.json`, an Amazon reset (Settings → My Fire TV → Reset to Factory Defaults) brings everything back.

Note: newer Fire OS versions block turning off some Amazon apps. When that happens, the script asks whether to remove the app for your profile instead (`pm uninstall --user 0`), which option 5 can undo. If both are blocked, it skips the app.

## 3. Make it look cleaner (on the TV, 2 minutes)

ADB can't change these settings, so set them with the remote:

- **Stop autoplaying trailers:** Settings → Preferences → **Featured Content** → turn off *Allow Video Autoplay* and *Allow Audio Autoplay*.
- **Fewer targeted ads:** Settings → Preferences → **Privacy Settings** → turn off *Device Usage Data*, *Collect App Usage Data*, and *Interest-based Ads*.
- **Quieter notifications:** Settings → Preferences → **Notification Settings** → turn off notifications for apps you don't want hearing from.
- **Tidy the top row:** on the home screen, hold the **☰ (menu)** button on an app → *Move* or *Remove from Favorites*, so only the apps you use are on the main row.
- **Less storage creep:** Settings → Applications → **Manage Installed Applications** shows what's using space, if you want to check without a PC.

### Want a fully ad-free home screen?

On Fire OS 7.6 and later, Amazon blocks replacing its home screen. What you can do is install a launcher app such as Projectivy Launcher or Wolf Launcher from the Amazon Appstore and open it as your main screen. Free My TV can also run on the Stick as an app this way. Pressing Home will still go back to Amazon's screen, though, so expect a workaround rather than a full replacement.
