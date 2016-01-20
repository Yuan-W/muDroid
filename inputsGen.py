import sys, getopt
import random

eventType = ['tap', 'swipe', 'text']
testString = 'Hello'

def randomCommand(width, height):
    event = random.randint(0, 0)
    command = ''
    if event == 0:
        x = random.randint(0, width)
        y = random.randint(0, height)
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


if __name__ == "__main__":
    if (len(sys.argv)) != 4:
        print 'Usage: inputGen.py <number of events> <screen width> <screen height>'
        sys.exit(2)
    number = int(sys.argv[1])
    width = int(sys.argv[2])
    height = int(sys.argv[3])
    commandList = []
    for i in range(0, number):
        c = randomCommand(width, height)
        print c
        commandList.append(c)
    f = open("commands.txt", "w")
    for c in commandList:
        f.write("%s\n" % c)

    