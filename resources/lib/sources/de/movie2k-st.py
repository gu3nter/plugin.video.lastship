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

import re
import urllib
import urlparse
import base64

from resources.lib.modules import cache
from resources.lib.modules import cleantitle
from resources.lib.modules import client
from resources.lib.modules import source_utils
from resources.lib.modules import source_faultlog
from resources.lib.modules import dom_parser


class source:
    def __init__(self):
        self.priority = 1
        self.language = ['de']
        self.domains = ['movie2k.st']
        self.base_link = 'http://www.movie2k.st'
        self.search_link = '/search/%s'

    def movie(self, imdb, title, localtitle, aliases, year):
        try:
            url = self.__search([localtitle] + source_utils.aliases_to_array(aliases))
            if not url and title != localtitle: url = self.__search([title] + source_utils.aliases_to_array(aliases))
            return url
        except:
            return

    def sources(self, url, hostDict, hostprDict):
        sources = []
        try:
            if not url:
                return sources
            query = urlparse.urljoin(self.base_link, url)
            r = cache.get(client.request, 4, query)

            links = dom_parser.parse_dom(r, 'div', attrs={'id': 'tab-plot_german'})
            links = dom_parser.parse_dom(links, 'tbody')
            links = dom_parser.parse_dom(links, 'tr')
            links = [(dom_parser.parse_dom(i, 'a')[0],
                      dom_parser.parse_dom(i, 'td', attrs={'class': 'votesCell'})[0])
                     for i in links if "gif" in i.content]

            links = [(i[0][1], i[0].attrs['href'], source_utils.get_release_quality(i[1].content)[0]) for i in links]

            for hoster, link, quality in links:
                valid, hoster = source_utils.is_host_valid(hoster, hostDict)
                if not valid:
                    continue
                if '?' in link:
                    link = urlparse.urljoin(url, link)

                sources.append({'source': hoster, 'quality': quality, 'language': 'de', 'url': link, 'direct': False,
                                'debridonly': False, 'checkquality': True})

            if len(sources) == 0:
                raise Exception()
            return sources
        except:
            source_faultlog.logFault(__name__, source_faultlog.tagScrape, url)
            return sources

    def resolve(self, url):
        try:
            if 'e_link' in url:
                r = cache.get(client.request, 4, urlparse.urljoin(self.base_link,url))
                s = re.findall("dingdong\('(.*?)'", r)[0]
                s = base64.b64decode(s)
                s = re.findall("src=\"(.*?)\"", s)[0]
                url = s.strip('/')
            else:
                return url

        except:
            source_faultlog.logFault(__name__,source_faultlog.tagResolve)
            return url

    def __search(self, titles):
        try:
            query = self.search_link % (urllib.quote_plus(urllib.quote_plus(cleantitle.query(titles[0]))))
            query = urlparse.urljoin(self.base_link, query)

            t = [cleantitle.get(i) for i in set(titles) if i]

            r = cache.get(client.request, 4, query)

            r = dom_parser.parse_dom(r, 'ul', attrs={'class': 'coverBox'})
            r = dom_parser.parse_dom(r, 'li')
            r = dom_parser.parse_dom(r, 'span', attrs={'class': 'name'})
            r = dom_parser.parse_dom(r, 'a')
            r = [(i.attrs['href'], i.attrs['title']) for i in r]
            r = [(i[0], re.findall('(.*?)\(', i[1])[0]) for i in r]
            r = [i[0] for i in r if cleantitle.get(i[1]) in t]

            return source_utils.strip_domain(r[0])

        except:
            try:
                source_faultlog.logFault(__name__, source_faultlog.tagSearch, titles[0])
            except:
                return
            return
