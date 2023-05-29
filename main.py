# -*- coding: UTF-8 -*-

import requests
import json
import itertools
from file_manager import Settings, save_file

from bs_interface import NoticePage, Person
from pathlib import Path


def get_notices(url='', notice_type='', nation='', gender='', age='', keyword='', request='', limit='') -> (dict, int):
    """
    Формирует словарь Превьюшек с базовыми данными для всех Персон, подходящих под фильтр.
    :param url: api-ссылка
    :param notice_type: `red` или `yellow`
    :param nation: ID Гражданства. Доступный список получаем непосредственно из HTML страницы.
    :param gender: ID Пола. Доступный список получаем непосредственно из HTML страницы.
    :param age: Возраст для фильтрации. Используем одно значения для минимального и максимального значения.
    :param keyword: Уточняющее слово, которое позволяет сузить выборку. Используем его при выдаче более 159 результатов.
    :param request: Готовый запрос с фильтрами и указанием страницы выдачи. Используем его при рекурсивном обходе.
    :param limit: Количество результатов выдачи на одну страницу.
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
                  f'ageMin={age}&ageMax={age}&' \
                  f'resultPerPage={limit}&freeText={keyword}'
    print(f'Request: {request}')
    response = requests.get(url=request)

    # TODO - обработать все прочие запросы. Возможно, добавить несколько попыток при получении 4** и 5** ошибок.
    if response.status_code == 200:  # Для простоты игнорируем другие статусы. По-уму их тоже нужно обработать
        output_dict = response.json()   # Метод .json сразу же возвращает Словарь вместо json-Сроки.

        if output_dict and int(output_dict['total']) > 0:  # Проверяем что результат не пуст и `total` больше `0`
            total = int(output_dict['total'])

            for notice in output_dict['_embedded']['notices']:
                # Собираем все превью персон в словарь. Ключом выступает уникальный идентификатор Запроса
                notices[notice['entity_id']] = notice

            next_page = output_dict['_links'].get('next')     # Ищем ссылку на следующую страницу выдачи, `default=None`
            if next_page:
                # У последней страницы нет ссылки на следующую страницу.
                # TODO - заменить предварительное сохранение и проверку "истинности" результата на обработку ошибок сети
                # Рекурсивно проходим по всем доступным страницам выдачи, обновляя словарь Превьюшек персон ("Нотисов")
                # TODO - больше не нужно, т.к. забираем всю доступную выдачу одним запросом без разбивки на страницы
                next_page_response, total = get_notices(request=next_page['href'])
                if next_page_response:       # Если результат не пуст (а он не должен быть пуст, если сеть доступна),
                    notices.update(next_page_response)   # то расширяем словарь "нотисов".

    return notices, total  # Пустой словарь тоже обработается без ошибок как в рекурсии, так и в вызывающем коде


if __name__ == '__main__':
    settings = Settings()
    print(f"Гражданство: {settings.nations}\n"
          f"Пол: {settings.genders}\n"
          f"Минимальный возраст: {settings.min_age}\n"
          f"Максимальный возраст: {settings.max_age}\n")

    for page_id, page_url in settings.search_pages_urls.items():
        """
        Главный цикл, который проходит по списку ключей поисковых страниц: `red`, `yellow`.
        Если в задаче появятся другие типы, вроде `purple`, `blue` - то их добавление ограничивается файлом настроек.
        """
        if settings.search_pages_id and page_id not in settings.search_pages_id:
            # Если параметр заполнен И текущий `page_id` НЕ содержится в параметре - то пропускаем этот тип страниц.
            continue
        page_object = NoticePage(url=page_url)      # Создаем объект поисковой страницы нужного типа.

        print(f'Page `{page_id}` get_status: {page_object.get_status()}')
        '''
        Использовать параметры объекта настроек нагляднее, но перехватить ошибки битого файла настроек проще
        с использованием словаря параметров: nations = settings.data.get('nations', page_object.nationalities)
        или же перехватывать ошибки с присвоением: nations = getattr(settings, 'nations', page_object.nationalities)
        '''
        # Если фильтры заданы при запуске - используем их. Иначе, используем все доступные варианты со страницы.
        # Используем автодополнение IDE-шки вместо `защиты от дурака` в виде проверки на существование параметра.
        nations = settings.nations if settings.nations else page_object.nationalities
        genders = settings.genders if settings.genders else page_object.genders

        for nation, gender, age in itertools.product(nations, genders,
                                                     range(settings.min_age, settings.max_age+1)):
            '''
            Цикл по всем вариациям фильтров в заданных пределах. Сохраняем результаты в промежуточный словарь.
            Это позволит избавиться от неизбежно возникающих дублей, связанных с соответствием одной персоны
            нескольким словарным ключам (где они используются для поиска).
            '''
            # Предварительно сохраняем данные в словарь, чтобы исключить дубли, которые могут образоваться после
            # применения запросов с ключами. Уже после передаем словарь в функцию, которая вытаскивает
            # более полные сведения по запросу
            # Ключ - ID уведомления, значение - json
            result_notices = {}  # Тут копятся краткие сведения всех найденных персон для текущего запроса.

            # Итерируемся по всем комбинациям фильтров в пределах заданного диапазона возрастов
            if nation not in page_object.nationalities or gender not in page_object.genders:
                # Если задано несуществующее значение Гражданства или Пола, то пропускаем итерацию
                continue

            # Получаем все результаты по запросу и их общее количество
            search_notices, notices_total = get_notices(url=settings.request_url, notice_type=page_id,
                                                        nation=nation, gender=gender, age=age,
                                                        limit=settings.notices_limit)
            result_notices.update(search_notices)

            if notices_total >= settings.notices_limit:
                """
                В случае, если запрос без ключа дает нам больше 160 результатов, мы создаем дополнительные запросы
                ключами и пересобираем данные уже по ним. Результатом является словарь - это избавит от дублей.
                """
                for keyword in settings.keywords[page_id]:
                    print(f'Using the key `{keyword}` for request')
                    search_notices, _ = get_notices(url=settings.request_url, notice_type=page_id,
                                                    nation=nation, gender=gender, age=age, keyword=keyword)
                    result_notices.update(search_notices)

            print(json.dumps(result_notices, indent=4))
            print(f'Total notices in Response: {notices_total}')
            print(f'Total notices in Result: {len(result_notices)}')

            for notice_id, notice_preview_json in result_notices.items():
                # Теперь проходим по созданному словарю, забираем айдишники каждой Персоны и содержимое его Превью
                person_detail_url = notice_preview_json['_links']['self']['href']
                images_url = notice_preview_json['_links']['images']['href']

                person = Person(person_detail_url=person_detail_url, images_url=images_url)
                # Генерим ссылку для выгрузки данных формата 'result/red/Zimbabwe/1990-8402/detail.json'
                person_result_path = Path(settings.result_dir,
                                          page_id,
                                          page_object.nationalities[nation],
                                          person.person_id)
                save_file(file_path=Path(person_result_path, 'detail.json'), file_data=person.detail_data)

                # Выгружаем все фото в папку Персоны
                for image_name, image_raw in person.images.items():
                    save_file(file_path=Path(person_result_path, image_name), file_data=image_raw)
