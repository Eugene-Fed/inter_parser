# -*- coding: UTF-8 -*-

import requests
import json
import itertools
import asyncio
import aiohttp
import random
from file_manager import Settings, save_file

from bs_interface import NoticePage, PersonDetail, PersonPreview, get_async_response
from pathlib import Path


async def get_notices(url='', notice_type='', nation='', gender='', keyword='', request='', limit=0,
                      min_age=0, max_age=0) -> dict:
    """
    Формирует словарь Превьюшек с базовыми данными для всех Персон, подходящих под фильтр.

    :param url: api-ссылка
    :param notice_type: `red` или `yellow`
    :param nation: ID Гражданства. Доступный список получаем непосредственно из HTML страницы.
    :param gender: ID Пола. Доступный список получаем непосредственно из HTML страницы.
    :param keyword: DEPRECATED. Уточняющее слово, которое позволяет сузить выборку.
    :param request: DEPRECATED. Готовый запрос с фильтрами и указанием страницы выдачи.
    :param limit: Количество результатов выдачи на одну страницу.
    :param min_age: Минимальный возраст выборки.
    :param max_age: Максимальный возраст выборки.
    :return: {'2023/4812':
    {'person_preview': 'person preview json', 'person_nation': 'nation id', 'notice_type': 'red'}}
    """
    min_age = int(min(min_age, max_age))
    max_age = int(max(min_age, max_age))
    notices = {}        # Словарь, который хранит результаты выдачи
    output_dict = {}
    # if not request:     # Этот `if` потерял актуальность, т.к. больше не используем параметр `request`.
    # Если нам не передан готовый реквест, значит собираем его из параметров
    request = f'{url}{notice_type}?' \
              f'nationality={nation}&' \
              f'sexId={gender}&' \
              f'ageMin={min_age}&ageMax={max_age}&' \
              f'resultPerPage={limit}'      # &freeText={keyword} - Ключевой запрос больше не используем.
    '''
    response = requests.get(url=request)
    # TODO - обработать все прочие запросы. Возможно, добавить несколько попыток при получении 4** и 5** ошибок.
    output_dict = response.json() if response.status_code == 200 else None
    '''

    # Отправляем запросы раз в 100 мсек в течение заданного в настройках времени, чтобы снизить нагрузку на сервер
    response = await get_async_response(request,
                                        sleep=random.randint(1, settings.request_dist_time/settings.request_freq)
                                              * settings.request_freq)
    response_status = response.get('status')
    print(f'Request: {request} status: {response_status}')

    if response_status == 200:
        output_dict = await response.get('json')

    total = int(output_dict.get('total', 0))    # Если `total` == 0, значит результат запроса пуст
    if output_dict and total > 0:  # Проверяем что результат не пуст и `total` больше `0`

        if total >= limit and min_age != max_age:
            """
            Если в выдаче 160 результатов и более, значит фильтр слишком широк, и нужно его уточнить.
            Для этого разбиваем возрастной диапазон на 2 половины и рекурсивно вызываем метод по двум новым диапазонам.
            """
            [lower_min_age, lower_max_age], [upper_min_age, upper_max_age] = get_age_ranges(min_age, max_age)

            # Асинхронный вариант рекурсивного обхода
            notice_lower_age = {
                'url': url,
                'notice_type': notice_type,
                'nation': nation,
                'gender': gender,
                'keyword': keyword,
                'limit': limit,
                'min_age': lower_min_age,
                'max_age': lower_max_age
            }
            notice_upper_age = notice_lower_age.copy()
            notice_upper_age.update({'min_age': upper_min_age, 'max_age': upper_max_age})
            tasks = [asyncio.create_task(get_notices(**notice_lower_age)),
                     asyncio.create_task(get_notices(**notice_upper_age))]
            done, _ = await asyncio.wait(tasks)

            # alt
            '''
            coros = [get_notices(**notice_lower_age), get_notices(**notice_upper_age)]
            results = await asyncio.gather(*coros)
            # async for result in asyncio.gather(coros, return_exceptions=False):
            for result in results:
                notices.update(result)
            '''

            for future in done:
                notices.update(future.result())

        else:
            """
            Если в выдаче меньше 160 результатов ИЛИ минимальный возраст равен максимальному -
            то нет необходимости дальше углубляться в запросах, т.к. мы достигли `листа` в нашем графе.
            """
            for notice in output_dict['_embedded']['notices']:
                # Собираем все превью персон в словарь. Ключом выступает уникальный идентификатор Запроса
                # notices[notice['entity_id']] = notice
                notices[notice['entity_id']] = {'person_preview': notice,
                                                'person_nation': nation,
                                                'notice_type': notice_type}

    return notices  # Пустой словарь тоже обработается без ошибок как в рекурсии, так и в вызывающем коде


async def get_person_data(person_preview_json) -> PersonPreview:
    """
    Получаем превью/детальные данные персоны, а также данные всех фотографий.
    :param person_preview_json: Словарь (json объект), который содержит превью данных персоны.
    :return: Объект, содержащий уже загруженные данные и изображения.
    """
    # TODO - передавать `settings` параметром, вместо использования глобала
    if settings.preview_only:
        person = PersonPreview(person_preview_data=person_preview_json)

    else:
        person = PersonDetail(person_preview_data=person_preview_json)
        person_detail = await person.get_detail_json()

    # Отправляем запросы раз в 100 мсек в течение заданного в настройках времени, чтобы снизить нагрузку на сервер
    # response = await get_async_response(request,
    #                                     sleep=random.randint(1, settings.request_dist_time) * settings.request_freq)
    # person_images = person.get_images()     # сохраняем картинки последовательно, иначе сервер выдает 4хх ошибки
    '''_ = await person.get_async_images(sleep=random.randint(1, settings.request_dist_time/settings.request_freq)
                                        * settings.request_freq)'''
    _ = await asyncio.gather(person.get_async_images(sleep=random.randint(1,
                                                                          settings.request_dist_time
                                                                          / settings.request_freq)
                                                           * settings.request_freq))
    return person


def get_age_ranges(min_age: int, max_age: int) -> list:
    """
    Разбивка диапазона возрастов на два
    :param min_age:
    :param max_age:
    :return:
    """
    if int(min_age) != int(max_age):
        diapason = int(max(min_age, max_age)) - int(min(min_age, max_age))        # Защита от дурака
        lower_max = diapason // 2 + min_age
        return [[min_age, lower_max], [lower_max+1, max_age]]
    else:
        return []       # Если поймаем непредвиденный случай - то получим ошибку при распаковке пустого словаря.


async def main_coro(url, page_type, notices_limit, min_age, max_age, nations, genders) -> None:
    """
    Корутина, которая запускает поиск по всем доступным фильтрам с рекурсивным уточнением возраста по необходимости
    :param url: Домен API
    :param page_type: На выбор два варианта: `red` и `yellow`
    :param notices_limit: Ограничение на количество результатов в выдаче. По-умолчанию - 160.
    :param min_age: Предварительный фильтр по минимальному возрасту
    :param max_age: Предварительный фильтр по максимальному возрасту
    :param nations: Список наций TODO - описать полный список в доках
    :param genders: Список гендеров ['F', 'M', 'U']
    :return:
    """
    result_notices = {}
    # Генерируем список `задач`, на основе всех доступных вариантов фильтров
    '''main_search_tasks = [asyncio.create_task(get_notices(url=url, notice_type=page_type,
                                                         nation=nation, gender=gender,
                                                         limit=notices_limit,
                                                         min_age=min_age, max_age=max_age)) for
                         nation, gender in itertools.product(nations, genders)]'''
    main_search_coros = [get_notices(url=url, notice_type=page_type,
                                     nation=nation, gender=gender,
                                     limit=notices_limit,
                                     min_age=min_age,
                                     max_age=max_age) for nation, gender in itertools.product(nations, genders)]

    '''done_search_tasks, _ = await asyncio.wait(main_search_tasks)'''
    search_results = await asyncio.gather(*main_search_coros, return_exceptions=False)

    '''Собираем базу всех возможных превью персоны прежде, чем обрабатывать ее данные. Это позволит избавиться
    от дублирующих запросов, т.к. некоторые люди попадают под разные фильтры и могут быть продублированы.
    Предварительный сбор словаря ключом которого является ID персоны - избавит нас от лишних дублирующих запросов.'''
    '''for task in done_search_tasks:
        result_notices.update(task.result())   # Асинхронно получаем общий словарь с превью по всем возможным фильтрам'''
    for result in search_results:
        result_notices.update(result)

    # Генерим список задач на основе данных по всем полученным персонам
    '''person_tasks = [asyncio.create_task(get_person_data(person_preview_json=notice_data)) for
                    notice_data in result_notices.values()]'''
    person_coros = [get_person_data(person_preview_json=notice_data) for
                    notice_data in result_notices.values()]
    # Теперь проходим по созданному словарю, забираем айдишники каждой Персоны и содержимое его Превью

    '''done_person_task, _ = await asyncio.wait(person_tasks)'''
    person_results = await asyncio.gather(*person_coros, return_exceptions=False)

    for person in person_results:
        # Генерим ссылку для выгрузки данных формата 'result/red/Zimbabwe/1990-8402/'. Имя файла добавим позже.
        person_result_path = Path(settings.result_dir,
                                  person.notice_type,
                                  page_object.nationalities[person.nation],
                                  person.preview_json['entity_id'].replace('/', '-'))
        save_file(file_path=Path(person_result_path, 'preview.json'), file_data=person.preview_json)

        # Выгружаем все фото в папку Персоны
        for image_name, image_raw in person.images.items():
            save_file(file_path=Path(person_result_path, image_name), file_data=image_raw)

    """
    for task in done_person_task:
        current_person = task.result()
        # Генерим ссылку для выгрузки данных формата 'result/red/Zimbabwe/1990-8402/'. Имя файла добавим позже.
        person_result_path = Path(settings.result_dir,
                                  current_person.notice_type,
                                  page_object.nationalities[current_person.nation],
                                  current_person.preview_json['entity_id'].replace('/', '-'))
        save_file(file_path=Path(person_result_path, 'preview.json'), file_data=current_person.preview_json)
        '''
        if hasattr(current_person, 'detail_json'):
            save_file(file_path=Path(person_result_path, 'detail.json'), file_data=person_detail)
        else:
            save_file(file_path=Path(person_result_path, 'preview.json'), file_data=current_person.preview_json)
        '''
        # Выгружаем все фото в папку Персоны
        for image_name, image_raw in current_person.images.items():
            save_file(file_path=Path(person_result_path, image_name), file_data=image_raw)
    """


if __name__ == '__main__':
    settings = Settings()
    print(f"Гражданство: {settings.nations}\n"
          f"Пол: {settings.genders}\n"
          f"Минимальный возраст: {settings.min_age}\n"
          f"Максимальный возраст: {settings.max_age}\n"
          f"Только Превью: {settings.preview_only}")

    for page_type, page_url in settings.search_pages_urls.items():
        """
        Главный цикл, который проходит по списку ключей поисковых страниц: `red`, `yellow`.
        Если в задаче появятся другие типы, вроде `purple`, `blue` - то их добавление ограничится файлом настроек.
        """
        if settings.search_pages_id and page_type not in settings.search_pages_id:
            # Если параметр заполнен И текущий `page_type` НЕ содержится в параметре - то пропускаем этот тип страниц.
            continue
        page_object = NoticePage(url=page_url)      # Создаем объект поисковой страницы нужного типа.

        print(f'Page `{page_type}` get_status: {page_object.get_status()}')
        if page_object.get_status() != 200:
            continue
        '''
        Использовать параметры объекта настроек нагляднее, но перехватить ошибки битого файла настроек проще
        с использованием словаря параметров: nations = settings.data.get('nations', page_object.nationalities)
        или же перехватывать ошибки с присвоением: nations = getattr(settings, 'nations', page_object.nationalities)
        '''
        # Если фильтры заданы при запуске - используем их. Иначе, используем все доступные варианты со страницы.
        nations = settings.nations if settings.nations else page_object.nationalities
        genders = settings.genders if settings.genders else page_object.genders

        '''
        with asyncio.Runner() as runner:
            runner.run(main_coro(url=settings.request_url, page_type=page_type,
                                          notices_limit=settings.notices_limit, min_age=settings.min_age,
                                          max_age=settings.max_age, nations=nations, genders=genders))
        '''

        asyncio.run(main=main_coro(url=settings.request_url, page_type=page_type,
                                   notices_limit=settings.notices_limit, min_age=settings.min_age,
                                   max_age=settings.max_age, nations=nations, genders=genders))
