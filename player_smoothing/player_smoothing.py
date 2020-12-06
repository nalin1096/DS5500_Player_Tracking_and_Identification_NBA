import json
import cv2
import numpy as np
import matplotlib.pyplot as plt
from pykalman import KalmanFilter

def processTrackingData(data):
    # creates dictionary of form {player1:[(x1,y1),(x2,y2),...],player2:[(x1,y1),...]}
    
    #we need list of unique player ids - we loop over data to create this
    playerIds = []
    for image in data:
        players = data[image].keys()
        playerIds.extend(list(players))
    playerIds = set(playerIds)

    playerDict = {k:[] for k in playerIds}
    for image in data:
        for playerId in playerIds:
            #if player appears in current image, append coords
            if playerId in data[image].keys():
                playerDict[playerId].append((data[image][playerId]['x'], data[image][playerId]['y']))
            # #if player not in current image, append (0,0) 
            # else:
            #     playerDict[playerId].append((0,0))
    return playerDict

#given an array of (x,y) coords, we want to remove portions that have only (0,0) observations
#goal is to keep tracking data for time player is on court, but still allow for some missing data in between trajectory
def findNonZero(array):
    firstNonZero = np.min(np.nonzero(array))
    lastNonZero = np.max(np.nonzero(array))+1
    new = array[firstNonZero:lastNonZero,:]
    return new, firstNonZero, lastNonZero

def applySmoothing(playerDict,nIter):
    smoothedDict = {}
    frameDict = {}
    for i in playerDict:
        arr = np.array(playerDict[i])
        #we will remove continuous (0,0) observations
        measurements, firstNonZero, lastNonZero = findNonZero(arr)
        # frameDict[i] = (firstNonZero, lastNonZero)
        n = measurements.shape[0]
        #if there are more than 4 observations, apply smoothing
        if n > 4:
            kf = KalmanFilter(n_dim_obs=2,n_dim_state=2)
            #smooth all excpet first and last 2 coordinates (not enough obs for those)
            smoothed = kf.em(measurements,n_iter=nIter).smooth(measurements[2:(n-2)])
            adjusted1 = np.vstack((measurements[0:2],smoothed[0]))
            adjusted = np.vstack((adjusted1, measurements[(n-2):(n+1)]))
            #split array and convert to (x,y) coords
            xcoords = np.reshape(adjusted[:,0], (len(measurements)))
            ycoords = np.reshape(adjusted[:,1], (len(measurements)))
            smoothedDict[i] = list(zip(xcoords,ycoords))
        else:
            #if <= 4 obs do not smooth
            smoothedDict[i] = measurements
    return smoothedDict

# def deleteGaps(smoothedDict):
#     newSmoothed = {}
#     for i in smoothedDict:
#         arr = smoothedDict[i]
#         newSmoothed[i] = [x for x in arr if round(x[0],1)!=0.0 and round(x[1],1)!=0.0]
#     return newSmoothed
        
def replaceSmoothedCoords(data,smoothedDict):
    newDict = smoothedDict.copy()
    for image in data:
        players = list(data[image].keys())
        for player in players:
            newDict[player] = list(newDict[player])
            x_smoothed,y_smoothed = newDict[player][0]
            old_x = data[image][player]['x'] 
            old_y = data[image][player]['y'] 
            data[image][player]['x'] = x_smoothed
            data[image][player]['y'] = y_smoothed
            newDict[player].pop(0)        
    return data


if __name__ == "__main__":
    #opening file
    inputFile = "./player_smoothing/player_tracking_transformed.json"
    with open(inputFile, "r") as readFile:
        data = json.load(readFile)

    playerDict = processTrackingData(data)
    smoothedDict = applySmoothing(playerDict,10)
    # noGapsSmoothed = deleteGaps(smoothedDict)
    newData = replaceSmoothedCoords(data,smoothedDict)
    outputFile = 'player_smoothing/smoothed_trajectories.txt'
    #writing json file
    with open(outputFile, 'w') as outfile:
        json.dump(newData, outfile)
