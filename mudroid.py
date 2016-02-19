#!/usr/local/bin/python

import sys, os, glob
from time import sleep, strftime
from PIL import Image, ImageChops
import pexpect
from xml.etree import ElementTree
import subprocess
from mutation_analyser import MutationAnalyser

DIFF_THRESHOLD = 5

def checkSimilarPictures(pic1, pic2, x_max=DIFF_THRESHOLD, y_max=DIFF_THRESHOLD):
    image1 = Image.open(pic1)
    image2 = Image.open(pic2)
    # print pic1, pic2
    diff = ImageChops.difference(image1, image2)
    box = diff.getbbox()
    if box is None:
        return True
    xdiff = abs(box[0] - box[2])
    ydiff = abs(box[1] - box[3])
    if(xdiff >= x_max or ydiff >= y_max):
        return False
    return False

def readAndroidManifest(source_directory):
    manifest = ElementTree.parse(os.path.join(source_directory, 'AndroidManifest.xml')).getroot()
    package = manifest.get('package')
    activities = manifest.find('application').findall('activity')
    for activity in activities:
        if 'android.intent.action.MAIN' in ElementTree.tostring(activity):
            start_activity = activity.get('{http://schemas.android.com/apk/res/android}name')
    start_activity = start_activity.replace(package, '')
    return package, start_activity

def compress(file_path, id):
    output = os.path.join(file_path, '{}_{}.apk'.format(file_path, id))
    command = ["./apktool", "b", os.path.join(file_path, 'src'), '-o{}'.format(output)]
    subprocess.call(command)
    return output

def decompress(file_path, is_force=False):
    source_directory = os.path.join(file_path[:-4], 'src')
    command = ["./apktool", "d", file_path, '-o%s' % source_directory]
    if is_force:
        command.append('-f')
    subprocess.call(command)
    return source_directory

def signApk(file_path):
    child = pexpect.spawn('jarsigner -verbose -keystore debug.keystore {} testKey'.format(file_path))
    child.expect('Enter Passphrase for keystore:')
    child.sendline('123456')
    child.expect('jar signed')

def captureScreen(pic_name, path):
    image_path = os.path.join(path, pic_name)
    device_path = '/sdcard/%s' % pic_name

    command = ['adb', 'shell', "screencap -p", device_path]
    subprocess.call(command)
    command = ['adb', 'pull', device_path, image_path]
    subprocess.call(command)
    command = ['adb', 'shell', 'rm', device_path]
    subprocess.call(command)
    img = Image.open(image_path)
    w, h = img.size
    img.crop((0, 80, w, h)).save(image_path)
    return image_path

def executeApk(package, start_activity, file_path, command_list, img_path):

    # effective_commands = []

    command = ['adb', 'uninstall', package]
    subprocess.call(command)
    command = ['adb', 'install', file_path]
    subprocess.call(command)
    command = ['adb', 'shell', 'am start -n %s/%s' % (package, start_activity)]
    subprocess.call(command)
    sleep(1)

    file_name = os.path.basename(file_path)
    img1 = captureScreen('%s_0.png' % file_name, img_path)

    for i, c in enumerate(command_list):
        command = ['adb', 'shell', 'input', c]
        print '%d %s' % (i+1, command)
        subprocess.call(command)

        pic = '%s_%d.png' % (file_name, i+1)
        img2 = captureScreen(pic, img_path)
        # sleep(0.1)
        while not os.path.isfile(img2):
            sleep(0.1)
        if(checkSimilarPictures(img1, img2)):
            # os.remove(img2)
            print pic
        else:
            img1 = img2
            # effective_commands.append(c)
            # break

    # return list(set(effective_commands))

def instrument(file_path, line, mutant):
    with open(file_path) as f:
        content = f.readlines()
    original = list(content)
    content[line-1] = mutant
    with open(file_path, 'w') as f:
        f.writelines(content)
    return original


class ReportGenerator():
    @staticmethod
    def writeTable(outputFile, elements, is_header=False):
        outputFile.write('<tr>\n')
        for e in elements:
            if is_header:
                outputFile.write('<th>%s</th>\n' % e)
            else:
                outputFile.write('<td>%s</td>\n' % e)
        outputFile.write('</tr>\n')

    @staticmethod
    def generateReport(operators, report_path):
        report = open("%s/result.html" % report_path, "w")
        report.write('''<style>
        table {
            border-collapse: collapse;
        }

        table, td, th {
            border: 1px solid black;
        }
        </style>''')
        report.write('<table>\n')
        ReportGenerator.writeTable(report, ['Id', 'Operator', 'Type', 'File', 'Line', 'Method', 'Original', 'Mutant', 'Killed'], True)
        o2 = {'line_num': ''}
        for o in operators:
            if o2['line_num'] == o['line_num']:
                ReportGenerator.writeTable(report, [o['id'], '', '', '', '', '', o['line'], o['mutant'], o['killed']])
            else:
                ReportGenerator.writeTable(report, [o['id'], o['operator'], o['operator_type'], o['file'], o['line_num'], o['method'], o['line'], o['mutant'], o['killed']])
            o2 = o
        report.write('</table>\n')

if __name__ == "__main__":
    if (len(sys.argv)) != 2:
        print 'Usage: mudroid.py <apk>'
        sys.exit(2)
    apk_file = sys.argv[1]
    if not apk_file.endswith('.apk'):
        print 'Input must be an Android Apk file!'
        sys.exit(2)

    effective_commands = []
    command_list = [line.rstrip('\n') for line in open('commands.txt')]

    report_path = os.path.join(apk_file[:-4], 'report', strftime('%Y%m%d%H%M%S'))
    os.makedirs(report_path)

    source_directory = decompress(apk_file, True)

    package, start_activity = readAndroidManifest(source_directory)

    # effective_commands += list(set(executeApk(package, start_activity, apk_file, command_list, report_path)) - set(effective_commands))

    # path = os.path.join(source_directory, 'smali')
    path = os.path.join(source_directory, 'smali', *package.split('.')) #TODO: Take paramater or read from file
    mutation_analyser = MutationAnalyser()
    operator_list = mutation_analyser.checkMutations(path)
                
    print len(operator_list)

    # for o in operator_list:
    #     file_original = instrument(o['file'], o['line_num'], o['mutant'])
    #     new_apk_path = compress(apk_file.split('.')[0], o['id'])
    #     with open(o['file'], 'w') as f:
    #         f.writelines(file_original)
    #     signApk(new_apk_path)

    #     effective_commands += list(set(executeApk(package, start_activity, new_apk_path, command_list, report_path)) - set(effective_commands))

    #     for i in range(0, len(command_list)+1):
    #         original_image = "{}/{}_{}.png".format(report_path, apk_file, i)
    #         instrumented_image = "{}/{}_{}.png".format(report_path, os.path.basename(new_apk_path), i)
    #         if(not checkSimilarPictures(original_image, instrumented_image)):
    #             o['killed'] = True
    #             break

    # seed = open("seed.txt", "w")
    # for c in effective_commands:
    #     seed.write("%s\n" % c)

    ReportGenerator.generateReport(operator_list, report_path)


