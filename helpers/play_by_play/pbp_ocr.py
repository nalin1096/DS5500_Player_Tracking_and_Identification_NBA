import pandas as pd
import numpy as np 
import json
from collections import defaultdict

from play_by_play import PlayByPlay

#define front end variables
DATE = '2015-12-25'
SEASON = '2015-16'
SEASON_TYPE = 'Regular+Season' # 'Regular+Season' or 'Playoffs'
HOME_TEAM = 'LAL'

def build_df(json):
    rows = []
    for frame_id in json:
        game_clock = json[frame_id]['time']
        quarter = json[frame_id]['quarter']
        row = [frame_id, game_clock, quarter]
        rows.append(row)
    df = pd.DataFrame(rows, columns = ['frame_id', 'game_clock', 'quarter'])
    return df

def encode_quarter(quarter):
    if quarter == '1st':
        return 1
    elif quarter == '2nd':
        return 2
    elif quarter == '3rd':
        return 3
    elif quarter == '4th':
        return 4
    else:
        #doublecheck: is all of OT just 5? 2OT, 3OT,...etc.
        return 5

def new_json_format(my_dict):
    ''' better organzition by nesting players on the court info  '''
    new_dict = defaultdict(dict)
    for frame_id in ocr_pbp_dict:
        game_clock = my_dict[frame_id]['game_clock']
        quarter = my_dict[frame_id]['game_clock']
        team1_id = my_dict[frame_id]['TEAM1_ID']
        team1_player1 = my_dict[frame_id]['TEAM1_PLAYER1']
        team1_player2 = my_dict[frame_id]['TEAM1_PLAYER2']
        team1_player3 = my_dict[frame_id]['TEAM1_PLAYER3']
        team1_player4 = my_dict[frame_id]['TEAM1_PLAYER4']
        team1_player5 = my_dict[frame_id]['TEAM1_PLAYER5']
        team2_id = my_dict[frame_id]['TEAM2_ID']
        team2_player1 = my_dict[frame_id]['TEAM2_PLAYER1']
        team2_player2 = my_dict[frame_id]['TEAM2_PLAYER2']
        team2_player3 = my_dict[frame_id]['TEAM2_PLAYER3']
        team2_player4 = my_dict[frame_id]['TEAM2_PLAYER4']
        team2_player5 = my_dict[frame_id]['TEAM2_PLAYER5']
        #assign to new format json
        new_dict[frame_id]['game_clock'] = game_clock
        new_dict[frame_id]['quarter'] = quarter
        #Team 1
        #for organizition, nest another dictionary for the team id and player ids of each team
        new_dict[frame_id]['team1'] = {}
        new_dict[frame_id]['team1']['id'] = team1_id
        new_dict[frame_id]['team1']['players'] = [team1_player1, team1_player2, team1_player3, team1_player4, team1_player5]
        #Team 2
        new_dict[frame_id]['team2'] = {}
        new_dict[frame_id]['team2']['id'] = team2_id
        new_dict[frame_id]['team2']['players'] = [team2_player1, team2_player2, team2_player3, team2_player4, team2_player5]
    return new_dict

if __name__ == "__main__":

    #read in the ocr results
    with open('./data/ocr_results.json') as ocr:
        ocr_json = json.load(ocr)

    #extract play by play data for the game uploaded
    pbp = PlayByPlay(DATE, SEASON, SEASON_TYPE, HOME_TEAM).get_pbp()

    #convert from json to DataFrame
    ocr_df = build_df(ocr_json)

    #fill in missing frames quarter by taking the last known quarter
    #future TODO: very small chance the last known quarter is incorrect if missing values occur at transition around 12:00 mark of new quarter
    ocr_df['quarter'] = ocr_df['quarter'].fillna(method = 'ffill')

    #convert game clock from string to seconds
    pbp['TimeSecs'] = [int(a) * 60 + int(b) for a, b in pbp['PCTIMESTRING'].str.split(':')]
    ocr_df['TimeSecs'] = [int(a) * 60 + int(b) for a, b in ocr_df['game_clock'].str.split(':')]

    #same for the quarter
    ocr_df['quarter'] = ocr_df['quarter'].apply(encode_quarter)

    #using pandas merge_asof to match up the corresponding pbp record for each frame to figure out who is on the court at each frame
    ocr_pbp = pd.merge_asof(ocr_df.sort_values('TimeSecs'), pbp[['TimeSecs', 'PERIOD','TEAM1_ID','TEAM1_PLAYER1', 'TEAM1_PLAYER2', 'TEAM1_PLAYER3', 'TEAM1_PLAYER4', 'TEAM1_PLAYER5', 'TEAM2_ID', 'TEAM2_PLAYER1', 'TEAM2_PLAYER2', 'TEAM2_PLAYER3', 'TEAM2_PLAYER4','TEAM2_PLAYER5']].sort_values('TimeSecs'), on='TimeSecs', left_by = 'quarter', right_by = 'PERIOD', direction='forward').sort_values('frame_id').drop(columns = ['TimeSecs', 'PERIOD'])

    #set index for .to_dict method
    ocr_pbp = ocr_pbp.set_index('frame_id')

    #convert to dictionary
    ocr_pbp_dict = ocr_pbp.to_dict(orient='index')

    #transform to final output form
    ocr_pbp_new = new_json_format(ocr_pbp_dict)

    #export the final ocr json
    with open('./ocr_w_players.json', 'w') as output:
        json.dump(ocr_pbp_new, output)