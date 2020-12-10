import uuid
from django.db import models


class Video(models.Model):
    NBA_SEASONS = [
        ('2012-2013', '2012-2013'),
        ('2013-2014', '2013-2014'),
        ('2014-2015', '2014-2015'),
        ('2015-2016', '2015-2016'),
        ('2016-2017', '2016-2017'),
        ('2017-2018', '2017-2018'),
        ('2018-2019', '2018-2019'),
    ]
    NBA_TEAMS = [
        ('ATL', 'Atlanta Hawks'),
        ('BKN', 'Brooklyn Nets'),
        ('BOS', 'Boston Celtics'),
        ('CHA', 'Charlotte Hornets'),
        ('CHI', 'Chicago Bulls'),
        ('CLE', 'Cleveland Cavaliers'),
        ('DAL', 'Dallas Mavericks'),
        ('DEN', 'Denver Nuggets'),
        ('DET', 'Detroit Pistons'),
        ('GSW', 'Golden State Warriors'),
        ('HOU', 'Houston Rockets'),
        ('IND', 'Indiana Pacers'),
        ('LAC', 'Los Angeles Clippers'),
        ('LAL', 'Los Angeles Lakers'),
        ('MEM', 'Memphis Grizzlies'),
        ('MIA', 'Miami Heat'),
        ('MIL', 'Milwaukee Bucks'),
        ('MIN', 'Minnesota Timberwolves'),
        ('NOP', 'New Orleans Pelicans'),
        ('NYK', 'New York Knicks'),
        ('OKC', 'Oklahoma City Thunder'),
        ('ORL', 'Orlando Magic'),
        ('PHI', 'Philadelphia 76ers'),
        ('PHX', 'Phoenix Suns'),
        ('POR', 'Portland Trail Blazers'),
        ('SAC', 'Sacramento Kings'),
        ('SAS', 'San Antonio Spurs'),
        ('TOR', 'Toronto Raptors'),
        ('UTA', 'Utah Jazz'),
        ('WAS', 'Washington Wizards'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    results_id = models.CharField(max_length=32, null=True)
    email = models.EmailField()
    season = models.CharField(max_length=9, choices=NBA_SEASONS, default='2018-2019')
    home_team = models.CharField(max_length=3, choices=NBA_TEAMS, default='LAL')
    videofile = models.FileField(upload_to='tracking/videos/', null=True, verbose_name="")
    player_tracking_file = models.FileField(upload_to='tracking/tracking_results', null=True, verbose_name="", max_length=1000)
    court_tracking_file = models.FileField(upload_to='tracking/tracking_results', null=True, verbose_name="", max_length=1000)
    ocr_file = models.FileField(upload_to='tracking/tracking_results', null=True, verbose_name="", max_length=1000)
    ocr_with_players_file = models.FileField(upload_to='tracking/tracking_results', null=True, verbose_name="", max_length=1000)
    player_tracking_transformation_file = models.FileField(upload_to='tracking/tracking_results', null=True, verbose_name="", max_length=1000)
    player_tracking_smoothing_file = models.FileField(upload_to='tracking/tracking_results', null=True, verbose_name="", max_length=1000)

    def __str__(self):
        return str(self.videofile)

