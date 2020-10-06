''' Given the date, season, season type, and home team from the front,
this script retrieves the game_id then fetches play by play data for that game'''

import pbp_utils as util

DATE = '2020-08-14'
SEASON = '2019-20'
SEASON_TYPE = 'Regular+Season' # 'Regular+Season' or 'Playoffs'
HOME_TEAM = 'HOU'

def main():
    #get game_id
    url_games = "https://stats.nba.com/stats/leaguegamelog?Counter=1000&DateFrom=&DateTo=&Direction=DESC&LeagueID=00&PlayerOrTeam=T&Season={0}&SeasonType={1}&Sorter=DATE".format(SEASON, SEASON_TYPE)
    df_games = util.extract_data(url_games)
    GAME_ID = df_games[(df_games['GAME_DATE'] == DATE) & (df_games['TEAM_ABBREVIATION'] == HOME_TEAM)]['GAME_ID'].values[0]

    #get pbp for that game
    play_by_play = util.extract_data(util.play_by_play_url(GAME_ID))
    players_at_start_of_period = util.get_players_on_court(GAME_ID)
    final_pbp = util.add_players_on_court_to_pbp(play_by_play, players_at_start_of_period)
    print(final_pbp.head())

if __name__ == '__main__':
    main()
