# -*- coding: UTF-8 -*-

import json
import imghdr
from pathlib import Path

SETTINGS_FILE = Path('settings.json')
SETTINGS_DATA = {
    'result_dir': 'result',
    'search_pages_urls': {
        'red': r'https://www.interpol.int/How-we-work/Notices/View-Yellow-Notices',
        'yellow': r'https://www.interpol.int/How-we-work/Notices/View-Red-Notices'
    },
    'request_url': r'https://ws-public.interpol.int/notices/v1/',
    'nations': [],
    'genders': [],     # Можно оставить пустым. Доступные значения: ['M', 'F', 'U']
    'search_pages_id': [],   # Фильтр запрашиваемых типов поиска. Равно ключам `search_pages_url`. Если пуст - то все
    'min_age': 0,
    'max_age': 120,
    'notices_limit': 160,
    'preview_only': False,      # Если `True` - собирает только упрощенные данные: ФИО, Д.р., Гражданство и Миниатюра.
    'keywords': {    # Эта фича не помогает нарастить количество результатов, поэтому можно опустить ради быстродействия
        'red': ['ammunition', 'armed', 'assault', 'blackmail', 'crime', 'criminal', 'death', 'drug', 'encroachment',
                'explosive', 'extorsion', 'extremist', 'federal', 'femicidio', 'firearms', 'homicide', 'hooliganism',
                'illegal', 'infanticidio', 'injury', 'murder', 'narcotic', 'passport', 'rape', 'sabotag', 'sexual',
                'stealing', 'terror', 'viol', 'weapon'],
        'yellow': []            # Желтые страницы возвращают пустой результат при наличии ключевого запроса
    }
}


class Settings:
    # TODO - вместо словаря параметров использовать **kwargs для генерации параметров по содержимому файла настроек
    data = SETTINGS_DATA
    path = SETTINGS_FILE
    preview_only = False
    """
    result_dir = Path('')
    search_pages_urls = {}
    request_url = ''
    nations = []
    genders = []
    search_pages_id = []
    min_age = 0
    max_age = 0
    notices_limit = 0
    keywords = {}
    """

    def __init__(self, settings_path=None):
        """
        Добываем настройки из файла. Если файл отсутствует или недоступен, то он будет создан со значением по-умолчанию.
        :param settings_path: Путь к файлу настроек в формате строки или `Path`. Если не задан или другой объект -
        будет использовано значение по-умолчанию.
        """
        # Если передана строка - приводим ее к `Path`, если `Path` - используем как есть,
        # если что-то другое - будем использовать значение по-умолчанию
        if isinstance(settings_path, str):
            self.path = Path(settings_path)
        elif isinstance(settings_path, Path):
            self.path = settings_path

        self.data = load_json(file_path=self.path, default=self.data)   # Можем получить параметры через словарь
        '''
        # Использовать имена параметров из файла настроек оказалось неудобно, т.к IDE не дает подсказки,
        # хоть это и само по себе достаточно лаконично/
        for key, value in self.data:                                    
           setattr(self, key, value)
        '''
        self.result_dir = self.data['result_dir']                       # А можем напрямую по имени параметра
        self.search_pages_urls = self.data['search_pages_urls']
        self.request_url = self.data['request_url']
        self.nations = self.data['nations']
        self.genders = self.data['genders']
        self.search_pages_id = self.data['search_pages_id']
        self.min_age = min(self.data['min_age'], self.data['max_age'])
        self.max_age = max(self.data['min_age'], self.data['max_age'])
        self.notices_limit = self.data['notices_limit']
        self.keywords = self.data['keywords']
        self.preview_only = self.data['preview_only']

    def __call__(self, *args, **kwargs):
        return self.data


def load_json(file_path: Path, default={}) -> json:
    """
    Загрузка настроек из json-файла.
    :param file_path: Путь к файлу настроек
    :param default: Использовать значение по-умолчанию, если файл отсутствует
    :return: json-объект с настройками
    """
    json_data = None
    if file_path.exists():
        with file_path.open() as f:
            try:
                json_data = json.load(f)
                print(f'Файл настроек `{str(file_path)}` загружен.')
            except Exception as e:
                print(e, '\nФайл настроек имеет неверный формат. Файл будет перезаписан со значениями по-умолчанию.')

    if not json_data:
        json_data = default
        save_file(file_path=file_path, file_data=json_data)

    return json_data


def save_file(file_path: Path, file_data=None) -> None:
    # TODO - Реализовать как класс `FileSaver` с двумя методами: `save_image` и `save_json`.
    # todo - При инициализации класс принимает Путь к файлу 'file_path' и создает структуру папок для сохранения.
    # todo - Или принимает два параметра: путь `folders` и имя файла `file_name`.
    """
    Сохранение файла с учетом формата данных.
    :param file_path: Конечный путь к файлу в формате `json` или изображения. Во втором случае - нужно выяснить его тип.
    :param file_data: Данные файла - json-объект или байтовая строка изображения.
    :return: None
    """
    # Обходим список родителей в обратном порядке, т.к. чем больше индекс, тем ближе родитель к корневому.
    # [0: 'dir_1/dir_2/dir_3'], [1: 'dir_1/dir_2'], [2: 'dir_1']
    for parent in file_path.parents[::-1]:
        # Если папка не существует, то создаем папку
        if not parent.is_dir():
            parent.mkdir()

    # После того как все папки созданы, добавляем в нее искомый файл с учетом его типа.
    # Не добавляю тут проверку данных, т.к. это избыточно в данном случае.
    if file_path.suffix == r'.json':
        # TODO - переписать на проверку типа данных вместо проверки разрешения в пути сохранения файла
        with file_path.open("w", encoding="utf-8") as fp:
            json.dump(file_data, fp, indent=4, ensure_ascii=False)

    else:
        #  TODO - разобраться с модулем `imghdr` и переписать получение типа изображения по его данным.
        '''
        img_suffix = imghdr.what(file_data)     # Получаем тип изображения из данных через модуль `imghdr`
        if not img_suffix:
            img_suffix = 'jpg'  # Если модуль не смог получить тип изображения, сохраняем его как `jpg`
        '''

        # file_path = file_path.with_suffix(img_suffix)       # Добавляем к пути файла расширение изображения
        with file_path.open('wb') as fp:
            fp.write(file_data)

    print(f'File `{str(file_path)}` saved.')
    pass


if __name__ == '__main__':
    settings = Settings(settings_path=SETTINGS_FILE)
    print(json.dumps(settings(), indent=4))
else:
    pass
