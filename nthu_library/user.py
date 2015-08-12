import re
from urllib.parse import urljoin

import nthu_library.static_urls as NTHULibraryUrl
from nthu_library.tools import get_page, post_page, get_rss

__author__ = 'salas'


class NotLoginException(Exception):
    pass


class Account:

    def __init__(self, username, password):
        self.username = username
        self.password = password
        self.home_url = ''
        self.session_url = ''
        self.is_login = False

    def login(self):
        soup = get_page(urljoin(self.home_url, '?func=file&file_name=login1'))
        login_url = soup.find('form').attrs.get('action')

        resp = post_page(login_url, data=self.to_dict())
        self.is_login = '您已登入' in resp.text
        self.session_url = resp.url
        return self.is_login

    def to_dict(self):
        return {
            'bor_id': self.username,
            'bor_verification': self.password,
            'func': 'login',
            'ssl_flag': 'Y',
        }


class User:

    def __init__(self, parent, account):
        self.parent = parent
        self.account = account
        self.is_login = self.init_account()

    def init_account(self):
        self.account.home_url = NTHULibraryUrl.info_system
        return self.account.login()

    def get_info(self):
        if not self.is_login:
            raise NotLoginException
        soup = get_page(urljoin(self.account.session_url, '?func=BOR-INFO'))

        return self._parse(soup)

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

    def get_current_borrow(self, res):
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

    def get_borrow_history(self, res):
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