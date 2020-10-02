''' Given the date and season from the frontend, and the
home team from PyTesseract or the frontend for simplicity,
this script returns the game_id for fetching play by play data '''

import pbp_utils as util

DATE = '2020-08-14'
SEASON = '2019-20'
HOME_TEAM = 'HOU'

def main():
    url_games = "https://stats.nba.com/stats/leaguegamelog?Counter=1000&DateFrom=&DateTo=&Direction=DESC&LeagueID=00&PlayerOrTeam=T&Season={0}&SeasonType=Regular+Season&Sorter=DATE".format(SEASON)
    df_games = util.extract_data(url_games)
    game_id = df_games[(df_games['GAME_DATE'] == DATE) & (df_games['TEAM_ABBREVIATION'] == HOME_TEAM)]['GAME_ID']
    print(game_id.values[0])

if __name__ == '__main__':
    main()
