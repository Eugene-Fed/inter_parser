# -*- coding: UTF-8 -*-

import requests
import json
import time
import re
import itertools
import imghdr
import file_manager as fm

from bs_interface import NoticePage, Person
from argparse import ArgumentParser
from pathlib import Path
from datetime import datetime
from argparse import ArgumentParser

YELLOW_PAGES_URL = r'https://www.interpol.int/How-we-work/Notices/View-Red-Notices'
RED_PAGES_URL = r'https://www.interpol.int/How-we-work/Notices/View-Yellow-Notices'
REQUEST_URL = r'https://ws-public.interpol.int/notices/v1/'
NATIONS = []      # Фильтр искомых национальностей. Если пуст - собираем все возможные
GENDERS = ['M', 'F']
MIN_AGE = 0             # Фильтр возраста в диапазоне 0..120
MAX_AGE = 120           # TODO - принимать как параметр при запуске кода
NOTICES_LIMIT = 160     # Максимальное количество позиций, которые выдает сайт по отдельному запросу
# Используем ключевые запросы для уточнения выдачи в том случае, когда по фильтру возвращается более 159 результатов
# Используем `нормализованные` ключи, т.к. они прекрасно работают
KEYWORDS = {'red': ['armed', 'ammunition', 'crime', 'drug', 'encroachment', 'extremist', 'explosive',
                    'hooliganism', 'illegal', 'injury', 'federal', 'firearms', 'murder', 'viol', 'death', 'sexual',
                    'passport', 'stealing', 'terror', 'narcotic', 'weapon', 'rape', 'assault',
                    'infanticidio', 'femicidio', 'homicide', 'extorsion', 'criminal', 'sabotag', 'blackmail'],
            'yellow': []}     # Для Жёлтых страниц - поле ключевиков не дает результатов на сайте, т.к. нет описаний


def get_notices(url='', notice_type='', nation='', gender='', age='', keyword='', request='') -> (dict, int):
    """
    Формирует словарь Превьюшек с базовыми данными для всех Персон, подходящих под фильтр.
    :param url: api-ссылка
    :param notice_type: `red` или `yellow`
    :param nation: ID Гражданства. Доступный список получаем непосредственно из HTML страницы.
    :param gender: ID Пола. Доступный список получаем непосредственно из HTML страницы.
    :param age: Возраст для фильтрации. Используем одно значения для минимального и максимального значения.
    :param keyword: Уточняющее слово, которое позволяет сузить выборку. Используем его при выдаче более 159 результатов.
    :param request: Готовый запрос с фильтрами и указанием страницы выдачи. Используем его при рекурсивном обходе.
    :return: Возвращаем словарь и целое число. Словарь: Ключ - `entity_id`,
    Значение - Словарь с краткими сведениями о найденной персоне. Из него получаем, в том числе,
    ссылку на фото и запрос детальной информации.
    Целое число - общее количество результатов по запросу.
    """
    notices = {}        # Словарь, который хранит результаты выдачи
    total = 0           # Общее количество результатов в выдаче. Забираем его параметров выдачи.
    if not request:
        # Если нам не передан готовый реквест, значит собираем его из параметров
        request = f'{url}{notice_type}?' \
                  f'nationality={nation}&' \
                  f'sexId={gender}&' \
                  f'ageMin={age}&ageMax={age}&freeText={keyword}'
    print(f'Request: {request}')
    response = requests.get(url=request)

    # TODO - обработать все прочие запросы. Возможно, добавить несколько попыток при получении 4** и 5** ошибок.
    if response.status_code == 200:  # Для простоты игнорируем другие статусы. По-уму их тоже нужно обработать
        # output_json = response.json()
        output_dict = response.json()   # Метод .json сразу же возвращает Словарь вместо json-Сроки.

        # if output_json and int(output_json['total']) > 0:
        if output_dict and int(output_dict['total']) > 0:  # Проверяем что результат не пуст и `total` больше `0`
            # output_dict = json.loads(output_json)       # Преобразуем в словарь для доступа к питонским методам
            total = int(output_dict['total'])

            for notice in output_dict['_embedded']['notices']:
                # Собираем все превью персон в словарь. Ключом выступает уникальный идентификатор Запроса
                notices[notice['entity_id']] = notice

            next_page = output_dict['_links'].get('next')   # default=None. Пытаемся найти ссылку на следующую страницу
            if next_page:
                # Рекурсивно проходим по всем доступным страницам выдачи, обновляя словарь Превьюшек персон ("Нотисов")
                # TODO - заменить предварительное сохранение и проверку "истинности" результата на обработку ошибок сети
                next_page_response, total = get_notices(request=next_page['href'])
                if next_page_response:       # Если результат не пуст (а он не должен быть пуст, если сеть доступна),
                    notices.update(next_page_response)   # то расширяем словарь "нотисов".

    return notices, total  # Пустой словарь тоже обработается без ошибок как в рекурсии, так и в вызывающем коде


if __name__ == '__main__':
    search_pages = {       # Если появятся еще и `зеленые`, `фиолетовые` и прочие страницы - мы просто добавим их здесь
        'red': NoticePage(url=RED_PAGES_URL),
        'yellow': NoticePage(url=YELLOW_PAGES_URL)
    }
    # search_response = {}  # Тут хранятся результаты запросов по всем вариациям фильтров. Ключ - параметры фильтра
    # Предварительно сохраняем данные в словарь, чтобы исключить дубли, которые могут образоваться после применения
    # запросов с ключами. Уже после передаем словарь в функцию, которая вытаскивает более полные сведения по запросу

    for page_id, page_object in search_pages.items():
        """Цикл по всем заданным поисковым страницам: красные и желтые"""
        print(f'Page `{page_id}` get_status: {page_object.get_status()}')

        result_notices = {}  # Тут копятся краткие сведения всех найденных персон для текущего запроса.
        # Ключ - ID уведомления, значение - json

        # Если фильтры заданы при запуске - используем их. Иначе, используем все доступные варианты со страницы
        # TODO - переписать под использование параметров запуска вместо констант
        nations = NATIONS if NATIONS else page_object.nationalities
        genders = GENDERS if GENDERS else page_object.genders

        for nation, gender, age in itertools.product(nations, genders, range(MIN_AGE, MAX_AGE + 1)):
            # Цикл по всем вариациям фильтров в заданных пределах. Сохраняем результаты в промежуточный словарь.
            # Это позволит избавиться от неизбежно возникающих дублей, связанных с соответствием одной персоны
            # нескольким словарным ключам (где они используются для поиска).
            # result_notices = {}  # Тут копятся краткие сведения всех найденных персон для текущего запроса.
            # Итерируемся по всем комбинациям фильтров в пределах заданного диапазона возрастов
            if nation not in page_object.nationalities or gender not in page_object.genders:
                # "Защита от дурака" - если задано несуществующее значение Гендера или Нации, то пропускаем итерацию
                continue

            # Получаем все результаты по запросу и их общее количество
            search_notices, notices_total = get_notices(url=REQUEST_URL, notice_type=page_id,
                                                        nation=nation, gender=gender, age=age)
            result_notices.update(search_notices)

            if notices_total >= NOTICES_LIMIT:      # Если количество результатов равно 160, то пробуем уточнить запрос
                for keyword in KEYWORDS[page_id]:
                    print(f'Use key `{keyword}` for request')
                    """
                    В случае, если запрос без ключа дает нам больше 160 результатов, мы создаем дополнительные запросы
                    ключами и пересобираем данные уже по ним. Результатом является словарь - это избавит от дублей.
                    """
                    search_notices, _ = get_notices(url=REQUEST_URL, notice_type=page_id,
                                                    nation=nation, gender=gender, age=age, keyword=keyword)
                    result_notices.update(search_notices)

            print(f'Total notices in Response: {notices_total}')
            print(f'Total notices in Result: {len(result_notices)}')
            # search_results[(page_id, nation, gender, age)] = SearchResponse(url=REQUEST_URL, notice_type=page_id,
            #                                                                nation=nation, gender=gender, age=age)()
        # result = json.dumps(result_notices, indent=4)
        print(json.dumps(result_notices, indent=4))
        # print(f'Total notices in Response: {notices_total}')
        # print(f'Total notices in Result: {len(result_notices)}')

        for notice_id, notice_preview_json in result_notices.items():
            # Теперь проходим по созданному словарю, забираем айдишники каждой Персоны и содержимое его Превью
            person_detail_url = notice_preview_json['_links']['self']['href']
            images_url = notice_preview_json['_links']['images']['href']

            person = Person(person_detail_url=person_detail_url, images_url=images_url)
            # Генерим ссылку для выгрузки данных формата 'result/red/2023-8402/detail.json'
            person_result_path = Path(fm.RESULT_DIR, page_id, person.person_id)
            fm.save_file(file_path=Path(person_result_path, 'detail.json'), file_data=person.detail_data)

            # Выгружаем все фото в папку Персоны
            for image_name, image_raw in person.images.items():
                fm.save_file(file_path=Path(person_result_path, image_name), file_data=image_raw)
