# -*- coding: UTF-8 -*-

"""
    Lastship Add-on (C) 2019
    Credits to Placenta and Covenant; our thanks go to their creators

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""

# Addon Name: Lastship
# Addon id: plugin.video.lastship
# Addon Provider: LastShip

import base64
import json
import re
import urllib
import urlparse

from resources.lib.modules import anilist, cache
from resources.lib.modules import cfscrape
from resources.lib.modules import dom_parser
from resources.lib.modules import source_faultlog
from resources.lib.modules import source_utils
from resources.lib.modules import tvmaze


class source:
    def __init__(self):
        self.priority = 1
        self.language = ['de']
        self.domains = ['foxx.to']
        self.base_link = 'http://foxx.to'
        self.search_link = '/?s=%s'
        self.scraper = cfscrape.create_scraper()

    def movie(self, imdb, title, localtitle, aliases, year):
        try:
            url = self.__search([localtitle] + source_utils.aliases_to_array(aliases), year)
            if not url and title != localtitle: url = self.__search([title] + source_utils.aliases_to_array(aliases), year)
            if not url and source_utils.is_anime('movie', 'imdb', imdb): url = self.__search([anilist.getAlternativTitle(title)] + source_utils.aliases_to_array(aliases), year)
            
            return url
        except:
            return ""

    def tvshow(self, imdb, tvdb, tvshowtitle, localtvshowtitle, aliases, year):
        try:
            linkAndTitle = self.__search([tvshowtitle, localtvshowtitle] + source_utils.aliases_to_array(aliases), year)
            aliases = source_utils.aliases_to_array(aliases)

            if not tvshowtitle and source_utils.is_anime('show', 'tvdb', tvdb): linkAndTitle = self.__search([tvmaze.tvMaze().showLookup('thetvdb', tvdb).get('name')] + source_utils.aliases_to_array(aliases), year)

            return linkAndTitle
        except:
            return ""

    def episode(self, url, imdb, tvdb, title, premiered, season, episode):
        try:
            if not url:
                return
            url = urlparse.urljoin(self.base_link, url)
            r = cache.get(self.scraper.get, 4, url).content

            if season == 1 and episode == 1:
                season = episode = ''

            r = dom_parser.parse_dom(r, 'ul', attrs={'class': 'episodios'})
            r = dom_parser.parse_dom(r, 'a', attrs={'href': re.compile('[^\'"]*%s' % ('-%sx%s' % (season, episode)))})[0].attrs['href']
            return source_utils.strip_domain(r)
        except:
            return ""

    def sources(self, url, hostDict, hostprDict):
        sources = []
        try:
            if not url:
                return sources
            url = urlparse.urljoin(self.base_link, url)
            temp = cache.get(self.scraper.get, 4, url)
            link = re.findall('iframe\ssrc="(.*?view\.php.*?)"', temp.content)[0]
            if link.startswith('//'):
                link = "https:" + link

            r = cache.get(self.scraper.get, 4, link, headers={'referer': url}).content
            phrase = re.findall("(?:jbdaskgs|m3u8File)[^>]=[^>]'([^']+)", r)[0]

            if '\n' in phrase: return sources

            if "m3u8File" in r:
                domain = re.findall("urlVideo\s=\s'(.*streamservice.online)", r)[0]
                link = '%s/public/dist/index.html?id=%s' % (domain, phrase)
                valid, hoster = source_utils.is_host_valid(link, hostDict)
                if valid:
                    sources.append({'source': hoster, 'quality': '720p', 'language': 'de', 'url': link, 'direct': False,
                         'debridonly': False})
            else:
                links = json.loads(base64.b64decode(phrase))
                [sources.append({'source': 'CDN', 'quality': i['label'] if i['label'] in ['720p', '1080p'] else 'SD',
                                 'language': 'de', 'url': i['file'], 'direct': True, 'debridonly': False}) for i in links]

            if len(sources) == 0:
                raise Exception()
            return sources
        except Exception as e:
            source_faultlog.logFault(__name__,source_faultlog.tagScrape, url)
            return sources

    def resolve(self, url):
        return url

    def __search(self, titles, year):
        try:
            query = self.search_link % (urllib.quote_plus(titles[0]))
            query = urlparse.urljoin(self.base_link, query)

            r = cache.get(self.scraper.get, 4, query).content
            dom_parsed = dom_parser.parse_dom(r, 'div', attrs={'class': 'details'})
            links = [(dom_parser.parse_dom(i, 'a')[0], dom_parser.parse_dom(i, 'span', attrs={'class' : 'year'})[0].content) for i in dom_parsed]

            r = sorted(links, key=lambda i: int(i[1]), reverse=True)  # with year > no year
            r = [x[0].attrs['href'] for x in r if int(x[1]) == int(year)]

            if len(r) > 0:
                return source_utils.strip_domain(r[0])

            return
        except:
            try:
                source_faultlog.logFault(__name__, source_faultlog.tagSearch, titles[0])
            except:
                return
            return ""
