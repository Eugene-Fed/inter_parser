# inter_parser
Test task for IP parsing

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
  
Добавлена функция дополнительной фильтрации с использованием ключевых слов - это должно позволить преодолеть ограничение для тех результатов выдачи, где даже с учетом всех фильтров получается больше 160 Персон. Для исключения дублей и перезаписи данных, информация о людях предварительно копитcя в словаре с ID в качестве ключа, и после обработки результатов по фильтру (без учета ключевиков) - происходит выгрузка данных.

## Заметка
Сам сайт периодически выдает дубли одной Персоны на странице поиска. Поэтому не мудрено, что порой в результатах меньше позиций, чем в `Total` сайта/ответа.

## TODO
- [ ] Реализовать быстрый сбор только основных сведений (ФИО, дата рождения, ID, гражданство, миниатюра фотографии) с переключение через настройки.
- [ ] Реализовать "умный" поиск, который запрашивает по-умолчанию весь возрастной диапазон и урезает его только в тех случаях, когда выдача предлагает 160 результатов.
- [ ] Добавить асинхронности коду, чтобы распараллелить отправку запросов.
