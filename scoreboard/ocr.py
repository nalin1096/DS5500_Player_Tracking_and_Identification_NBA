import numpy as np
import easyocr
import cv2
import re
import matplotlib.pyplot as plt
import time
import json

#loading english ocr reader
reader = easyocr.Reader(["en"])

def getResults(sec,cap):
    cap.set(cv2.CAP_PROP_POS_MSEC, sec*1000)
    hasFrames, image = cap.read()
    if hasFrames:
        cropped = imageProcessing(image, 'espn')
        resultCrop = reader.readtext(cropped)
        #detecting text from inverted colors to get black text on white bg
        resultCropInv = reader.readtext(np.invert(cropped))
        results = resultCrop + resultCropInv
        matches = findMatches(results)
        return hasFrames,matches

    return False,{}

def imageProcessing(image, network):
    img = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    #cropping game clock based on network (this tells us location of clock)
    y,x = img.shape
    if network == 'espn':
        x1,y1 = round(0.55*x),round(0.87*y)
        x2,y2 = round(x-0.3*x), y    
    if network == 'test':
        #825,578 to 988,608
        x1,y1 = round(0.64*x),round(0.8*y)
        x2,y2 = x,y
    cropped = img[y1:y2,x1:x2]
    # plt.imshow(image, cmap='gray')
    # plt.show()
    # # plt.imshow(cropped, cmap='gray')
    # # plt.show()
    return cropped

## TO DO: FIND FOOTAGE OF OVERTIME/ HANDLE OVERTIME
## check runtime/improve

def findMatches(results):
    ''' uses regex to find matches for time, quarter and shot clock from ocr results '''

    #quarter format - a number from 1-4 followed by 2 letters or Ist/IInd,...
    # #leaving letters open ended to allow wrong ocr letter prediction (eg 2ud instead of 2nd)
    quarterRegex = r'[1-4]{1}\w{2}'
    #time match (any valid time format from 0:00 to 24:00 or 59.0 to 0.0)
    timeRegex = r'[0-9]:[0-5][0-9]|[1][0-1]:[0-5][0-9]|[12]:[0][0]|[0-5][0-9]\.[0-9]|[0-9]\.[0-9]'
    #shot clock match (any discrete number from 0-24, or 4.9 to 0.0)
    shotClockRegex = r':?[0-1][0-9]|[2][0-4]|[0-9]|[0-4]\.[0-9]'

    matches = {'time':(),'quarter':(), 'shotClock':[]}    
    quarterFlag = False
    #we want time and quarter prediction with best confidence
    bestTimeC = 0.0
    bestQuarterC = 0.0
    for i in results:
        text = i[1]
        c = i[2]
        j = ''.join(text.split(" "))
        #catching a misreading of '1st'
        if j.lower()=='ist':
            matches['quarter'] = (i[0][0][0], j, i[2])
            bestQuarterC = c
            quarterFlag = True
        #we only want valid numeric results
        elif len(j) > 0 and not j.isalpha():
            if not quarterFlag:
                quarterMatch = re.match(quarterRegex,j)
                if quarterMatch and i[2] > bestQuarterC:
                    matches['quarter'] = (i[0][0][0],quarterMatch.group(0),i[2])
                    bestQuarterC = i[2]
            timeMatch = re.match(timeRegex, j)
            if timeMatch:
                if i[2] > bestTimeC:
                    matches['time'] = (i[0][0][0],timeMatch.group(0),i[2])
                    bestTimeC = i[2]
            # collecting all shot clock matches and filtering later with location
            shotClockMatch = re.match(shotClockRegex,j)
            if shotClockMatch:
                matches['shotClock'].append((i[0][0][0],shotClockMatch.group(0),i[2]))

    #picking highest confidence shot clock match that's to the right of the time clock in the frame
    if len(matches['shotClock'])!=0:
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
            if  loc > timeX:
                if c > bestShotClockC:
                    bestShotClockMatch = match
                    bestShotClockC = c
                    bestShotClockLoc = loc
        matches['shotClock'] = (loc, match, c)
        
    return matches

videoFile = 'scoreboard/trimmed1.mp4'
sec = 0
frameRate = 0.04
success = True
frameId = 1
currDict = {}

start_time = time.time()

while success: 
    sec = sec + frameRate 
    sec = round(sec, 2) 
    cap = cv2.VideoCapture(videoFile)
    success,result  = getResults(sec,cap) 
    resultsDict = {}
    for k,v in result.items():
        resultsDict[k] = v[1]
    currDict[str(frameId)] = resultsDict
    frameId += 1
    
with open('ocrresult.txt', 'w') as outfile:
    json.dump(currDict, outfile)

print("--- %s seconds ---" % round(time.time() - start_time,2))