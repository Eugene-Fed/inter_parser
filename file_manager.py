# -*- coding: UTF-8 -*-

import json
import sys
import imghdr
from pathlib import Path

settings_file = Path('settings.json')
result_dir = Path('result')


def load_json(file_path: Path) -> json:
    """
    Загрузка настроек из json-файла.
    :param file_path: Путь к файлу настроек
    :return: json-объект с настройками
    """
    json_data = {}
    if file_path.exists():
        with file_path.open() as f:
            json_data = json.load(f)
            print(f'Файл настроек `{str(file_path)}` загружен.')

    return json_data


def save_file(file_path: Path, file_data=None) -> None:
    """
    Сохранение файла с учетом формата данных.
    :param file_path: Конечный путь к файлу в формате `json` или изображения. Во втором случае - нужно выяснить его тип.
    :param file_data: Данные файла - json-объект или байтовая строка изображения.
    :return: None
    """
    # Обходим список родителей в обратном порядке. т.к. чем больше индекс, тем ближе родитель к корневому
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
        img_suffix = imghdr.what(file_data)     # Получаем тип изображения из данных через модуль `imghdr`
        if not img_suffix:
            img_suffix = 'jpeg'  # Если модуль не смог получить тип изображения, сохраняем его как `jpeg`
        file_path.with_suffix(img_suffix)       # Добавляем к пути файла расширение изображения
        with file_path.open("wb") as fp:
            fp.write(file_data.content)

    print(f'File `{str(file_path)}` saved.')
    pass


if __name__ == '__main__':
    settings = load_json(file_path=settings_file)
    print(json.dumps(settings, indent=4))
else:
    pass
