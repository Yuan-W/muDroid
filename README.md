MuDroid
======

MuDroid is a mutation testing tool for Android testing in integeration level.

Usage
------

1. Run inputsGen.py first to generate system event in the format of `python inputsGen.py <number of events> <max height> <max width>`. Or `python inputsGen.py -a <number of events>` to auto detect the screen resolution.

2. Run mudroid.py with the apk file apk. `python mudroid.py <apk file>`