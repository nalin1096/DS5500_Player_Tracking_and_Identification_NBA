''' Given the date, season, season type, and home team from the frontend,
this script retrieves the game_id then fetches play by play data for that game'''

import pbp_utils as util

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
        df_games = util.extract_data(url_games)
        game_id = df_games[(df_games['GAME_DATE'] == self.date) & (df_games['TEAM_ABBREVIATION'] == self.home_team)]['GAME_ID'].values[0]
        return game_id

    def get_pbp(self):
        #get pbp for that game
        play_by_play = util.extract_data(util.play_by_play_url(self.game_id))
        players_at_start_of_period = util.get_players_on_court(self.game_id)
        final_pbp = util.add_players_on_court_to_pbp(play_by_play, players_at_start_of_period)
        return final_pbp
