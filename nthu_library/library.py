from nthu_library.tools import get_rss
from nthu_library.crawler import get_circulation_links, crawl_top_circulations, crawl_lost_objects
from nthu_library.user import User as LibraryUser

__author__ = 'salas'


class NTHULibrary(object):

    home = 'http://webpac.lib.nthu.edu.tw/F/'
    top_circulations = 'http://www.lib.nthu.edu.tw/guide/topcirculations/index.htm'
    top_circulations_bc2007 = 'http://www.lib.nthu.edu.tw/guide/topcirculations/bc2007.htm'
    rss_recent_books = 'http://webpac.lib.nthu.edu.tw:8080/nbr/reader/rbn_rss.jsp'
    lost_found_url = 'http://adage.lib.nthu.edu.tw/find/search_it.php'

    def __init__(self, user):
        self.user = LibraryUser(self, user)
        self._circulation_links = get_circulation_links(self)

    def __repr__(self):
        return '%s@library object' % self.user.account


    def get_lost(self,
                 place='ALL', date_start='2015-02-10',
                 date_end='2015-08-10', catagory='ALL',
                 keyword=''):
        data = {
            'place': place, 'date_start': date_start,
            'date_end': date_end, 'catalog': catagory,
            'keyword': keyword
        }
        return crawl_lost_objects(self, data)

    def get_newest_books(self, lang=None):
        """
        fetch recent newest books from official RSS
        :param lang: default is `None` to get both languages,
                     'en' for English; or 'zh' for Chinese
        :return: `RSS dict()`
        """
        param = {
            None: '',
            'en': '?C=LCC',
            'zh': '?C=CCL',
        }
        url = NTHULibrary.rss_recent_books + param[lang]
        return get_rss(url)

    def get_top_circulated_materials(
            self, year=None, type='loaned'):
        """
        fetch the top circulated materials in library
        :param year: 4-digit number
        :param type: 'loaned' or 'reserved'
        :return: `dict()` type data
        """
        q_type = 'b_' if type == 'loaned' else 'o_'
        query = [
            href
            for a, href in self._circulation_links
            #  filter by year and type
            if not year or (year and str(year)) in a.text
            if a.get('href').startswith(q_type)
        ]
        return crawl_top_circulations(query)

    def get_info(self):
        return self.user.get_info()

    def get_current_borrow(self, res):
        return self.user.get_current_borrow(res)

    def get_borrow_history(self, res):
        return self.user.get_borrow_history(res)

    def get_current_reserve(self):
        pass

    def get_hold_reserve(self):
        pass

    def get_reserve_history(self, res):
        return self.user.get_reserve_history(res)
