"""Yahoo Sports CFB data scraper"""

from __future__ import print_function
import os.path
import json
import urllib2
import re
from datetime import datetime
from bs4 import BeautifulSoup
import pandas as pd

class YahooScraper(object):
    """Scrapes data from Yahoo Sports."""
    _datefmt = '%Y-%m-%d'
    _team_names_file = 'data/teams.json'
    
    def __init__(self):
        with open('data/urls.json') as json_file:
            self.urls = json.load(json_file)

    def get_team_names(self, overwrite=False):
        """Obtain all team names and save them in a JSON database. If
        overwrite is True, this will forcibly overwrite the team names
        database if it exists.

        Notes
        -----
        The URLs use the division names "I-A" and "I-AA" to signify
        FBS and FCS, respecitvely.

        """
        # Check if we should proceed
        assert isinstance(overwrite, (bool, int))
        if not overwrite and os.path.exists(self._team_names_file):
            print("Team names database already exists! Not overwriting")
            return
        
        # Load HTML for scraping
        print("Fetching team names...")
        try:
            url = self.urls['names'].format(division="I-A")
            fbs_html = urllib2.urlopen(url)
            url = self.urls['names'].format(division="I-AA")
            fcs_html = urllib2.urlopen(url)
        except urllib2.URLError:
            print("Failed to fetch names. Are the URLs incorrect?")

        # Empty dictionary for storing team data
        # TODO: populate all the other stuff, too
        data = {
            'team': [],
            'division': [],
            #'conference': [],
            #'subconference': [] # division within a conference if applicable
        }

        # Scrape FBS
        #conferences = fbs_html.find_all('span', class_='yspdetailttl')
        soup = BeautifulSoup(fbs_html)
        teams = soup.find_all('a', href=re.compile('^/ncaaf/teams/'))
        for team in teams:
            data['team'].append(team.text)
            data['division'].append('FBS')

        # Scrape FCS
        soup = BeautifulSoup(fcs_html)
        teams = soup.find_all('a', href=re.compile('^/ncaaf/teams/'))
        for team in teams:
            data['team'].append(team.text)
            data['division'].append('FCS')

        # Write
        with open(self._team_names_file, 'w') as outfile:
            json.dump(data, outfile, indent=2)

    def get_scores(self, week):
        """Get all scores from one week.

        Notes
        -----
        The URLs for all games use "conference" names 'fbs_all' and
        'fcs_all' for all games in FBS and FCS,
        respectively. Unfortunately, the link for all FBS and FCS does
        not appear to work for all weeks, so they would have to be
        scraped separately.

        """
        # Fetch scores
        assert isinstance(week, int)
        print("Fetching scores for week {}...".format(week))
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
            date = datetime.strptime(date_str, '%Y%m%d')
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
            data.to_csv(location, index=False, date_format=self._datefmt)

if __name__ == "__main__":
    scraper = YahooScraper()
    scraper.get_team_names(overwrite=True)
    scraper.get_scores(1)
    scraper.export('data/scores.csv', fmt='csv')
    