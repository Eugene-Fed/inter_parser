# inter_parser
Парсер нарушителей и потерянных.  

## Подготовка к запуску
Предварительно необходимо установить дополнительные библиотеки командой  
`pip install -r requirements.txt`  

## Запуск
Пуск происходит командой  
`python main.py`  

Управлять настройками запуска можно с помощью файла `settings.json`. Если файл отсутствует или имеет синтаксические ошибки - то при запуске скрипта файл будет перезаписан со значениями по-умолчанию.  

Основные настройки касаются ограничений по возрасту, полу и гражданству человека.  
Пол принимает значения: `M` - мужской, `F` - женский или `U` - неопределен. Необходимые варианты перечисляются в соответствующем списке.  
Гражданство настраивается аналогично, с использованием кодов государств.  
Если любой из предыдущих списков пуст - поиск будет работать по всем возможным вариантам (без фильтра) для этого поля.  

Параметр `preview_only` (`true` или `false`) отвечает за сбор только базовой информации для сокращения времени выполнения, т.к. не требует открывать каждую карточку по-отдельности. Собирается только ФИО, дата рождения, гражданство и Миниатюра фотографии.  

## UPDATE 2023.05.30
Переработана функция `get_notices()` в `main.py` с целью уменьшения количества запросов к серверу. Это реализовано "ленивым" фильтром по возрасту. Теперь первоначально происходит попытка собрать всю выдачу по стране, полу и всему диапазону доступных возрастов. Только если количество результатов равно или больше 160, тогда функция обрезает весь возрастной диапазон на две половины и рекурсивно генерирует два новых запроса до тех пор, пока не получит меньше 160 результатов или не достигнет фильтра с диапазоном в 1 год.  

## UPDATE 2023.06.04  
Получаем расширение изображений через заголовок ответа.  

## DEPRECATED
Добавлена функция дополнительной фильтрации с использованием ключевых слов - это должно позволить преодолеть ограничение для тех результатов выдачи, где даже с учетом всех фильтров получается больше 160 Персон. Для исключения дублей и перезаписи данных, информация о людях предварительно копитcя в словаре с ID в качестве ключа, и после обработки результатов по фильтру (без учета ключевиков) - происходит выгрузка данных.  
По большому счету это излишне, т.к. почти не увеличивает количество собираемых данных, однако значительно увеличивает количество запросов к серверу.

## Заметка
Сам сайт периодически выдает дубли одной Персоны на странице поиска. Поэтому не мудрено, что порой в результатах меньше позиций, чем в `Total` сайта/ответа.

## TODO
- [x] Реализовать быстрый сбор только основных сведений (ФИО, дата рождения, ID, гражданство, миниатюра фотографии) с переключение через настройки.
- [x] Реализовать "умный" поиск, который запрашивает по-умолчанию весь возрастной диапазон и урезает его только в тех случаях, когда выдача предлагает 160 результатов.
- [ ] Добавить асинхронности коду, с помощью `asyncio` и `aiohttp` (+ `aiofile` или `multiprocessing` при работе с превью данных, т.к. это значительно ускорит выполнение за счет параллельного сохранения картинок).
- [ ] Добавить в модуль `bs_interface` методы `get_json` и `get_content`, которые обернут запросы `requests.get()` в блоки `try except`.
- [ ] Реализовать работу через proxy.
