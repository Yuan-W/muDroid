MuDroid
======

MuDroid is a mutation testing tool for Android testing in integeration level.

Requirements
------

MuDroid requires Pillow and pexpect installed. MuDroid was tested with Python 2.7, Pillow 3.1.1 and pexpect 4.0.1.

Usage
------

1. Run `python mudroid.py <apk file>` for full mutation testing.

2. Run `python mutant_generator.py <apk file>` for mutants generation only.

3. Run `python interaction_simulator.py <mutants dir>` to simulate user input and get screenshots.

4. Run `python result_analyzer.py <screenshots dir>` to analyze result and generate report.

5.(Optional) Run `python report_generator.py <mutants dir>` to generate html report from mutants json file.

Example
------
__Warning:__ The test suite is only suitable for Android devices/emulators with a 1920x1200 resolution(Preferably Nexus 7 2013 device or equivalent emulator).

An example for CleanCalculator with a sample test suite was included in this repository. To run the example, execute the shell script under example directory and then run `python mudroid.py CleanCalculator.apk` in the main directory. The screenshots and html report will be put under `CleanCalculator/report` folder.