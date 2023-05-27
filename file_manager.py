# -*- coding: UTF-8 -*-

import json
import sys
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
    Сохранение файла с учетом формата данных
    :param file_path: конечный путь к файлу
    :param file_data: данные файла: json-объект или изображение
    :return: None
    """
    # Обходим список родителей в обратном порядке. т.к. чем больше индекс, тем ближе родитель к корневому
    # [0: 'dir_1/dir_2/dir_3'], [1: 'dir_1/dir_2'], [2: 'dir_1']
    for parent in file_path.parents[::-1]:
        # Если папка не существует, то создаем папку
        if not parent.is_dir():
            parent.mkdir()

    # После того как все папки созданы, добавляем в нее искомый файл из шаблона.
    with file_path.open("w", encoding="utf-8") as f:
        json.dump(file_data, f, indent=4, ensure_ascii=False)
    print(f'File "{str(file_path)}" does not exists. It will be  created from template.')
    pass


if __name__ == '__main__':
    settings = load_json(file_path=settings_file)
    print(json.dumps(settings, indent=4))
else:
    pass
