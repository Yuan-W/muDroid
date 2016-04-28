MuDroid
======

MuDroid is a mutation testing tool for Android testing in integeration level.

Usage
------

1. Run `python mudroid.py <apk file>` for full mutation testing.

2. Run `python mutant_generator.py <apk file>` for mutants generation only.

3. Run `python interaction_simulator.py <mutants dir>` to simulate user input and get screenshots.

4. Run `python result_analyzer.py <screenshots dir>` to analyze result and generate report.