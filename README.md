Проблема 1:

Аналитика поведения пользователей в мобильных приложениях (условно clickstream) часто приходит в хранилище с ошибками: в каких-то событиях начиная с некоторой версии приложения перестали писаться или стали писать неверно значения параметров, перестали присылаться события целиком, и т. д.
Необходимо описать решение, которое позволит мониторить качество аналитических событий и быстро локализировать проблемы.

Решение:
Как только событие поступает на обработку (условно где-то в облаке), оно сперва проходит валидацию, вместо того, чтобы сразу записываться в базу событий. В случае, если какие-то данные некорректные (какие-то численные метрики не попадают в оперируемый диапазон, приходят null поля, поля пришли с неверным типом), они уходят в отдельное хранилище, в котором хранится id ивента и текст ошибки. Для этой базы уже будет заведен какой-нибудь отдельный воркер, который будет накапливать определенную базу знаний ошибок и методов их решения. Решение, соответственно, будет автоматизировано. На очень банальном примере: если в базе в какое-то integer поле пришел float, то мы просто конвертируем в нужный тип, убедившись, что ошибка заключается в этом, о чем будет говорить поле в базе данных некорректных событий. Соответственно, под какие-то конкретные комбинации ошибок будут подобраны конкретные решения. 
Весь этот пайплайн завернуть внутрь графа условных Airflow или ArgoWorkflows, который будет инстацироваться при появлении новых батчей событий, приходящих на сервер.

Как вариант, в дальнейшем подключить ML систему, которая параллельно будет обучаться устанавливать корреляцию между какими-то маркерами падения (неверного события) и первопричиной.

Дополнительно следует также ввести дашборд с визуализацей данных (с использованием Grafana, Tableau, DataLens и т. д.), чтобы в любой момент была возможность зайти и посмотреть, все ли сейчас окей с данными, и в какой именно момент что-то пошло не так. Помимо этого в случае, если в процессе работы графа пайплайна обработки данных будут обнаружены некорректные события, то овнеру графа придет соответствующее сообщение.

Код не представляет из себя полноценный MVP, лишь показывает суть концепции на очень мелких примерах, поэтому используется SQLite. Кодово реализовать прототип решения проблем из failed_events не хватило времени, к сожалению :(

запуск:

`python main.py --db-dir '{/home/user/directory_with_db_file}' --json-file '{events.json}' --first-run`
`--db-dir` - директория с файлом с базой данных
`--json-file` - файл со списком событий, в данном примере их 2 - один валидный, второй нет
`--first-run` - флаг, на случай если это первый запуск и таблиц в базе никаких нет

В результате видим, что первое событие записалось в базу, второе в базу проблемных событий. Для второго события, соответственно, должен будет запуститься уже внутри пайплайна обработчик проблемных событий. В базе будет указано, что проблема заключается в том, что в числовое поле записана строка. Подобные проверки на валидность могут в дальнейшем обрастать новыми кейсами.


Проблема 2:

Часто в результате выкладки новых версий приложений или каких-то внешних факторов происходят падения или скачки метрик, в т. ч. только в отдельных разрезах/для отдельных сегментов. Например, упала конверсия из открытия приложения в регистрацию, выросло количество ошибок оплаты или значительно увеличилось время ответа от нашего бекенда. 

Нужно описать решение, которое позволит мониторить здоровье метрик и оперативно реагировать на проблемы.

