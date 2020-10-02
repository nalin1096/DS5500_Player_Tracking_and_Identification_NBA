import pbp_utils as util

GAME_ID = '0021901315'

def main():
    play_by_play = util.extract_data(util.play_by_play_url(GAME_ID))
    players_at_start_of_period = util.get_players_on_court(GAME_ID)
    final_pbp = util.add_players_on_court_to_pbp(play_by_play, players_at_start_of_period)
    print(final_pbp.head())

if __name__ == '__main__':
    main()
