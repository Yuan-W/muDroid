#!/usr/local/bin/python

import argparse
import os, sys, getopt
import subprocess
import random

eventType = ['tap', 'swipe', 'text']
testString = 'Hello'

def randomCommand(width, height):
    event = random.randint(0, 0)
    command = ''
    if event == 0:
        x = random.randint(0, width)
        y = random.randint(60, height)
        command = '{} {} {}'.format(eventType[event], x, y)
    elif event == 1:
        x1 = random.randint(0, width)
        y1 = random.randint(0, height)
        x2 = random.randint(0, width)
        y2 = random.randint(0, height)
        command = '{} {} {} {} {}'.format(eventType[event], x1, y1, x2, y2)
    elif event == 2:
        command = '{} {}'.format(eventType[event], testString)
    return command

def generateCommands(number, height, width, output_dir=''):
    commandList = []

    for i in range(0, number):
        c = randomCommand(width, height)
        # print c
        commandList.append(c)

    if output_dir == '':
        f = open("commands", "w")
    else:
        f = open(os.path.join(output_dir, 'commands'), 'w')
    
    for c in commandList:
        f.write("%s\n" % c)

def usage():
    print 'usage: generate [-c] <number of events> <screen width> <screen height>'

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='generate screen events.')
    parser.add_argument('-a', '--auto', help='auto detect screen resolution', action='store_true')
    parser.add_argument("number", help="mumber of events to generate", type=int)
    parser.add_argument('width', type=int, nargs='?', help='max width in pixel', default=1200)
    parser.add_argument('height', type=int, nargs='?', help='max height in pixel', default=1920)

    args = parser.parse_args()
    if(args.auto):
        output = subprocess.check_output(['adb shell dumpsys window | grep "mUnrestrictedScreen"'], shell=True)
        res = output.split(' ')[-1].split('x')
        width = int(res[0])
        height = int(res[1])
        print 'Screen Resolution: %dx%d' % (width, height)
    else:
        width = args.width
        height = args.height

    generateCommands(args.number, height, width)

    