#!/usr/local/bin/python

import argparse
import sys, os, glob
from mutation_analyser import MutationAnalyser
from mutants_generator import generateMutants
from inputs_generator import generateCommands
from interaction_simulator import simulate
from result_analyzer import analyze_results


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('apk', help='apk file')
    args = parser.parse_args()

    apk_file = args.apk
    if not apk_file.endswith('.apk'):
        print 'Input must be an Android Apk file!'
        sys.exit(2)

    file_name = apk_file[:-4]

    if not os.path.exists(os.path.join(file_name, 'commands')):
        if not os.path.exists(file_name):
            os.mkdir(file_name)
        print 'Command list does not exist!'
        height = input('Please enter maximum height of command:')
        width = input('Please enter maximum width of command:')
        number = input('Please enter total number of commands:')
        generateCommands(number, height, width, file_name)

    directory = generateMutants(apk_file)
    result_directory = simulate(directory)
    analyze_results(file_name, result_directory)
