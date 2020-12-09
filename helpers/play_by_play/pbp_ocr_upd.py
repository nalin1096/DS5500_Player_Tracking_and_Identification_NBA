import json
import pandas as pd
import requests
import json
from collections import defaultdict

#define front end variables
DATE = '2015-12-25'
SEASON = '2015-16'
SEASON_TYPE = 'Regular+Season' # 'Regular+Season' or 'Playoffs'
HOME_TEAM = 'LAL'

header_data  = {
    'Connection': 'keep-alive',
    'Accept': 'application/json, text/plain, */*',
    'x-nba-stats-token': 'true',
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/79.0.3945.130 Safari/537.36',
    'x-nba-stats-origin': 'stats',
    'Sec-Fetch-Site': 'same-origin',
    'Sec-Fetch-Mode': 'cors',
    'Referer': 'https://stats.nba.com/',
    'Accept-Encoding': 'gzip, deflate, br',
    'Accept-Language': 'en-US,en;q=0.9',
}

# Extract json
def extract_data(url):
    r = requests.get(url, headers=header_data)                  # Call the GET endpoint
    resp = r.json()                                             # Convert the response to a json object
    results = resp['resultSets'][0]                             # take the first item in the resultsSet (This can be determined by inspection of the json response)
    headers = results['headers']                                # take the headers of the response (our column names)
    rows = results['rowSet']                                    # take the rows of our response
    frame = pd.DataFrame(rows)                                  # convert the rows to a dataframe
    frame.columns = headers                                     # set our column names using the  extracted headers
    return frame

def calculate_time_at_period(period):
    if period > 5:
        return (720 * 4 + (period - 5) * (5 * 60)) * 10
    else:
        return (720 * (period - 1)) * 10

def split_subs(df, tag):
    subs = df[[tag, 'PERIOD', 'EVENTNUM']]
    subs['SUB'] = tag
    subs.columns = ['PLAYER_ID', 'PERIOD', 'EVENTNUM', 'SUB']
    return subs

def frame_to_row(df):
    game_id = df['GAME_ID'].unique()
    team1 = df['TEAM_ID'].unique()[0]
    team2 = df['TEAM_ID'].unique()[1]
    players1 = df[df['TEAM_ID'] == team1]['PLAYER_ID'].tolist()
    players1.sort()
    players2 = df[df['TEAM_ID'] == team2]['PLAYER_ID'].tolist()
    players2.sort()

    lst = [team1]
    lst.append(players1)
    lst.append(team2)
    lst.append(players2)
    lst.append(game_id)


    return lst

# Players at the start of each period are stored as an string in the dataframe column
# We need to parse out that string into an array of player Ids
def split_row(list_str):
    return [x.replace('[', '').replace(']', '').strip() for x in str(list_str).split(',')]

def play_by_play_url(game_id):
    return "https://stats.nba.com/stats/playbyplayv2/?gameId={0}&startPeriod=0&endPeriod=14".format(game_id)

def advanced_boxscore_url(game_id, start, end):
    return "https://stats.nba.com/stats/boxscoretraditionalv2/?gameId={0}&startPeriod=0&endPeriod=14&startRange={1}&endRange={2}&rangeType=2".format(game_id, start, end)

def get_players_on_court(game_id):

    play_by_play = extract_data(play_by_play_url(game_id))

    substitutionsOnly = play_by_play[play_by_play['EVENTMSGTYPE'] == 8][['PERIOD', 'EVENTNUM', 'PLAYER1_ID', 'PLAYER2_ID']]
    substitutionsOnly.columns = ['PERIOD', 'EVENTNUM', 'OUT', 'IN']

    subs_in = split_subs(substitutionsOnly, 'IN')
    subs_out = split_subs(substitutionsOnly, 'OUT')

    full_subs = pd.concat([subs_out, subs_in], axis=0).reset_index()[['PLAYER_ID', 'PERIOD', 'EVENTNUM', 'SUB']]
    first_event_of_period = full_subs.loc[full_subs.groupby(by=['PERIOD', 'PLAYER_ID'])['EVENTNUM'].idxmin()]
    players_subbed_in_at_each_period = first_event_of_period[first_event_of_period['SUB'] == 'IN'][
        ['PLAYER_ID', 'PERIOD', 'SUB']]

    periods = players_subbed_in_at_each_period['PERIOD'].drop_duplicates().values.tolist()

    rows = []
    for period in periods:
        low = calculate_time_at_period(period) + 5
        high = calculate_time_at_period(period + 1) - 5
        boxscore = advanced_boxscore_url(game_id, low, high)
        boxscore_players = extract_data(boxscore)#[['PLAYER_NAME', 'PLAYER_ID', 'TEAM_ID']]
        boxscore_players['PERIOD'] = period

        players_subbed_in_at_period = players_subbed_in_at_each_period[players_subbed_in_at_each_period['PERIOD'] == period]

        joined_players = pd.merge(boxscore_players, players_subbed_in_at_period, on=['PLAYER_ID', 'PERIOD'], how='left')
        joined_players = joined_players[pd.isnull(joined_players['SUB'])][['GAME_ID', 'PLAYER_ID', 'TEAM_ID', 'PERIOD']]
        row = frame_to_row(joined_players)
        row.append(period)
        rows.append(row)

    players_on_court_at_start_of_period = pd.DataFrame(rows)
    cols = ['TEAM_ID_1', 'TEAM_1_PLAYERS', 'TEAM_ID_2', 'TEAM_2_PLAYERS', 'GAME_ID', 'PERIOD']
    players_on_court_at_start_of_period.columns = cols

    return players_on_court_at_start_of_period

def add_players_on_court_to_pbp(play_by_play, players_at_start_of_period):

    #create a hashmap that stores a teams lineup for the start of each period of each game
    sub_map = {}
    # Pre-populate the map with the players at the start of each period
    for r in players_at_start_of_period.iterrows():
        sub_map[r[1]['PERIOD']] = {r[1]['TEAM_ID_1']: split_row(r[1]['TEAM_1_PLAYERS']),
                                   r[1]['TEAM_ID_2']: split_row(r[1]['TEAM_2_PLAYERS'])}

    for index, row in play_by_play.iterrows():
        #grab the game_id and period for a row
        game_id = row['GAME_ID']
        period = row['PERIOD']
        #if the event is a sub
        if row['EVENTMSGTYPE'] == 8:
            try:

                #grab the team_id
                team_id = row['PLAYER1_TEAM_ID']
                #grab the player ids for the sub in and sub out
                player_in = str(row['PLAYER2_ID'])
                player_out = str(row['PLAYER1_ID'])
                #get the current players in for that period
                players = sub_map[period][team_id]
                #get the sub out's index
                players_index = players.index(player_out)
                #replace with the sub in
                players[players_index] = player_in
                players.sort()
                #new list of players are the players after the sub
                sub_map[period][team_id] = players
            except ValueError:
                continue

        for i, k in enumerate(sub_map[period].keys()):
            play_by_play.loc[index, 'TEAM{}_ID'.format(i + 1)] = str(k)
            play_by_play.loc[index, 'TEAM{}_PLAYER1'.format(i + 1)] = sub_map[period][k][0]
            play_by_play.loc[index, 'TEAM{}_PLAYER2'.format(i + 1)] = sub_map[period][k][1]
            play_by_play.loc[index, 'TEAM{}_PLAYER3'.format(i + 1)] = sub_map[period][k][2]
            play_by_play.loc[index, 'TEAM{}_PLAYER4'.format(i + 1)] = sub_map[period][k][3]
            try:
                play_by_play.loc[index, 'TEAM{}_PLAYER5'.format(i + 1)] = sub_map[period][k][4]
            except IndexError:
                play_by_play.loc[index, 'TEAM{}_PLAYER5'.format(i + 1)] = 'None'

    return play_by_play

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

class PlayByPlay:
    def __init__(self, DATE, SEASON, SEASON_TYPE, HOME_TEAM):
        self.date = DATE 
        self.season = SEASON 
        self.season_type = SEASON_TYPE 
        self.home_team = HOME_TEAM
        self.game_id = self.get_gameid()

    def get_gameid(self):
        #get game_id
        url_games = "https://stats.nba.com/stats/leaguegamelog?Counter=1000&DateFrom=&DateTo=&Direction=DESC&LeagueID=00&PlayerOrTeam=T&Season={0}&SeasonType={1}&Sorter=DATE".format(self.season, self.season_type)
        df_games = extract_data(url_games)
        game_id = df_games[(df_games['GAME_DATE'] == self.date) & (df_games['TEAM_ABBREVIATION'] == self.home_team)]['GAME_ID'].values[0]
        return game_id

    def get_pbp(self):
        #get pbp for that game
        play_by_play = extract_data(play_by_play_url(self.game_id))
        players_at_start_of_period = get_players_on_court(self.game_id)
        final_pbp = add_players_on_court_to_pbp(play_by_play, players_at_start_of_period)
        return final_pbp


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
    with open('./data/ocr_w_players.json', 'w') as output:
        json.dump(ocr_pbp_new, output)