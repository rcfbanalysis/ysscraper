"""Yahoo Sports CFB data scraper"""

from __future__ import print_function
import json
import urllib2
from datetime import datetime
from bs4 import BeautifulSoup
import pandas as pd

class YahooScraper(object):
    """Scrapes data from Yahoo Sports."""
    def __init__(self):
        with open('data/urls.json') as json_file:
            self.urls = json.load(json_file)

    def get_team_names(self):
        """Obtain all team names and save them in a JSON database.

        Notes
        -----
        The URLs use the division names "I-A" and "I-AA" to signify
        FBS and FCS, respecitvely.

        """
        try:
            url = self.urls['names'].format(division="I-A")
            fbs_file = urllib2.urlopen(url)
            url = self.urls['names'].format(division="I-AA")
            fcs_file = urllib2.urlopen(url)
        except urllib2.URLError:
            print("Failed to fetch names. Are the URLs incorrect?")
        raise NotImplementedError("Not yet implemented.")

    def get_scores(self, week):
        """Get all scores from one week.

        Notes
        -----
        The URLs for all games use "conference" names 'fbs_all' and
        'fcs_all' for all games in FBS and FCS, respectively.

        """
        # Fetch scores
        assert isinstance(week, int)
        url = self.urls['scores'].format(conf='fbs_all', week=week)
        try:
            html = urllib2.urlopen(url)
        except urllib2.URLError:
            print("Failed to fetch scores.")
        soup = BeautifulSoup(html)

        # Filter for game rows
        def game_row(tag):
            try:
                if tag['class'] == ['game', 'link']:
                    return True
                else:
                    return False
            except:
                return False

        # Empty dictionary for storing score data
        data = {
            'date': [],
            'home.team': [],
            'home.score': [],
            'away.team': [],
            'away.score': [],
            'url': []
        }

        # Get score data
        games = soup.find_all(game_row)
        for game in games:
            date_str = game['data-gid'].split('.')[2][:8]
            date = datetime.strptime(date_str, '%Y%m%d').strftime('%Y-%m-%d')
            home = game.find('td', class_='home').find('em').text
            away = game.find('td', class_='away').find('em').text
            score = game.find('td', class_='score')
            home_score = int(score.find(True, class_='home').text)
            away_score = int(score.find(True, class_='away').text)
            url = 'http://sports.yahoo.com' + game['data-url']
            data['date'].append(date)
            data['home.team'].append(home)
            data['home.score'].append(home_score)
            data['away.team'].append(away)
            data['away.score'].append(away_score)
            data['url'].append(url)
        self.scores = pd.DataFrame(data)

    def export(self, location, kind='scores', fmt='csv'):
        """Export data.

        Parameters
        ----------
        location : str
            Path to save the data to.
        kind : str
            Which data to export. Default: 'scores'
        fmt : str
            Data format to use. Default: 'csv'

        Notes
        -----
        Eventually, it would be nice to export to any (or at least
        many) of the formats that pandas supports.

        """
        kinds = ['scores']
        formats = ['csv']
        if kind not in kinds:
            raise RuntimeError("Invalid data kind. Must be one of " + str(kinds))
        if fmt not in formats:
            raise RuntimeError("Invalid format. Must be one of " + str(formats))

        # Select the data to write
        if kind is 'scores':
            data = self.scores

        # Write data
        if fmt is 'csv':
            data.to_csv(location)

if __name__ == "__main__":
    scraper = YahooScraper()
    scraper.get_scores(1)
    scraper.export('data/scores.csv', fmt='csv')
    