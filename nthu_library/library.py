import re
from urllib.parse import urljoin

from nthu_library.tools import get_page, post_page, get_pages, get_rss

__author__ = 'salas'


class NTHULibrary():

    home = 'http://webpac.lib.nthu.edu.tw/F/'
    top_circulations = 'http://www.lib.nthu.edu.tw/guide/topcirculations/index.htm'
    top_circulations_bc2007 = 'http://www.lib.nthu.edu.tw/guide/topcirculations/bc2007.htm'
    rss_recent_books = 'http://webpac.lib.nthu.edu.tw:8080/nbr/reader/rbn_rss.jsp'

    def __init__(self, user):
        self.user = user
        self._session_url = ''
        self._circulation_links = self._get_circulation_links()
        self.is_login = self._login()

    def __repr__(self):
        return '%s@library object' % self.user.account

    def _login(self):
        soup = get_page(urljoin(self.home, '?func=file&file_name=login1'))
        login_url = soup.find('form').attrs.get('action')

        resp = post_page(login_url, data=self.user.to_dict())
        self._session_url = resp.url
        return '您已登入' in resp.text

    def _parse(self, soup):
        if not self.is_login:
            raise NotLoginException
        tables = soup.find_all('table', attrs={'cellspacing': '2'})

        # 圖書館流通狀態
        status = {}
        for row in tables[0].find_all('tr'):
            cols = [e for e in row.children if str(e).strip()]
            key = cols[0].text.strip()
            val = cols[1].find('a').text.strip()
            link = re.findall("'(.*?)'", cols[1].find('a').attrs.get('href'))[0]
            status[key] = (val, link)

        # 聯絡資料
        person = {}
        for row in tables[1].find_all('tr'):
            cols = [e for e in row.children if str(e).strip()]
            key = cols[0].text.strip() or '地址'
            val = cols[1].text.strip()
            person[key] = person[key] + val if key in person else val

        # 管理資訊
        manage = {}
        for row in tables[2].find_all('tr'):
            cols = [e for e in row.children if str(e).strip()]
            key = cols[0].text.strip()
            val = cols[1].text.strip()
            if key == '讀者權限資料':
                val = re.findall("borstatus='(.*)'", val)[0]
            manage[key] = val

        result = dict()
        result['user'] = person
        result['status'] = status
        result['user']['manage'] = manage
        return result

    def _get_circulation_links(self):
        return [
            (a, urljoin(self.top_circulations, a.get('href')))
            for soup in get_pages([
                NTHULibrary.top_circulations,
                NTHULibrary.top_circulations_bc2007])
            for a in soup.find(id='cwrp').find_all('a')
        ]

    def get_newest_books(self, **kwargs):
        """
        fetch recent newest books from official RSS
        :param lang: default is `None` to get both languages,
                     'en' for English; or 'zh' for Chinese
        :return: `RSS dict()`
        """
        return get_rss(NTHULibrary.rss_recent_books, **kwargs)

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

        results = dict()
        for content in get_pages(query):
            table = content.find('table', 'listview')
            books = list()
            for row in table.find_all('tr')[1:]:
                try:
                    rk, title, ref, cnt = row.findChildren()
                except:
                    # for year 2003, there's no <a> tag
                    rk, title, cnt = row.findChildren()
                books.append({
                    'rank': rk.text,
                    'bookname': title.text.strip(' /'),
                    'link': ref.get('href') if ref else None,
                    'times': cnt.text
                })
            results[table.get('summary')] = books
        return results

    def get_info(self):
        if not self.is_login:
            raise NotLoginException
        soup = get_page(urljoin(self._session_url, '?func=BOR-INFO'))

        return self._parse(soup)

    def get_current_bowrrow(self, res):
        if not self.is_login:
            raise NotLoginException
        try:
            soup = get_page(res['status']['目前借閱中清單'][1])
            rows = soup.find('table', attrs={'cellspacing': '2', 'border': '0'}).find_all('tr')[1:]
        except AttributeError:
            return []
        books = []
        for row in rows:
            cols = [e for e in row.children if str(e).strip()]
            meta_dl = re.findall('(.*?)(\d+)', cols[5].text)[0]

            book = {
                'link': cols[0].find('a').attrs.get('href'),
                'author': cols[2].text,
                'title': cols[3].text.strip(' /'),
                'publish_year': cols[4].text,
                'deadline_status': meta_dl[0] if len(meta_dl) == 2 else None,
                'deadline': meta_dl[1] if len(meta_dl) == 2 else meta_dl[0],
                'publish_cost': cols[7].text,
                'branch': cols[8].text,
                'call_number': cols[9].text
            }
            books.append(book)
        return books

    def get_bowrrow_history(self, res):
        if not self.is_login:
            raise NotLoginException
        try:
            soup = get_page(res['status']['借閱歷史清單'][1])
            rows = soup.find('table', attrs={'cellspacing': '2', 'border': '0'}).find_all('tr')[1:]
        except AttributeError:
            return []
        books = []
        for row in rows:
            cols = [e for e in row.children if str(e).strip()]
            meta_dl = re.findall('(.*?)(\d+)', cols[4].text)[0]
            book = {
                'link': cols[0].find('a').attrs.get('href'),
                'author': cols[1].text,
                'title': cols[2].text.strip(' /'),
                'publish_year': cols[3].text,
                'deadline_status': meta_dl[0] if len(meta_dl) == 2 else None,
                'deadline': meta_dl[1] if len(meta_dl) == 2 else meta_dl[0],
                'borrow_time': cols[6].text + ' ' + re.findall('>(.*?)<', str(cols[7]))[0],
                'branch': cols[8].text
            }
            books.append(book)
        return books

    def get_current_reserve(self):
        pass

    def get_hold_reserve(self):
        pass

    def get_reserve_history(self, res):
        if not self.is_login:
            raise NotLoginException
        try:
            soup = get_page(res['status']['預約歷史清單'][1])
            rows = soup.find('table', attrs={'cellspacing': '2', 'border': '0'}).find_all('tr')[1:]
        except AttributeError:
            return []
        books = []
        for row in rows:
            cols = [e for e in row.children if str(e).strip()]
            book = {
                'link': cols[0].find('a').attrs.get('href'),
                'author': cols[1].text,
                'title': cols[2].text.strip(' /'),
                'publish_year': cols[3].text,
                'history_date': cols[4].text,
                'booking_date': cols[5].text,
                'booking_valid': cols[6].text,
                'book_return': cols[7].text,
                'branch': cols[8].text,
                'call_number': cols[9].text,
                'branch_take': cols[10].text,
                'book_status': cols[11].text
            }
            books.append(book)
        return books


class NotLoginException(Exception):
    pass


class UserPayload:

    def __init__(self, account, password):
        self.account = account
        self.password = password

    def to_dict(self):
        return {
            'bor_id': self.account,
            'bor_verification': self.password,
            'func': 'login',
            'ssl_flag': 'Y',
        }
