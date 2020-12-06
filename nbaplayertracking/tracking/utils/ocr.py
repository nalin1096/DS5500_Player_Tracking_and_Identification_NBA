import numpy as np
import easyocr
import cv2
import re
import json
import glob
import os

def imageProcessing(image, network):
    '''crops image according to network'''
    img = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    y, x = img.shape
    if network == 'espn':
        x1, y1 = round(0.55*x),round(0.87*y)
        x2, y2 = round(x-0.3*x), y
    elif network == 'test':
        # 825,578 to 988,608
        x1, y1 = round(0.64*x),round(0.8*y)
        x2, y2 = x,y
    elif network == 'tnt':
        x1, y1 = round(0.66*x),round(0.84*y)
        x2, y2 = round(0.88*x),round(0.88*y)
    cropped = img[y1:y2, x1:x2]
    return cropped

## TO DO: FIND FOOTAGE OF OVERTIME/ HANDLE OVERTIME
## check runtime/improve

def findMatches(results):
    ''' uses regex to find matches for time, quarter and shot clock from ocr results '''
    # quarter format - a number from 1-4 followed by 2 letters or Ist/IInd,...
    # leaving letters open ended to allow wrong ocr letter prediction (eg 2ud instead of 2nd)
    quarterRegex = r'[1-4]{1}\w{2}'
    # time match (any valid time format from 0:00 to 24:00 or 59.0 to 0.0)
    timeRegex = r'[0-9]:[0-5][0-9]|[1][0-1]:[0-5][0-9]|[12]:[0][0]|[0-5][0-9]\.[0-9]|[0-9]\.[0-9]'
    # shot clock match (any discrete number from 0-24, or 4.9 to 0.0)
    shotClockRegex = r':?[0-1][0-9]|[2][0-4]|[0-9]|[0-4]\.[0-9]'
    matches = {'time':(None, None, None),'quarter':(None, None, None), 'shotClock':[]}    
    quarterFlag = False
    # we want time and quarter prediction with best confidence
    bestTimeC = 0.0
    bestQuarterC = 0.0
    
    for i in results:
        text = i[1]
        c = i[2]
        j = ''.join(text.split(" "))
        # catching a misreading of '1st'
        if j.lower() == 'ist':
            matches['quarter'] = (i[0][0][0], '1st', i[2])
            bestQuarterC = c
            quarterFlag = True
        # we only want valid numeric results
        elif len(j) > 0 and not j.isalpha():
            if not quarterFlag:
                quarterMatch = re.match(quarterRegex, j)
                if quarterMatch and i[2] > bestQuarterC:
                    matches['quarter'] = (i[0][0][0], quarterMatch.group(0), i[2])
                    bestQuarterC = i[2]
            timeMatch = re.match(timeRegex, j)
            if timeMatch:
                if i[2] > bestTimeC:
                    matches['time'] = (i[0][0][0], timeMatch.group(0), i[2])
                    bestTimeC = i[2]
            # collecting all shot clock matches and filtering later with location
            shotClockMatch = re.match(shotClockRegex,j)
            if shotClockMatch:
                matches['shotClock'].append((i[0][0][0], shotClockMatch.group(0), i[2]))

    # picking highest confidence shot clock match that's to the right of the time clock in the frame
    if len(matches['shotClock']) != 0:
        if matches['time']:
            timeX = matches['time'][0]
        else:
            timeX = 0
        bestShotClockMatch = None
        bestShotClockC = 0.0
        bestShotClockLoc = None

        for shotClockMatch in matches['shotClock']:
            match = shotClockMatch[1]
            c = shotClockMatch[2]
            loc = shotClockMatch[0]
            if loc > timeX:
                if c > bestShotClockC:
                    bestShotClockMatch = match
                    bestShotClockC = c
                    bestShotClockLoc = loc
        if bestShotClockC >= 0.6:
            matches['shotClock'] = (loc, match, c)
        else:
            matches['shotClock'] = (None, None, None)
    return matches
    
def processImages(reader, directoryPath, network):
    '''process images from a directory to find scoreboard results'''
    all_frames = [cv2.cvtColor(cv2.imread(image), cv2.COLOR_BGR2RGB) for image in sorted(glob.glob(os.path.join(directoryPath, "*.png")))]
    filenames = sorted(glob.glob(os.path.join(directoryPath, "*.png")))
    currDict = {}

    for frame, filename in zip(all_frames, filenames):
        cropped = imageProcessing(frame, network)
        resultCrop = reader.readtext(cropped)
        # detecting text from inverted colors to get black text on white bg
        resultCropInv = reader.readtext(np.invert(cropped))
        results = resultCrop + resultCropInv
        matches = findMatches(results)
        resultsDict = {}
        for k, v in matches.items():
            resultsDict[k] = v[1]
        currDict[os.path.basename(filename)] = resultsDict
    return currDict

def get_ocr(frames_dir, output_dir):
    # loading english ocr reader
    reader = easyocr.Reader(["en"])
    network = 'test'

    result = processImages(reader, frames_dir, network)

    # writing json file
    with open(os.path.join(output_dir, "ocr_results.json"), "w") as outfile:  
        json.dump(result, outfile)

    return