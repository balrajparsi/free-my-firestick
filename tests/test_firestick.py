"""Offline tests: a fake Fire TV answers like the Fire TV Stick 4K (Fire OS 8.1) did. No device or adb needed."""
import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import firestick as fs  # noqa: E402

DF = ("Filesystem      1K-blocks    Used Available Use% Mounted on\n"
      "/dev/block/dm-6\n               12671508 4154052   8370000  34% /data")
DISKSTATS = ('Latency: 1ms\nPackage Names: ["com.netflix.ninja","com.amazon.hedwig","com.gone.app"]\n'
             "App Sizes: [104857600,2048,10]\nApp Data Sizes: [52428800,0,10]\nCache Sizes: [209715200,1024,10]")
PACKAGES = "package:com.netflix.ninja\npackage:com.amazon.hedwig\npackage:com.amazon.device.crashmanager"
USER = ("package:com.netflix.ninja\npackage:com.amazon.tv.settings.v2.overlay.localisation.common\n"
        "package:com.esaba.downloader")
FIND = "-rw------- 1 u0_a225 u0_a225 68737694 2026-01-09 18:58 /sdcard/Download/Downloader/My App.apk"


class FakeTV:
    def __init__(self):
        self.calls = []

    def __call__(self, *args):
        self.calls.append(args)
        cmd = args[-1]
        if cmd.startswith("df"):
            return DF
        if cmd == "dumpsys diskstats":
            return DISKSTATS
        if cmd == "pm list packages -3":
            return USER
        if cmd.startswith("pm list packages"):
            return PACKAGES
        if cmd.startswith("find"):
            return FIND
        if cmd == "pm disable-user --user 0 com.amazon.device.crashmanager":
            return ("Exception occurred while executing 'disable-user':\njava.lang.SecurityException: "
                    "Cannot disable a protected package: com.amazon.device.crashmanager")
        if cmd.startswith("pm disable-user"):
            return f"Package {cmd.split()[-1]} new state: disabled-user"
        return ""


class Tests(unittest.TestCase):
    def setUp(self):
        self.fake = FakeTV()
        self.tv = fs.FireTV("adb", "tv:5555", runner=self.fake)

    def test_free_space_survives_wrapped_df(self):
        total, used, free = self.tv.free_space()
        self.assertEqual(free, 8370000 * 1024)
        self.assertEqual(total, 12671508 * 1024)

    def test_user_apps_skip_overlays(self):
        self.assertEqual(self.tv.user_apps(), ["com.esaba.downloader", "com.netflix.ninja"])

    def test_app_sizes(self):
        self.assertEqual(self.tv.app_sizes()["com.netflix.ninja"], (104857600, 52428800, 209715200))

    def test_leftover_installers_keep_spaces_in_names(self):
        self.assertEqual(self.tv.leftover_installers(),
                         [(68737694, "/sdcard/Download/Downloader/My App.apk")])
        self.assertIn("/sdcard/ ", self.fake.calls[-1][-1])  # trailing slash: /sdcard is a symlink

    def test_disable_and_protected(self):
        self.assertEqual(self.tv.disable("com.amazon.hedwig"), "disabled")
        self.assertEqual(self.tv.disable("com.amazon.device.crashmanager"), "protected")

    def test_never_touches_protected_list(self):
        self.assertEqual(self.tv.disable("com.amazon.tv.launcher"), "protected")
        self.assertFalse(any("launcher" in c[-1] for c in self.fake.calls))

    def test_record_reads_powershell_bom_and_single_object(self):
        with tempfile.TemporaryDirectory() as d:
            fs.RECORD = Path(d) / "rec.json"
            fs.RECORD.write_text("\ufeff" + json.dumps({"Package": "com.amazon.hedwig", "Method": "disable"}),
                                 encoding="utf-8")
            self.assertEqual(fs.read_record()[0]["Package"], "com.amazon.hedwig")
            fs.remember({"Package": "global window_animation_scale", "Method": "setting", "Value": "1.0"})
            self.assertEqual(len(fs.read_record()), 2)

    def test_every_extra_package_is_unique_and_not_protected(self):
        pkgs = [p for g in fs.EXTRA_GROUPS for p in g["packages"]]
        self.assertEqual(len(pkgs), len(set(pkgs)))
        self.assertFalse(set(pkgs) & fs.PROTECTED)


if __name__ == "__main__":
    unittest.main()
