import os
import json

from nthu_library import NTHULibrary, timeit
from nthu_library.user import Account

__author__ = 'salas'


function_doc = """
    'personal': get_personal_info,
    'new': get_newest_books,
    'top': get_top_circulations,
    'lost': get_lost,
"""


def get_newest_books(lib, **kwargs):
    """
        :param lang: default is `None` to get both languages,
                     'en' for English; or 'zh' for Chinese
    """
    return lib.get_newest_books(**kwargs)


def get_top_circulations(lib, **kwargs):
    """
        :param year: 4-digit number
        :param type: 'loaned' or 'reserved'
    """
    return lib.get_top_circulated_materials(**kwargs)


def get_personal_info(lib):
    result = lib.get_info()
    info = {
        'personal': result,
        '借閱歷史': lib.get_borrow_history(result),
        '借閱中': lib.get_current_borrow(result),
        '預約紀錄': lib.get_reserve_history(result),
    }
    return info


def get_lost(library):
    return library.get_lost()


def welcome():
    id = os.getenv('NTHU_LIBRARY_ID') or input('ID: ')
    pwd = os.getenv('NTHU_LIBRARY_PWD') or input('PWD: ')
    print(function_doc)
    return id, pwd


@timeit
def start(instr, library):
    results = funcs[instr](library)
    dump(results)


def dump(results):
    with open('my-library-data.json', 'w', encoding='utf8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False, sort_keys=True)


''' functions eval() from doc string '''
funcs = eval('{%s}' % ''.join(function_doc.split()))


if __name__ == '__main__':

    account, pwd = welcome()
    library = NTHULibrary(Account(account, pwd))

    start('personal', library)
    start('top', library)
    start('new', library)
    start('lost', library)
