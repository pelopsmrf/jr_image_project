# Сервер картинок 2.0

Веб-приложение для загрузки картинок и получения прямых ссылок на них.
Бэкенд на Python (FastAPI), метаданные хранятся в PostgreSQL, картинки раздаёт Nginx, всё запускается в Docker.

## Требования

- Docker и Docker Compose
- Python 3.12+ (для скрипта бэкапа и запуска без Docker)

## Запуск

```bash
docker compose up --build
```

Остановка:

```bash
docker compose down
```

После запуска:

- Сайт через Nginx: http://localhost:8080
- Бэкенд напрямую: http://localhost:8000
- Картинки: http://localhost:8080/images/<имя_файла>
- PostgreSQL снаружи: `localhost:5433` (внутри Docker — `db:5432`)

### Запуск без Docker

База всё равно нужна, её можно поднять отдельно:

```bash
docker compose up -d db
pip install -r requirements.txt
python app.py
```

## Маршруты

| Маршрут | Метод | Кто обрабатывает | Описание |
|---|---|---|---|
| `/` | GET | бэкенд | Главная страница со ссылками |
| `/upload` | GET | бэкенд | Форма загрузки |
| `/upload` | POST | бэкенд | Загрузка файла (поле `file`). Сохраняет файл и метаданные в БД, возвращает ID и ссылку |
| `/images-list?page=N` | GET | бэкенд | Таблица картинок из БД, по 10 на странице, новые сверху |
| `/delete/<id>` | POST | бэкенд | Удаляет запись из БД и файл с диска, затем перенаправляет на `/images-list` |
| `/images/` | GET | бэкенд | Перенаправляет на `/images-list` |
| `/images/<имя_файла>` | GET | Nginx | Сама картинка |
| `/static/...` | GET | бэкенд | CSS |

Правила загрузки:

- форматы: `.jpg`, `.png`, `.gif`
- размер: до 5 МБ
- файл проверяется через Pillow, что это действительно картинка
- при ошибке в файле возвращается `400 Bad Request` с сообщением
- если запись в БД не удалась, файл удаляется и возвращается `500`

Пример через curl:

```bash
curl -F "file=@cat.jpg" http://localhost:8080/upload
```

## База данных

Таблица создаётся автоматически при старте бэкенда:

```sql
CREATE TABLE images (
    id SERIAL PRIMARY KEY,
    filename TEXT NOT NULL,
    original_name TEXT NOT NULL,
    size INTEGER NOT NULL,
    upload_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    file_type TEXT NOT NULL
);
```

Параметры подключения задаются переменными окружения в `compose.yaml`:
`DB_HOST`, `DB_PORT`, `DB_NAME`, `DB_USER`, `DB_PASSWORD`.

## Резервное копирование

Создать бэкап (контейнеры должны быть запущены):

```bash
python backup.py
```

Файл появится в папке `backups/`, например `backups/backup_2025-01-24_153000.sql`.
Результат записывается в `logs/app.log`.

То же самое вручную:

```bash
docker exec -t image_server_db pg_dump -U postgres images_db > backups/backup.sql
```

Восстановить базу из бэкапа:

```bash
docker exec -i image_server_db psql -U postgres images_db < backups/backup_2025-01-24_153000.sql
```

## Логи

Пишутся в `logs/app.log` (папка подключена к контейнеру) в формате:

```text
[2025-01-24 14:00:00] Успех: изображение img1.jpg загружено.
[2025-01-24 14:01:00] Ошибка: неподдерживаемый формат файла (user_file.txt).
[2025-01-24 14:02:00] Успех: изображение img1.jpg удалено.
[2025-01-24 14:03:00] Успех: резервная копия backup_2025-01-24_140300.sql создана.
```

## Структура проекта

```text
├── app.py              # бэкенд: маршруты, загрузка, удаление, логи
├── backup.py           # скрипт резервного копирования БД
├── utils/file_utils.py # проверка файла и генерация имени
├── utils/db.py         # работа с PostgreSQL
├── templates/          # HTML-страницы
├── static/style.css    # стили
├── requirements.txt    # зависимости Python
├── Dockerfile          # образ бэкенда (multi-stage build)
├── compose.yaml        # сервисы db, app и nginx
├── nginx.conf          # раздача картинок и проксирование на бэкенд
├── logs/               # логи
└── backups/            # резервные копии БД
```

Картинки хранятся в Docker-томе `images`, база — в томе `db_data`, поэтому данные не пропадают после перезапуска.
