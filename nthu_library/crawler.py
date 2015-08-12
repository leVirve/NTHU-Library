from urllib.parse import urljoin

import nthu_library.static_urls as NTHULibraryUrl
from nthu_library.tools import get_page, get_pages, build_soup, post_page

__author__ = 'salas'


def get_circulation_links():
    return [
        ({'text': a.text, 'href': a.get('href')},
         urljoin(NTHULibraryUrl.top_circulations, a.get('href')))
        for resp in get_pages([
            NTHULibraryUrl.top_circulations,
            NTHULibraryUrl.top_circulations_bc2007])
        for a in build_soup(resp).find(id='cwrp').find_all('a')
    ]


def crawl_top_circulations(query):
    results = dict()
    for content in get_pages(query):
        table = build_soup(content).find('table', 'listview')
        books = list()
        for row in table.find_all('tr')[1:]:
            try:
                rk, title, ref, cnt = row.findChildren()
            except ValueError:
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


def crawl_lost_objects(data):
    soup = post_page(NTHULibraryUrl.lost_found_url, data=data)
    lost_items = list()
    for item in build_soup(soup).select('table > tr')[1:]:
        lost_items.append({
            'id': item.select('td:nth-of-type(1)')[0].text,
            'time': item.select('td:nth-of-type(2)')[0].text,
            'place': item.select('td:nth-of-type(3)')[0].text,
            'description': item.select('td:nth-of-type(4)')[0].text,
        })
    return lost_items
