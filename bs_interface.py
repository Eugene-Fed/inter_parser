import requests
import re
import json

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
        При иницализации получаем адрес целевой страницы, с которой необходимо работать в дальнейшем.
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
            if option.attrs:        # Первый элемент пустой, поэтому его пропускаем. Нужен лишь список ID стран
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
            if radio.attrs['value']:        # Первая кнопка `All` имеет пустое значение атрибута `value`, его пропускаем
                self.genders[radio.attrs['value']] = page.find('label', attrs={'for': radio.attrs['id']}).string
        return self.genders

    def get_total(self, page: BeautifulSoup) -> int:
        """
        Получаем общее количество персон для заданной страницы. Забираем это значения непосредственно из HTML.
        # TODO - в текущей реализации всегда выдает нулевое значение.
        # todo - Для получения реального числа необходим отправить запрос с фильтрами на все позиции
        :param page: Объект страницы.
        :return: Общее количество персон в поиске.
        """
        return int(page.find('strong', id='totalResults').string)


class SearchRequest:
    url = ''
    nation = ''
    gender = ''
    notice_type = ''
    age = 0
    total = 0
    responses = []
    keywords = []

    def __init__(self, url='', nation='', gender='', notice_type='', age=0, keywords=[]):
        """

        :param url: API для запроса: `https://ws-public.interpol.int/notices/v1/`
        :param nation: Двузначный идентификатор гражданства
        :param gender: Пол: `M`, `F`, `U` - undefined
        :param notice_type: Тип запрашиваемого поиска: `red` или `yellow`
        :param age:
        """
        self.url = url
        self.nation = nation
        self.gender = gender
        self.notice_type = notice_type
        self.age = age
        self.keywords = keywords

    def __call__(self) -> list:
        # Можно добавить альтернативный ввод `keywords` как параметра при необходимости кастомизации вызова
        response_json = self.get_response(url=self.url, notice_type=self.notice_type, nation=self.nation,
                                          gender=self.gender, age=self.age)
        if response_json:       # Если ответ не пуст (статус запроса `200`, и количество результатов больше `0`
            if int(response_json['total']) < 160:   # Если при этом фильтрация сработала отлично
                self.responses.append(response_json)    # Тогда добавляем `json` результата результирующий список
            else:   # Если же после фильтрации количество результатов равно предельному `160`
                for keyword in self.keywords:       # Тогда добавляем к запросу вариации ключевых слов
                    self.responses.append(self.get_response(url=self.url, notice_type=self.notice_type,
                                                            nation=self.nation, gender=self.gender, age=self.age,
                                                            keyword=keyword))

        return self.responses

    def get_response(self, url, notice_type, nation, gender, age, keyword='') -> json:
        request = f'{url}{notice_type}?' \
                  f'nationality={nation}&' \
                  f'sexId={gender}&' \
                  f'ageMin={age}&ageMax={age}&freeText={keyword}'
        response = requests.get(url=request)

        if response.status_code == 200:     # Для простоты игнорируем другие статусы. По-уму их тоже нужно обработать
            output_json = response.json()
            if output_json and int(output_json['total']) > 0:       # Проверяем что json не пуст и `total` больше `0`
                return output_json
        else:
            return None

        """"
            total = int(output_json['total'])

            if total > 0:           # Если количество результатов в ответе равно 0, то возвращаем пустой список
                if total == 160 and keywords:
                    # Если количество результатов равно 160, значит в фильтре слишком много результатов
                    # Нужно попробовать добавить различные ключевики к запросу, чтобы собрать максимальное кол-во персон
                    for key in keywords:
                        # Добавляем рекурсию глубиной в 1, чтобы пройтись по всем элементам списка ключевиков
                        return self.get_response(url=url, notice_type=notice_type,
                                                  nation=nation, ender=gender, age=age, keyword=key)
                else:
                    responses.append(output_json)

        return responses
        """


class Person:
    pass
