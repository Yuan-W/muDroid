#!/usr/local/bin/python

import argparse
import sys, os, glob
import json
from time import sleep, strftime
from PIL import Image
import subprocess
from inputs_generator import generateCommands
from image_checker import checkSimilarPictures

EVENTS_PER_IMAGE = 1
APP_START_DELAY = 2
STATUS_BAR_CROP_HEIGHT = 80
SCREEN_CPATURE_DELAY = 0

def captureScreen(pic_name, path):
    image_path = os.path.join(path, pic_name)
    device_path = '/sdcard/%s' % pic_name

    command = ['adb', 'shell', "screencap -p", device_path]
    subprocess.call(command)
    command = ['adb', 'pull', device_path, image_path]
    subprocess.call(command)

    while not os.path.isfile(image_path):
        sleep(0.1)

    command = ['adb', 'shell', 'rm', device_path]
    subprocess.call(command)
    img = Image.open(image_path)
    w, h = img.size
    img.crop((0, STATUS_BAR_CROP_HEIGHT, w, h)).save(image_path)
    return image_path

def executeOriginal(package, start_activity, file_path, img_path, commands):
    executeApk(package, start_activity, file_path, img_path)
    file_name = os.path.basename(file_path)
    img_index = 1
    for i, c in enumerate(commands):
        executeCommand(c)
        if ((i+1) % EVENTS_PER_IMAGE) == 0:
            sleep(SCREEN_CPATURE_DELAY)
            img_name = '%s_%d.png' % (file_name, img_index)
            img = captureScreen(img_name, img_path)
            img_index += 1           

def executeMutant(package, start_activity, original_apk, file_path, img_path, commands):
    executeApk(package, start_activity, file_path, img_path)
    original_image = "{}/{}_0.png".format(img_path, original_apk)
    instrumented_image = "{}/{}_0.png".format(img_path, os.path.basename(file_path))

    similar, crashed = checkSimilarPictures(original_image, instrumented_image)
    if(not similar):
        return True, crashed

    img_index = 1
    for i, c in enumerate(commands):
        executeCommand(c)

        if ((i+1) % EVENTS_PER_IMAGE) == 0:
            sleep(SCREEN_CPATURE_DELAY)
            img_name= "{}_{}.png".format(os.path.basename(file_path), img_index)
            instrumented_image = captureScreen(img_name, img_path)
            original_image = "{}/{}_{}.png".format(img_path, original_apk, img_index)
            img_index += 1
            similar, crashed = checkSimilarPictures(original_image, instrumented_image)
            if(not similar):
                return True, crashed

    if (len(commands) % EVENTS_PER_IMAGE) != 0:
        sleep(SCREEN_CPATURE_DELAY)
        img_name= "{}_{}.png".format(os.path.basename(file_path), img_index)
        instrumented_image = captureScreen(img_name, img_path)
        original_image = "{}/{}_{}.png".format(img_path, original_apk, img_index)
        similar, crashed = checkSimilarPictures(original_image, instrumented_image)
        if(not similar):
            return True, similar
    return False, crashed

def executeApk(package, start_activity, file_path, img_path):
    command = ['adb', 'uninstall', package]
    subprocess.call(command)
    command = ['adb', 'install', file_path]
    subprocess.call(command)
    command = ['adb', 'shell', 'am start -n %s/%s' % (package, start_activity)]
    subprocess.call(command)
    sleep(APP_START_DELAY)

    file_name = os.path.basename(file_path)
    img = captureScreen('%s_0.png' % file_name, img_path)

def executeCommand(command):
    c = ['adb', 'shell', 'input', command]
    subprocess.call(c)

def simulate(directory):
    config_file = os.path.join(directory, 'config')
    mutants_list = os.path.join(directory, 'mutants')
    commands_list = os.path.join(directory, 'commands')

    if not os.path.exists(config_file):
        print 'Config file does not exist! Please run mutants generator first.'
        sys.exit(2)
    if not os.path.exists(mutants_list):
        print 'Mutants list does not exist! Please run mutants generator first.'
        sys.exit(2)

    with open(config_file, 'rb') as handle:
        config = json.load(handle)

    with open(mutants_list, 'rb') as handle:
        mutants = json.load(handle)

    if not os.path.exists(commands_list):
        generateCommands(100, 1800, 1200, directory)

    commands = [line.rstrip('\n') for line in open(commands_list)]
    report_path = os.path.join(config['file'], 'report', strftime('%Y%m%d%H%M%S'))
    os.makedirs(report_path)
    
    original_apk = config['file']+'.apk'

    executeOriginal(config['package'], config['start_activity'], original_apk, report_path, commands)

    for m in mutants:
        new_apk_path = os.path.join(directory, '{}_{}.apk'.format(config['file'], m['id']))
        m['killed'], m['crashed'] = executeMutant(config['package'], config['start_activity'], original_apk, new_apk_path, report_path, commands)
        print m['id'], m['killed']

    new_mutants_list = os.path.join(report_path, 'mutants')
    with open(new_mutants_list, 'wb') as handle:
        json.dump(mutants, handle)

    return report_path

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('dir', help='Directory contains apk mutants.')
    args = parser.parse_args()

    commands_list = os.path.join(args.dir, 'commands')
    if not os.path.exists(commands_list):
        print 'Command list does not exist!'
        height = input('Please enter maximum height of command:')
        width = input('Please enter maximum width of command:')
        number = input('Please enter total number of commands:')
        generateCommands(number, height, width, args.dir)

    commands = [line.rstrip('\n') for line in open(commands_list)]

    simulate(args.dir)