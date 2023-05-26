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

    def get_total(self, page: BeautifulSoup) -> int:
        """
        Получаем общее количество персон для заданной страницы. Забираем это значения непосредственно из HTML.
        # TODO - в текущей реализации всегда выдает нулевое значение.
        # todo - Для получения реального числа необходим отправить запрос с фильтрами на все позиции
        :param page: Объект страницы.
        :return: Общее количество персон в поиске.
        """
        return int(page.find('strong', id='totalResults').string)


class Person:
    pass
