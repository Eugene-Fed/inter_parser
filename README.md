# inter_parser
Test task for IP parsing

В текущей реализации мы получаем первую страницу результатов запросов по всем фильтрам.
Добавлена функция дополнительной фильтрации с использованием ключевых слов - это должно позволить преодолеть  ограничение в 160 персон на запрос. Однако порождает дубликаты, т.к. несколько людей могут подходить под разные ключевые запросы. Это можно исправить с помощью множеств.  

Однако, кроме получения всех результатов запросов, необходимо также пройтись вглубь по всем страницам. По сути каждый результат запроса можно обработать как объект с методом `next`, т.к. результат содержит в себе номер первой, последней, текущей и следующей страниц. Эти номре можно исопльзьвать для уточнения результата выдачи. Сами запросы содержат только базовую информацию по каждой персоне и ссылку на фото. За дополнительной информацией все равно необходимо лезть по заданной ссылке внутрь карточки.  

Проработать класс `Person`, в котором будет храниться вся конечная информация
