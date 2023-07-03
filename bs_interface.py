# -*- coding: UTF-8 -*-

import requests
import asyncio
import aiohttp
from bs4 import BeautifulSoup


class NoticePage:
    """
    Класс, определяющий все базовые данные поисковой страницы. Здесь хранятся значения фильтров, по которым
    мы будем формировать запросы по API
    """
    url = ''
    nationalities = {}
    genders = {}
    request_page = None
    parser_page = None
    total = 0

    def __init__(self, url: str):
        """
        При инициализации получаем адрес целевой страницы, с которой необходимо работать в дальнейшем.
        :param url: Строка адреса поисковой страницы
        """
        self.url = url
        self.request_page = requests.get(self.url)

        if self.request_page.status_code == 200:
            # Если страница недоступна, то не требуется ничего с ней делать
            self.parser_page = BeautifulSoup(self.request_page.text, 'html.parser')
            self.nationalities = self.get_nationalities(page=self.parser_page)
            self.genders = self.get_genders(page=self.parser_page)
            self.total = self.get_total(page=self.parser_page)

    def __call__(self):
        if self.parser_page:

            return len(self.nationalities)

        else:
            return

    def get_status(self) -> int:
        """Возвращаем статус запроса страницы"""
        return int(self.request_page.status_code)

    def get_nationalities(self, page: BeautifulSoup) -> dict:
        """
        Получаем список национальностей со страницы. Используем именно этот фильтр, т.к. он присутствует как в
        `Красных`, так и в `Желтых` страницах.
        :param page: Сюда передаем объект страницы.
        :return: Возвращаем словарь с ID национальности в кач-ве ключа и с Названием государства в качестве значения.
        """
        select = page.find('select', id='nationality')

        # TODO - переписать с использованием фильтрующей функции `select.find_all(filter_func)`
        # TODO - переписать с использованием словарного включения. P.S. или оставить как есть =)
        for option in select.find_all('option'):
            if option.attrs:  # Первый элемент пустой, поэтому его пропускаем. Нужен лишь список ID стран
                self.nationalities[option.attrs['value']] = option.string
        return self.nationalities

    def get_genders(self, page: BeautifulSoup) -> dict:
        """
        Получаем список гендеров со страницы. Забираем эти данные из блока `радио` переключателей.
        :param page: Сюда передаем объект страницы.
        :return: Возвращаем словарь с ID гендера в кач-ве ключа и Названием в кач-ве значения.
        """
        radios = page.find_all('input', attrs={'type': 'radio', 'name': 'sexId'})

        for radio in radios:
            if radio.attrs['value']:  # Первая кнопка `All` имеет пустое значение атрибута `value`, его пропускаем
                self.genders[radio.attrs['value']] = page.find('label', attrs={'for': radio.attrs['id']}).string
        return self.genders

    @staticmethod
    def get_total(page: BeautifulSoup) -> int:
        """
        Получаем общее количество персон для заданной страницы. Забираем это значения непосредственно из HTML.
        # TODO - в текущей реализации всегда выдает нулевое значение.
        # todo - Для получения реального числа необходим отправить запрос с фильтрами на все позиции.
        :param page: Объект страницы.
        :return: Общее количество персон в поиске.
        """
        return int(page.find('strong', id='totalResults').string)


class PersonPreview:
    """
    preview_json = {}
    images = {}
    """

    def __init__(self, person_preview_data: dict):
        self.preview_json = person_preview_data['person_preview']
        self.nation = person_preview_data['person_nation']
        self.notice_type = person_preview_data['notice_type']
        try:        # Когда начинают сыпаться ошибки сервера, к нам попадают пустые ответы
            self.thumbnail_url = self.preview_json['_links']['thumbnail']['href']
        except KeyError:
            self.thumbnail_url = None
        self.images = {}

    async def __call__(self):
        images = await self.get_async_images()
        return self.preview_json, images

    @staticmethod
    def get_thumbnail(url: str):
        """
        DEPRECATED
        :param url:
        :return:
        """
        response = requests.get(url)
        suffix = response.headers['content-type'].split('/')[-1]
        return {f'thumbnail.{suffix}': response.content}

    def get_images(self):
        if self.thumbnail_url:
            self.images = self.get_thumbnail(self.thumbnail_url)
        return self.images

    async def get_async_thumbnail(self, sleep=0) -> dict:
        """
        Отдельный метод для загрузки только Превью картинки на случай острой необходимости.
        :param sleep: Время ожидания перед отправкой запроса (нужно для распределения асинхронных запросов по времени).
        :return: Словарь, содержащий имя изображения и само изображение.
        """
        response = await get_async_response(url=self.thumbnail_url, sleep=sleep)
        response_status = response.get('status')    # Мы не можем использовать футуру напрямую в условии
        thumbnail = {}
        if response_status == 200:
            image_raw = response.get('content')
            suffix = response.get('headers').get('content-type').split('/')[-1]
            thumbnail[f'thumbnail.{suffix}'] = image_raw
            self.images.update(thumbnail)

        return thumbnail

    async def get_async_images(self, url='', sleep=0):
        tasks = []
        if self.thumbnail_url:
            tasks.append(asyncio.create_task(self.get_async_thumbnail(sleep=sleep)))
        if url:
            pass
        else:
            pass
        if tasks:
            done, _ = await asyncio.wait(tasks)
            for future in done:
                return future.result()


class PersonDetail(PersonPreview):
    # TODO - наследовать от `PersonPreview` (если  это имеет смысл).
    """
    detail_url = ''         # Ссылка на подробную страницу Персоны
    images_url = ''         # Запрос на получение ссылок всех фото Персоны
    person_id = ''  # Идентификатор Персоны формата `ГОД_ID`
    images = {}             # Словарь {`picture_id`: `image_raw_data`}, в котором хранятся все фото (без миниатюры).
    detail_json = {}  # json (словарь) с подробными данными Персоны
    """

    def __init__(self, person_preview_data: dict):
        # TODO - по аналогии с `PersonPreview` можно принимать лишь превью данных, и добывать ссылку на фото уже здесь.
        """
        - При инициализации или вызове можно добавить флаги `json_data = False, img = False`. Это упрощает код,
        но считается "моветоном" среди некоторых ООП-шников. На Плюсах это норм, а в Питоне считается хорошим тоном
        обрабатывать полученные объекты на основе их типов, а не вспомогательных настроечных флагов.
        - В текущей реализации нет смысла создавать новый экземпляр класса для обработки каждой Персоны,
        поэтому просто обнуляем словарь `images`, вместо вызова функции `__new__(cls):`.
        :param person_detail_url: Ссылка на детальную страницу Персоны.
        :param images_url: Ссылка на запрос фотографий Персоны.
        """
        super().__init__(person_preview_data)
        # self.person_id = ''  # Идентификатор Персоны формата `ГОД_ID`
        self.detail_json = {}  # json (словарь) с подробными данными Персоны
        self.detail_url = self.preview_json['person_preview']['_links']['self']['href']
        self.images_url = self.preview_json['person_preview']['_links']['images']['href']
        # TODO - перехватить все статусы реквестов кроме 200-го. Вероятно проще написать универсальный класс обработки

        # self.detail_json = requests.get(person_detail_url).json()
        # self.person_id = self.detail_json['entity_id'].replace('/', '-')    # Заменяем `/` на `-` для корректного пути
        '''
        # Получаем список ID и фотографии персоны
        images_json = requests.get(images_url).json()
        
        try:
            # TODO - сделать проверку на пустой ответ или коды ошибок
            for item in images_json['_embedded']['images']:
                response = requests.get(item['_links']['self']['href'])
                try:
                    suffix = response.headers['content-type'].split('/')[-1]    # Получаем расширение файла
                except Exception:
                    suffix = '.jpg'

                self.images[f"{item['picture_id']}.{suffix}"] = response.content    # Сохраняем картинку с именем
        except Exception as e:
            print(e)
        '''

    def __call__(self):
        # При вызове можно сразу же и сохранять файлы, либо прописать это отдельным методом. Либо оставить как есть =)
        return self.detail_json, self.images

    async def get_detail_json(self):
        coro = await get_async_response(url=self.detail_url)
        self.detail_json = await coro['json']
        # self.person_id = self.detail_json['entity_id'].replace('/', '-')  # Заменяем `/` на `-` для корректного пути
        return self.detail_json

    async def get_async_images(self):
        # Получаем список ID и фотографии персоны
        images_json = await get_async_response(url=self.images_url)['json']

        try:
            # TODO - сделать проверку на пустой ответ или коды ошибок
            for item in images_json['_embedded']['images']:
                response = await get_async_response(url=item['_links']['self']['href'])
                try:
                    suffix = response['headers']['content-type'].split('/')[-1]  # Получаем расширение файла
                except Exception as e:
                    print(e)
                    suffix = '.jpg'

                self.images[f"{item['picture_id']}.{suffix}"] = response['content']  # Сохраняем картинку с именем
        except Exception as e:
            print(e)
        return self.images


class AsyncRequest:
    # TODO - дописать класс для использования асинхронных запросов вместо отдельных методов, описанных ниже.
    """
    request = None
    response_json = {}
    response_headers = {}
    response_contend = None
    """

    def __init__(self, url: str, method='GET',  headers=''):
        self.url = url
        self.method = method
        self.headers = headers

    async def __call__(self):
        try:
            request = await aiohttp.request(method=self.method, url=self.url, headers=self.headers)
            self.response_json = request.json()
            self.response_contend = request.content()
            self.response_headers = request.headers
            request.close()
        except Exception as e:
            print(e)
        self.response_json = self.request.json()
        self.response_contend = self.request.content()

    async def get_request(url: str, method='GET',  headers=''):
        """
        DEPRICATED
        :param method:
        :param headers:
        :return:
        """
        try:
            request = await aiohttp.request(method=method, url=url, headers=headers)
            request.close()
        except Exception as e:
            print(e)
        return


async def get_async_response(url: str, method='GET', sleep=0) -> dict:
    """
    Асинхронный запрос с форматированным выводом
    :param url: Строка запроса
    :param method: Метод на выбор [`GET`, `POST` и т.п.]
    :param sleep: Время ожидания перед отправкой запроса. Используется для распределения запросов по времени.
    :return: {'status': status, 'json': data, 'content': content, 'headers': headers} - возвращаем `json` или `content`
    в зависимости от типа ответа. Если заполнено одно, значит другое поле будет возвращено пустым.
    """

    async with aiohttp.ClientSession() as session:
        await asyncio.sleep(sleep)
        async with session.request(method=method, url=url) as resp:
            data = {}
            content = None

            await resp.read()
            if resp.content_type == 'application/json':
                data = resp.json()
            else:
                content = await resp.content.read()      # .content.read() - это корутина

            status = resp.status
            headers = resp.headers

            return {'status': status, 'json': data, 'content': content, 'headers': headers}

