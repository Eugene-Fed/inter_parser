# -*- coding: UTF-8 -*-

import requests
import json
import itertools
import asyncio
import aiohttp
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
    :param age: DEPRECATED. Возраст для фильтрации. Используем одно значения для минимального и максимального значения.
    :param keyword: DEPRECATED. Уточняющее слово, которое позволяет сузить выборку.
    Используем его при выдаче более 159 результатов.
    :param request: DEPRECATED. Готовый запрос с фильтрами и указанием страницы выдачи.
    Используем его при рекурсивном обходе.
    :param limit: Количество результатов выдачи на одну страницу.
    :return: Возвращаем кортеж, который содержит словарь и целое число.
    Словарь: Ключ - `entity_id`, Значение - Словарь с краткими сведениями о найденной персоне.
    Из него получаем, в том числе, ссылку на фото и запрос детальной информации.
    Целое число: общее количество результатов по запросу.
    """
    min_age = int(min(min_age, max_age))
    max_age = int(max(min_age, max_age))
    notices = {}        # Словарь, который хранит результаты выдачи
    output_dict = {}
    if not request:     # Этот `if` потерял актуальность, т.к. больше не используем параметр `request`.
        # Если нам не передан готовый реквест, значит собираем его из параметров
        request = f'{url}{notice_type}?' \
                  f'nationality={nation}&' \
                  f'sexId={gender}&' \
                  f'ageMin={min_age}&ageMax={max_age}&' \
                  f'resultPerPage={limit}'      # &freeText={keyword} - Ключевой запрос больше не используем.
    print(f'Request: {request}')
    '''
    response = requests.get(url=request)
    # TODO - обработать все прочие запросы. Возможно, добавить несколько попыток при получении 4** и 5** ошибок.
    output_dict = response.json() if response.status_code == 200 else None
    '''

    # response = requests.get(request)
    # output_dict = response.json()

    response = await get_async_response(request, sleep=1)
    response_status = response.get('status')
    if response_status == 200:
        # output_dict = await response.json()
        output_dict = await response.get('json')
    '''
    async with aiohttp.ClientSession() as session:
        async with session.get(request) as resp:
            if resp.status == 200:
                output_dict = await resp.json()
            else:
                output_dict = {}
    '''

    if output_dict and int(output_dict['total']) > 0:  # Проверяем что результат не пуст и `total` больше `0`
        total = int(output_dict['total'])

        if total >= limit and min_age != max_age:
            """
            Если в выдаче 160 результатов и более, значит фильтр слишком широк, и нужно его уточнить.
            Для этого разбиваем возрастной диапазон на 2 половины и рекурсивно вызываем метод по двум новым диапазонам.
            """
            [lower_min_age, lower_max_age], [upper_min_age, upper_max_age] = get_age_ranges(min_age, max_age)
            '''
            # Рекурсивная часть оригинального синхронного кода.
            notices.update(get_notices(url=url, notice_type=notice_type, nation=nation, gender=gender, keyword=keyword,
                                       limit=limit, min_age=lower_min_age, max_age=lower_max_age))
            notices.update(get_notices(url=url, notice_type=notice_type, nation=nation, gender=gender, keyword=keyword,
                                       limit=limit, min_age=upper_min_age, max_age=upper_max_age))
            '''

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
            # tasks = [get_notices(**notice_lower_age), get_notices(**notice_upper_age)]
            # done = await asyncio.gather(*tasks)

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


async def get_persons(page_type, person_id, person_data):
    # notice_preview_json = person_data['person_preview']
    # TODO - передавать `settings` параметом, вместо использования глобала
    # Генерим ссылку для выгрузки данных формата 'result/red/Zimbabwe/1990-8402/'. Имя файла добавим позже.
    person_result_path = Path(settings.result_dir,
                              page_type,
                              page_object.nationalities[person_data['person_nation']],
                              person_id.replace('/', '-'))

    if settings.preview_only:
        # person = PersonPreview(person_preview_data=notice_preview_json)
        person = PersonPreview(person_preview_data=person_data['person_preview'])

        # person_images = await person.get_async_thumbnail()
    else:
        # person_detail_url = notice_preview_json['_links']['self']['href']
        # images_url = notice_preview_json['_links']['images']['href']
        # person = PersonDetail(person_detail_url=person_detail_url, images_url=images_url)
        # person = PersonDetail(person_detail_url=person_data['person_preview']['_links']['self']['href'],
        #                      images_url=person_data['person_preview']['_links']['images']['href'])
        person = PersonDetail(person_preview_data=person_data['person_preview'])
        person_detail = await person.get_detail_json()

    if hasattr(person, 'detail_json'):
        save_file(file_path=Path(person_result_path, 'detail.json'), file_data=person_detail)
    else:
        save_file(file_path=Path(person_result_path, 'preview.json'), file_data=person.preview_json)

    person_images = person.get_images()     # сохраняем картинки последовательно, иначе сервер выдает 4хх ошибки
    # person_images = await person.get_async_images()     # получаем результат выполнения корутины
    # person_images = person.get_async_images() # создаем футуру - объект корутины. футура требует ожидания
    # Выгружаем все фото в папку Персоны
    # for image_name, image_raw in person.images.items():
    # _ = await person.get_async_images()
    # for image_name, image_raw in person.images.items():
    for image_name, image_raw in person_images.items():
        save_file(file_path=Path(person_result_path, image_name), file_data=image_raw)


async def async_filters_loop(url, page_type, notices_limit, min_age, max_age, nations, genders):
    result_notices = {}
    # Генерируем список `задач`, на основе всех доступных вариантов фильтров
    main_search_tasks = [asyncio.create_task(get_notices(url=url, notice_type=page_type,
                                                         nation=nation, gender=gender,
                                                         limit=notices_limit,
                                                         min_age=min_age, max_age=max_age)) for
             nation, gender in itertools.product(nations, genders)]

    done_tasks, _ = await asyncio.wait(main_search_tasks)

    for task in done_tasks:
        result_notices.update(task.result())   # Асинхронно получаем общий словарь с превью по всем возможным фильтрам

    persons = [asyncio.create_task(get_persons(page_type=page_type,
                                               person_id=notice_id, person_data=notice_data)) for
               notice_id, notice_data in result_notices.items()]
    # Теперь проходим по созданному словарю, забираем айдишники каждой Персоны и содержимое его Превью

    await asyncio.wait(persons)


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
        Если в задаче появятся другие типы, вроде `purple`, `blue` - то их добавление ограничивается файлом настроек.
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

        # for nation, gender, age in itertools.product(nations, genders, range(settings.min_age, settings.max_age+1)):
        '''
        with asyncio.Runner() as runner:
            runner.run(async_filters_loop(url=settings.request_url, page_type=page_type,
                                          notices_limit=settings.notices_limit, min_age=settings.min_age,
                                          max_age=settings.max_age, nations=nations, genders=genders))
        '''

        asyncio.run(main=async_filters_loop(url=settings.request_url, page_type=page_type,
                                            notices_limit=settings.notices_limit, min_age=settings.min_age,
                                            max_age=settings.max_age, nations=nations, genders=genders))

        """
        for nation, gender in itertools.product(nations, genders):
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
            search_notices = get_notices(url=settings.request_url, notice_type=page_type,
                                         nation=nation, gender=gender,
                                         limit=settings.notices_limit,
                                         min_age=settings.min_age, max_age=settings.max_age)
            # ioloop = asyncio.get_event_loop()
            # ioloop.run_until_complete()

            # if notices_total < 160:
            result_notices.update(search_notices)
            
            # print(json.dumps(result_notices, indent=4))
            # print(f'Total notices in Response: {notices_total}')
            print(f'Total notices in Result: {len(result_notices)}')

            for notice_id, notice_preview_json in result_notices.items():
                # Теперь проходим по созданному словарю, забираем айдишники каждой Персоны и содержимое его Превью
                # Генерим ссылку для выгрузки данных формата 'result/red/Zimbabwe/1990-8402/'. Имя файла добавим позже.
                person_result_path = Path(settings.result_dir,
                                          page_type,
                                          page_object.nationalities[nation],
                                          notice_id.replace('/', '-'))

                if settings.preview_only:
                    person = PersonPreview(person_preview_data=notice_preview_json)
                else:
                    person_detail_url = notice_preview_json['_links']['self']['href']
                    images_url = notice_preview_json['_links']['images']['href']

                    person = PersonDetail(person_detail_url=person_detail_url, images_url=images_url)

                if hasattr(person, 'detail_json'):
                    save_file(file_path=Path(person_result_path, 'detail.json'), file_data=person.detail_json)
                else:
                    save_file(file_path=Path(person_result_path, 'preview.json'), file_data=person.preview_json)

                # Выгружаем все фото в папку Персоны
                for image_name, image_raw in person.images.items():
                    save_file(file_path=Path(person_result_path, image_name), file_data=image_raw)
        """
