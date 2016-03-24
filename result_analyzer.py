#!/usr/local/bin/python

import sys, os, json
from report_generator import ReportGenerator
from image_checker import checkSimilarPictures

def analyze_results(file_name, directory):
    mutants_list = os.path.join(directory, 'mutants')
    with open(mutants_list, 'rb') as handle:
        mutants = json.load(handle)

    for m in mutants:
        index = 0
        print m['id']
        instrumented_image = os.path.join(directory, '%s_%d.apk_%d.png' % (file_name, m['id'], index))
        print instrumented_image
        while(os.path.exists(instrumented_image)):
            original_image = os.path.join(directory, '%s.apk_%d.png' % (file_name, index))
            print original_image, instrumented_image
            if not checkSimilarPictures(original_image, instrumented_image):
                m['killed'] = True
                break
            index += 1
            instrumented_image = os.path.join(directory, '%s_%d.apk_%d.png' % (file_name, m['id'], index))

    with open(mutants_list, 'wb') as handle:
        json.dump(mutants, handle)

    ReportGenerator.generateReport(mutants, directory)

if __name__ == "__main__":
    directory = sys.argv[1]
    file_name = sys.argv[2]

    analyze_results(file_name, directory)
