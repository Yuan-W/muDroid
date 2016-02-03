#!/usr/bin/python

import sys, os, glob
from time import sleep, strftime
from PIL import Image, ImageChops
import pexpect
from xml.etree import ElementTree
import subprocess

id = 1
DIFF_THRESHOLD = 10
arithmeticOperator=['add-', 'rsub-', 'div-', 'mul-', 'rem-']
relationalOperator=['if-eq', 'if-ne', 'if-lt', 'if-ge', 'if-gt', 'if-le']
logicalConnector=[]
unaryOperator=['not-', 'neg-']

def checkSimilarPictures(pic1, pic2, xMax=DIFF_THRESHOLD, yMax=DIFF_THRESHOLD):
    image1 = Image.open(pic1)
    image2 = Image.open(pic2)
    # print pic1, pic2
    diff = ImageChops.difference(image1, image2)
    box = diff.getbbox()
    if box is None:
        return True
    xdiff = abs(box[0] - box[2])
    ydiff = abs(box[1] - box[3])
    if(xdiff >= xMax or ydiff >= yMax):
        return False
    return True

def compress(fileName, id):
    output = '{}_{}.apk'.format(fileName, id)
    command = ["apktool", "b", fileName, '-o{}'.format(output)]
    subprocess.call(command)
    return output

def decompress(fileName, isForce=False):
    command = ["apktool", "d", fileName]
    if isForce:
        command.append('-f')
    subprocess.call(command)

def signApk(fileName):
    child = pexpect.spawn('jarsigner -verbose -keystore debug.keystore {} testKey'.format(fileName))
    child.expect('Enter Passphrase for keystore:')
    child.sendline('123456')
    child.expect('jar signed')

def captureScreen(picName, path):
    imagePath = '%s/%s' % (path, picName)
    devicePath = '/sdcard/%s' % picName

    command = ['adb', 'shell', "screencap -p", devicePath]
    subprocess.call(command)
    command = ['adb', 'pull', devicePath, imagePath]
    subprocess.call(command)
    command = ['adb', 'shell', 'rm', devicePath]
    subprocess.call(command)
    img = Image.open(imagePath)
    w, h = img.size
    img.crop((0, 80, w, h)).save(imagePath)
    return imagePath

def executeApk(package, startActivity, fileName, commandList, path):

    effective_commands = []

    command = ['adb', 'uninstall', package]
    subprocess.call(command)
    command = ['adb', 'install', fileName]
    subprocess.call(command)
    command = ['adb', 'shell', 'am start -n %s/%s' % (package, startActivity)]
    subprocess.call(command)
    sleep(1)

    img1 = captureScreen('%s_0.png' % fileName, path)

    for i, c in enumerate(commandList):
        command = ['adb', 'shell', 'input', c]
        print '%d %s' % (i+1, command)
        subprocess.call(command)

        pic = '%s_%d.png' % (fileName, i+1)
        img2 = captureScreen(pic, path)
        # sleep(0.1)
        while not os.path.isfile(img2):
            sleep(0.1)
        if(checkSimilarPictures(img1, img2)):
            os.remove(img2)
        else:
            img1 = img2
            effective_commands.append(c)
            # break

    return list(set(effective_commands))


def instrument(fileName, line, mutant):
    with open(fileName) as f:
        content = f.readlines()
    content[line-1] = mutant
    with open(fileName, 'w') as f:
        f.writelines(content)

def replaceOperator(original, operators):
    mutant_list = []
    original_operator = original['operator']
    if original_operator in operators:
        mutantion_operator_list = [operator for operator in operators if operator != original_operator]
        for mutant in mutantion_operator_list:
            original['mutant'] = original['line'].replace(original_operator, mutant)
            global id
            original['id'] = id
            id = id + 1
            mutant_list.append(original.copy())
    return mutant_list

def checkOperator(fileName, operators):
    operator_list = []
    method = []
    with open(fileName) as f:
        for num, line in enumerate(f, 1):
            if '.method' in line:
                method = line
            for operator in operators:
                if operator in line:
                  original_key = {'file': fileName, 'line': line, 'line_num': num, 'operator': operator, 'method': method}
                  mutant_key = replaceOperator(original_key, operators)
                  operator_list += mutant_key        
    return operator_list

def writeTable(outputFile, elements, isHeader=False):
    outputFile.write('<tr>\n')
    for e in elements:
        if isHeader:
            outputFile.write('<th>%s</th>\n' % e)
        else:
            outputFile.write('<td>%s</td>\n' % e)
    outputFile.write('</tr>\n')

def generateReport(operators):
    report = open("%s/result.html" % resultPath, "w")
    report.write('''<style>
    table {
        border-collapse: collapse;
    }

    table, td, th {
        border: 1px solid black;
    }
    </style>''')
    report.write('<table>\n')
    writeTable(report, ['Original', 'File', 'Line', 'Method', 'Mutant', 'Killed'], True)
    o2 = {'line': ''}
    for o in operators:
        if o2['line'] == o['line']:
            writeTable(report, ['', '', '', '', o['mutant'], o['killed']])
        else:
            writeTable(report, [o['line'], o['file'], o['line_num'], o['method'], o['mutant'], o['killed']])
        o2 = o
    report.write('</table>\n')

effective_commands = []
commandList = [line.rstrip('\n') for line in open('commands.txt')]
resultPath = strftime('%Y%m%d%H%M%S')
os.mkdir(resultPath)

apkName = "CleanCalculator.apk"

decompress(apkName,True)

manifest = ElementTree.parse(os.path.join(apkName[:-4], 'AndroidManifest.xml')).getroot()
package = manifest.get('package')

activities = manifest.find('application').findall('activity')
for activity in activities:
    if 'android.intent.action.MAIN' in ElementTree.tostring(activity):
        startActivity = activity.get('{http://schemas.android.com/apk/res/android}name')
startActivity = startActivity.replace(package, '')

effective_commands += list(set(executeApk(package, startActivity, apkName, commandList, resultPath)) - set(effective_commands))

# path = os.path.join(apkName[:-4], 'smali', *package.split('.')) #TODO: Take paramater or read from file
# operator_list=[]
# for root, dirs, files in os.walk(path):
#     for f in files:
#         if f.endswith(".smali"):
#             operator_list += checkOperator(os.path.join(root, f), arithmeticOperator)

# print len(operator_list)

# print operator_list

# for o in operator_list:
#     o['killed'] = False
# #     instrument(o['file'], o['line_num'], o['mutant'])
# #     newApk = compress(apkName.split('.')[0], o['id'])
# #     signApk(newApk)
# #     effective_commands += list(set(executeApk(package, startActivity, newApk, commandList, resultPath)) - set(effective_commands))

# #     for i in range(0, len(commandList)):
# #         original_image = "{}/{}_{}.png".format(resultPath, apkName, i)
# #         instrumented_image = "{}/{}_{}.png".format(resultPath, newApk, i)
# #         if(not checkSimilarPictures(original_image, instrumented_image)):
# #             o['killed'] = True
# #             break

# # seed = open("seed.txt", "w")
# # for c in effective_commands:
# #     seed.write("%s\n" % c)

# generateReport(operator_list)


