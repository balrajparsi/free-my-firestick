#!/bin/bash
# Free My Fire Stick for macOS and Linux. On a Mac, double-click this file in Finder
# (the first time: right-click > Open, since it isn't from the App Store).
cd "$(dirname "$0")" || exit 1
if ! command -v python3 >/dev/null 2>&1; then
  echo "Python 3 is needed. On a Mac, run:  xcode-select --install   (or: brew install python), then try again."
  read -r -p "Press Enter to close." _; exit 1
fi
python3 firestick.py "$@"
status=$?
[ -t 0 ] && read -r -p "Press Enter to close." _
exit $status
