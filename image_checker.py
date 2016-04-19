#!/usr/local/bin/python
from PIL import Image, ImageChops
import math

DIFF_THRESHOLD = 10
CRASH_THRESHOLD = 1000
RMS_THRESHOLD = 1

def checkSimilarPictures(pic1, pic2, x_max=DIFF_THRESHOLD, y_max=DIFF_THRESHOLD):
    # print pic1, pic2
    image1 = Image.open(pic1).convert('L')
    image2 = Image.open(pic2).convert('L')
    
    diff = ImageChops.difference(image1, image2)
    box = diff.getbbox()
    if box is None:
        return True, False

    xdiff = abs(box[0] - box[2])
    ydiff = abs(box[1] - box[3])

    if(xdiff >= x_max and ydiff >= y_max):
        # print 'Box', xdiff, ydiff

        h = diff.histogram()
        sq = (v*(i**2) for i, v in enumerate(h))
        sum_of_squares = sum(sq)
        rms = math.sqrt(sum_of_squares/float(image1.size[0] * image1.size[1]))
        # print rms
        if rms > RMS_THRESHOLD:
            # print 'RMS', rms
            if(xdiff >= CRASH_THRESHOLD and ydiff >= CRASH_THRESHOLD):
                return False, True
            return False, False

    return True, False

if __name__ == "__main__":
    import sys
    img1 = sys.argv[1]
    img2 = sys.argv[2]
    print checkSimilarPictures(img1, img2)
