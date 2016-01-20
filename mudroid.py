#!/usr/bin/python

import sys, os, glob
from time import sleep, strftime
from PIL import Image, ImageChops
import pexpect
import subprocess

id = 1
DIFF_THRESHOLD = 10
intArithmeticOperator=['add-int', 'rsub-int', 'div-int', 'mul-int', 'rem-int']

def checkSimilarPictures(pic1, pic2, xMax=DIFF_THRESHOLD, yMax=DIFF_THRESHOLD):
    image1 = Image.open(pic1)
    image2 = Image.open(pic2)
    print pic1, pic2
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
    return imagePath

def executeApk(fileName, commandList, path):
    command = ['adb', 'uninstall', 'com.example']
    subprocess.call(command)
    command = ['adb', 'install', fileName]
    subprocess.call(command)
    command = ['adb', 'shell', 'am start -n com.example/.activity.MainActivity']
    subprocess.call(command)
    sleep(1)

    img1 = captureScreen('%s_0.png' % fileName, path)

    for i, c in enumerate(commandList):
        command = ['adb', 'shell', 'input', c]
        print '%d %s' % (i+1, command)
        subprocess.call(command)

        pic = '%s_%d.png' % (fileName, i+1)
        print pic
        img2 = captureScreen(pic, path)
        # sleep(0.1)
        while not os.path.isfile(img2):
            sleep(0.1)
        if(checkSimilarPictures(img1, img2)):
            os.remove(img2)
        else:
            img1 = img2


def instrument(fileName, line, mutant):
    with open(fileName) as f:
        content = f.readlines()
    content[line-1] = mutant
    with open(fileName, 'w') as f:
        f.writelines(content)

def replaceArithmeticOperator(original):
    mutant_list = []
    original_operator = original['operator']
    if original_operator in intArithmeticOperator:
        mutantion_operator_list = [operator for operator in intArithmeticOperator if operator != original_operator]
        for mutant in mutantion_operator_list:
            original['mutant'] = original['line'].replace(original_operator, mutant)
            global id
            original['id'] = id
            id = id + 1
            mutant_list.append(original.copy())
    return mutant_list

def checkArithmeticOperator(fileName):
    operator_list = []
    with open(fileName) as f:
        for num, line in enumerate(f, 1):
            for operator in intArithmeticOperator:
                if operator in line:
                  original_key = {'file': fileName, 'line': line, 'line_num': num, 'operator': operator}
                  mutant_key = replaceArithmeticOperator(original_key)
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


commandList = [line.rstrip('\n') for line in open('commands.txt')]
resultPath = strftime('%Y%m%d%H%M%S')
os.mkdir(resultPath)

scrPath="com.example"
apkName = "simple_test.apk"
executeApk(apkName, commandList, resultPath)
decompress(apkName,True)

path = os.path.join(apkName[:-4], 'smali', *scrPath.split('.'))
operator_list=[]
for root, dirs, files in os.walk(path):
    for f in files:
        if f.endswith(".smali"):
            operator_list += checkArithmeticOperator(os.path.join(root, f))

for o in operator_list:
    # print o
    o['killed'] = False
    instrument(o['file'], o['line_num'], o['mutant'])
    newApk = compress(apkName.split('.')[0], o['id'])
    signApk(newApk)
    executeApk(newApk, commandList, resultPath)
    for i in range(0, len(commandList)):
        print i
        original_image = "{}/{}_{}.png".format(resultPath, apkName, i)
        instrumented_image = "{}/{}_{}.png".format(resultPath, newApk, i)
        if(not checkSimilarPictures(original_image, instrumented_image)):
            o['killed'] = True
            break

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
writeTable(report, ['Mutant', 'Original', 'File', 'Killed'], True)
for o in operator_list:
    writeTable(report, [o['mutant'], o['line'], o['file'], o['killed']])
report.write('</table>\n')


