import json
import glob

import pandas as pd
import numpy as np
import math

import cv2

from sklearn.linear_model import LinearRegression

def build_training(court_json, player_json):
    rows = []
    #ensures frames match up in both court and player json
    for _, frame_id in zip(court_json, player_json):
        #extract the court keypoints that are found
        for keypoint in court_json[frame_id]:
            coords = court_json[frame_id][keypoint]
            #only found keypoints
            if len(coords) > 0:
                x_court_pixels = coords[0]
                y_court_pixels = coords[1]
                #access real coordinate dictionary tuple
                x_court_new = court_keypoints[keypoint][0]
                y_court_new = court_keypoints[keypoint][1]
                #build row
                row = [x_court_pixels, y_court_pixels, x_court_new, y_court_new]
                rows.append(row)
    return np.array(rows)

def player_prediction(player_json, model_x, model_y):
    ''' using the linear models trained on the court points
        predict the players locations in an inference step '''
    for frame_id in player_json:
        for player in player_json[frame_id]:
            player_x = player_json[frame_id][player]['x']
            player_y = player_json[frame_id][player]['y']
            x_predicted = model_x.predict(np.array([[player_x, player_y]]))[0]
            y_predicted = model_y.predict(np.array([[player_x, player_y]]))[0]
            #replace x and y with new coordinates
            player_json[frame_id][player]['x'] = x_predicted
            player_json[frame_id][player]['y'] = y_predicted
    return player_json

if __name__ == "__main__":
    #read in court and player tracking as input
    with open('./test_data/court_tracking_results_demo.json') as court:
        court_json = json.load(court)
    with open('./test_data/player_tracking_w_teams.json') as player:
        player_json = json.load(player)

    #read in the frames from user videp
    all_frames = [cv2.cvtColor(cv2.imread(image), cv2.COLOR_BGR2RGB) for image in sorted(glob.glob('/Users/dgrubis/Desktop/DS5500/repo/DS5500_Player_Tracking_and_Identification_NBA/demo_sample/test_frames/*.png'))]

    #Create dictionary to store court coordinates as a tuple of each keypoint
    #TODO: once court model is done update this to the new court keypoints
    court_keypoints = {'A': (-28,8),
                    'B': (-28,-8),
                    'C': (-22,0),
                    'D': (-47,-11),
                    'E': (-47,-8),
                    'F': (-47,11),
                    'G': (-47,8),
                    'H': (-17,0),
                    'I': (-28,6),
                    'J': (-28,6),
                    'K': (-47,25),
                    'L': (-47,22),
                    'M': (-19,25)}

    #build training data from court tracking output
    training = build_training(court_json, player_json)

    #features and labels for predicting the new y coordinate
    features = training[:,[0,1]]
    label_y = training[:,3]
    #labels for predicting the new x coordinate
    label_x = training[:,2]

    #train linear models for x and y coordinate in new coordinate system
    model_y = LinearRegression().fit(features, label_y)
    model_x = LinearRegression().fit(features, label_x)

    #predict players (x,y) using linear models
    player_json_transformed = player_prediction(player_json, model_x, model_y)

    #export and pass along the final player tracking json output
    with open('./player_tracking_transformed.json', 'w') as output:
        json.dump(player_json_transformed, output)