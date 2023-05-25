import requests
import json
import time
import re
import itertools

from bs_interface import NoticePage
from argparse import ArgumentParser
from pathlib import Path
from datetime import datetime
from argparse import ArgumentParser

YELLOW_PAGES_URL = r'https://www.interpol.int/How-we-work/Notices/View-Red-Notices'
RED_PAGES_URL = r'https://www.interpol.int/How-we-work/Notices/View-Yellow-Notices'
NATIONALITIES = ['AF', 'AS']      # Фильтр искомых национальностей. Если пуст - собираем все возможные
GENDERS = []
MIN_AGE = 22             # Фильтр возраста в диапазоне 0..120
MAX_AGE = 22           # TODO - принимать как параметр при запуске кода


if __name__ == '__main__':
    search_pages = {       # Если появятся еще и `зеленые`, `фиолетовые` и прочие страницы - мы просто добавим их здесь
        'red': NoticePage(url=RED_PAGES_URL),
        'yellow': NoticePage(url=YELLOW_PAGES_URL)
    }
    search_results = {}     # Тут хранятся результаты запросов по всем вариациям фильтров. Ключ - параметры фильтра
    search_persons = {}     # Тут хранятся все найденные персоны. Ключ - ID `уведомления`, значение - Объект персоны

    for page_id, page_object in search_pages.items():
        print(f'Page `{page_id}` get_status: {page_object.get_status()}')
        print(page_object())

        # Если фильтры заданы при запуске - используем их. Иначе, используем все доступные варианты со страницы
        # TODO - переписать под использование параметров запуска вместо констант
        nationalities = NATIONALITIES if NATIONALITIES else page_object.nationalities
        genders = GENDERS if GENDERS else page_object.genders

        for nation, gender, age in itertools.product(nationalities, genders, range(MIN_AGE, MAX_AGE + 1)):
            """
            Создаем итератор по всем вариациям фильтров в пределах заданного диапазона возрастов
            """
            if nation not in page_object.nationalities or gender not in page_object.genders:
                # "Защита от дурака" - если задано несуществующее значение Гендера или Нации, то пропускаем итерацию
                continue
            print(f'Nation: {nation}, Gender: {gender}, Age: {age}')