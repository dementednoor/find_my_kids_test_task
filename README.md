## Проблема 1:

Аналитика поведения пользователей в мобильных приложениях (условно clickstream) часто приходит в хранилище с ошибками: в каких-то событиях начиная с некоторой версии приложения перестали писаться или стали писать неверно значения параметров, перестали присылаться события целиком, и т. д.
Необходимо описать решение, которое позволит мониторить качество аналитических событий и быстро локализировать проблемы.

### Решение:

Как только событие поступает на обработку (условно где-то в облаке), оно сперва проходит валидацию, вместо того, чтобы сразу записываться в базу событий. В случае, если какие-то данные некорректные (какие-то численные метрики не попадают в оперируемый диапазон, приходят `null` поля, поля пришли с неверным типом), они уходят в отдельное хранилище, в котором хранится `id` ивента и текст ошибки. Для этой базы уже будет заведен какой-нибудь отдельный процесс, который будет накапливать определенную базу знаний ошибок и методов их решения. Решение, соответственно, будет автоматизировано. На очень банальном примере: если в базе в какое-то `integer` поле пришел `float`, то мы просто конвертируем в нужный тип, убедившись, что ошибка заключается в этом, о чем будет говорить поле в базе данных некорректных событий. Соответственно, под какие-то конкретные комбинации ошибок будут подобраны конкретные решения. 
Весь этот пайплайн завернуть внутрь графа условных `Airflow` или `ArgoWorkflows`, который будет инстацироваться при появлении новых батчей событий, приходящих на сервер.
То есть алгоритм следующий:
  1. В облако приходит `json` с набором событий;
  2. Запускается процесс обработки данных событий;
  3. Если событие валидно, оно записывается в базу;
  4. Если нет, то запускается отдельный процесс, который записывает событие в отдельное хранилище для проблемных данных;
  5. Если проблема, описанная в базе, имеет прецедент и заранее известен метод ее решения, он применяется автоматически (в коде не приведено);
  6. Если нет, то разбор данных ошибок происходит в ручном режиме.


Как вариант, в дальнейшем подключить ML систему, которая параллельно будет обучаться устанавливать корреляцию между какими-то маркерами возникновения неверного события и первопричиной.

Дополнительно следует также ввести дашборд с визуализацей данных (с использованием `Grafana, Tableau, DataLens` и т. д.), чтобы в любой момент была возможность зайти и посмотреть, все ли сейчас окей с данными, и в какой именно момент что-то пошло не так. Помимо этого в случае, если в процессе работы графа пайплайна обработки данных будут обнаружены некорректные события, то овнеру графа придет соответствующее сообщение.

Код не представляет из себя полноценный MVP, лишь показывает суть концепции на очень мелких примерах, поэтому в качестве СУБД используется `SQLite`. Кодово реализовать прототип решения проблем из `failed_events` не хватило времени, к сожалению :(

запуск:

`python main.py --db-dir '{/home/user/directory_with_db_file}' --json-file '{events.json}' --first-run`


`--db-dir` - директория с файлом с базой данных

`--json-file` - файл со списком событий (для локального вопсроизведения тоже должен быть расположен в директории с базой данных), в данном примере их 2 - один валидный, второй нет

`--first-run` - опцинальный флаг, на случай если это первый запуск и таблиц в базе никаких нет

В результате видим, что первое событие записалось в базу, второе в базу проблемных событий. Для второго события, соответственно, должен будет запуститься уже внутри пайплайна обработчик проблемных событий. В базе будет указано, что проблема заключается в том, что в числовое поле записана строка. Подобные проверки на валидность могут в дальнейшем обрастать новыми пунктами.


## Проблема 2:

Часто в результате выкладки новых версий приложений или каких-то внешних факторов происходят падения или скачки метрик, в т. ч. только в отдельных разрезах/для отдельных сегментов. Например, упала конверсия из открытия приложения в регистрацию, выросло количество ошибок оплаты или значительно увеличилось время ответа от нашего бекенда. 

Нужно описать решение, которое позволит мониторить здоровье метрик и оперативно реагировать на проблемы.

Тут, к сожалению, кода не будет, поскольку рассматривается все на абстрактных примерах. 

### Решение 
Концепция следующая:
Условно имеется таблица `Metrics` вида 


date | time | metric | value


Опираясь на эту таблицу, следует построить какой-нибудь параметризируемый дашборд (также с использованием `Grafana, Tableau, DataLens` и т. д.), который будет визуализировать накликанные данные, соответственно, на на них будут отображаться скачки тех или иных метрик, заметные человеческим невооруженным глазом.

Также следует держать табличку `Releases` вида 

- - - - - - - - - - - - -
| release | date | time |
- - - - - - - - - - - - -

И на вышеупомянутом дашборде к исходному запросу присоединять эту табличку и отображать, когда именно был выпушен новый релиз, чтобы понимать, есть ли связь между выкатом определенной фичи продукта в рамках нового релиза и падением каких-то метрик.

Оффлайн меры: 
Периодически запускать запрос к первой табличке примерно вида:

```
SELECT
  Metrics.date as date,
  Releases.release as release,
  Metrics.metric as metric,
  AVG(Metrics.value) as avg_value,
  MAX(Metrics.value) as max_value,
  MIN(Metrics.value) as min_value,
  PERCENTILE(Metrics.value, 0.5) as p50_value,
  PERCENTILE(Metrics.value, 0.95) as p95_value,
  PERCENTILE(Metrics.value, 0.99) as p99_value
FROM Metrics
LEFT JOIN Releases
ON Metrics.date = Releases.date
GROUP BY Metrics.date, Releases.release, Metrics.metric
```
И отсматривать показатели. Если, к примеру, 99-я перцентиль сильно выбивается из ожидаемых значений, то присылать какие-то оповещения ответственным, чтобы те применили какие-то меры. В дальнейшем можно также прикрутить к этой истории ML систему, которая будет устанавливать взаимосвязь разных метрик, как динамика одной влияет на другую и т. д.
