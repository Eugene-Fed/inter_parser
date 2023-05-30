# -*- coding: UTF-8 -*-

import requests
import json
import itertools
from file_manager import Settings, save_file

from bs_interface import NoticePage, PersonDetail, PersonPreview
from pathlib import Path


def get_notices(url='', notice_type='', nation='', gender='', keyword='', request='', limit=0,
                age=0, min_age=0, max_age=0) -> dict:
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
    total = 0           # DEPRECATED: Общее количество результатов в выдаче. Забираем его атрибутов параметров выдачи.
    if not request:     # Этот `if` потерял актуальность, т.к. больше не используем параметр `request`.
        # Если нам не передан готовый реквест, значит собираем его из параметров
        request = f'{url}{notice_type}?' \
                  f'nationality={nation}&' \
                  f'sexId={gender}&' \
                  f'ageMin={min_age}&ageMax={max_age}&' \
                  f'resultPerPage={limit}'      # &freeText={keyword} - Ключевой запрос больше не используем.
    print(f'Request: {request}')
    response = requests.get(url=request)

    # TODO - обработать все прочие запросы. Возможно, добавить несколько попыток при получении 4** и 5** ошибок.
    '''
    if response.status_code == 200:  # Для простоты игнорируем другие статусы. По-уму их тоже нужно обработать
        output_dict = response.json()   # Метод .json сразу же возвращает Словарь вместо json-Сроки.
    '''
    output_dict = response.json() if response.status_code == 200 else None      # Сократил вложенность `иф-элсов`

    if output_dict and int(output_dict['total']) > 0:  # Проверяем что результат не пуст и `total` больше `0`
        total = int(output_dict['total'])

        if total >= limit and min_age != max_age:
            """
            Если в выдаче 160 результатов и более, значит фильтр слишком широк, и нужно его уточнить.
            Для этого разбиваем возрастной диапазон на 2 половины и рекурсивно вызываем метод по двум новым диапазонам.
            """
            [lower_min_age, lower_max_age], [upper_min_age, upper_max_age] = get_age_ranges(min_age, max_age)

            notices.update(get_notices(url=url, notice_type=notice_type, nation=nation, gender=gender, keyword=keyword,
                                       limit=limit, min_age=lower_min_age, max_age=lower_max_age))
            notices.update(get_notices(url=url, notice_type=notice_type, nation=nation, gender=gender, keyword=keyword,
                                       limit=limit, min_age=upper_min_age, max_age=upper_max_age))
        else:
            """
            Если в выдаче меньше 160 результатов ИЛИ минимальный возраст равен максимальному -
            то нет необходимости дальше углубляться в запросах, т.к. мы достигли `листа` в нашем графе.
            """
            for notice in output_dict['_embedded']['notices']:
                # Собираем все превью персон в словарь. Ключом выступает уникальный идентификатор Запроса
                notices[notice['entity_id']] = notice

        """
        По сути мы больше не нуждаемся в этом блоке кода, т.к. забираем всю выдачу сразу без разбивки на страницы -
        `next_page` всегда будет `None`. Однако оставлю его "прозапас" на случай непредвиденных задач.
        """
        next_page = output_dict['_links'].get('next')     # Ищем ссылку на следующую страницу выдачи, `default=None`.
        if next_page:
            # У последней страницы нет ссылки на следующую страницу.
            # TODO - заменить предварительное сохранение и проверку "истинности" результата на обработку ошибок сети
            # Рекурсивно проходим по всем доступным страницам выдачи, обновляя словарь Превьюшек персон ("Нотисов").
            # TODO - больше не нужно, т.к. забираем всю доступную выдачу одним запросом без разбивки на страницы
            next_page_response, total = get_notices(request=next_page['href'])
            if next_page_response:       # Если результат не пуст (а он не должен быть пуст, если сеть доступна),
                notices.update(next_page_response)   # то расширяем словарь "нотисов".

    return notices  # Пустой словарь тоже обработается без ошибок как в рекурсии, так и в вызывающем коде


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
        nations = settings.nations if settings.nations else page_object.nationalities
        genders = settings.genders if settings.genders else page_object.genders

        # for nation, gender, age in itertools.product(nations, genders, range(settings.min_age, settings.max_age+1)):
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
            search_notices = get_notices(url=settings.request_url, notice_type=page_id,
                                         nation=nation, gender=gender,
                                         limit=settings.notices_limit,
                                         min_age=settings.min_age, max_age=settings.max_age)

            # if notices_total < 160:
            result_notices.update(search_notices)

            # TODO - оценить необходимость доп. фильтрации по ключевым запросам.
            '''
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
            '''

            # print(json.dumps(result_notices, indent=4))
            # print(f'Total notices in Response: {notices_total}')
            print(f'Total notices in Result: {len(result_notices)}')

            for notice_id, notice_preview_json in result_notices.items():
                # Теперь проходим по созданному словарю, забираем айдишники каждой Персоны и содержимое его Превью
                # Генерим ссылку для выгрузки данных формата 'result/red/Zimbabwe/1990-8402/'. Имя файла добавим позже.
                person_result_path = Path(settings.result_dir,
                                          page_id,
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
