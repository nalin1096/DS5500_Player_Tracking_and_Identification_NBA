import json
import glob

import pandas as pd
import numpy as np
import math

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

    #Create dictionary to store court coordinates as a tuple of each keypoint
    #TODO: once court model is done update this to the new court keypoints
    court_keypoints = {'AL': (-28,8),
                    'BL': (-28,-8),
                    'CL': (-22,0),
                    'DL': (-47,-11),
                    'EL': (-47,-8),
                    'FL': (-47,11),
                    'GL': (-47,8),
                    'HL': (-17,0),
                    'IL': (-28,6),
                    'JL': (-28,6),
                    'KL': (-47,25),
                    'LL': (-47,22),
                    'ML': (-19,25),
                    'AR': (28,8),
                    'BR': (28,-8),
                    'CR': (22,0),
                    'DR': (47,-11),
                    'ER': (47,-8),
                    'FR': (47,11),
                    'GR': (47,8),
                    'HR': (17,0),
                    'IR': (28,6),
                    'JR': (28,6),
                    'KR': (47,25),
                    'LR': (47,22),
                    'MR': (19,25)}

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