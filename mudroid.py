#!/usr/bin/python

import sys, os, glob
from time import sleep
from PIL import Image, ImageChops
import pexpect
import subprocess

id = 1
intArithmeticOperator=['add-int', 'rsub-int', 'div-int', 'mul-int', 'rem-int']

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

def captureScreen(imageName):
    command = ['adb', 'shell', "screencap -p /sdcard/{}".format(imageName)]
    subprocess.call(command)
    command = ['adb', 'pull', '/sdcard/{}'.format(imageName)]
    subprocess.call(command)
    command = ['adb', 'shell', 'rm /sdcard/{}'.format(imageName)]
    subprocess.call(command)

def executeApk(fileName):
    command = ['adb', 'uninstall', 'com.example']
    subprocess.call(command)
    command = ['adb', 'install', fileName]
    subprocess.call(command)
    command = ['adb', 'shell', 'am start -n com.example/.activity.MainActivity']
    subprocess.call(command)
    sleep(1)
    captureScreen(fileName+'_start.png')
    command = ['adb', 'shell', 'input tap 100 400']
    subprocess.call(command)
    captureScreen(fileName+'_click.png')


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

scrPath="com.example"
apkName = "simple_test.apk"
executeApk(apkName)
decompress(apkName,True)
original_start = Image.open("{}_start.png".format(apkName))
original_click = Image.open("{}_click.png".format(apkName))

path = os.path.join(apkName[:-4], 'smali', *scrPath.split('.'))
operator_list=[]
for root, dirs, files in os.walk(path):
    for f in files:
        if f.endswith(".smali"):
            operator_list += checkArithmeticOperator(os.path.join(root, f))

for o in operator_list:
    print o
    ininstrument(o['file'], o['line_num'], o['mutant'])
    newApk = compress(apkName.split('.')[0], o['id'])
    signApk(newApk)
    executeApk(newApk)
    instrumented_start = Image.open("{}_start.png".format(newApk))
    instrumented_click = Image.open("{}_click.png".format(newApk))
    diff_start = ImageChops.difference(original_start, ininstrumented_start)
    print "Start Diff: ", diff_start.getbbox()
    diff_click = ImageChops.difference(original_click, ininstrumented_click)
    print "Click Diff: ", diff_click.getbbox()



