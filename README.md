# Сервер картинок

Веб-приложение для загрузки картинок и получения прямых ссылок на них.
Бэкенд на Python (FastAPI), картинки раздаёт Nginx, всё запускается в Docker.

## Требования

- Docker и Docker Compose
- Python 3.12+ (только для запуска без Docker)

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

### Запуск без Docker

```bash
pip install -r requirements.txt
python app.py
```

## Маршруты

| Маршрут | Метод | Кто обрабатывает | Описание |
|---|---|---|---|
| `/` | GET | бэкенд | Главная страница со ссылками |
| `/upload` | GET | бэкенд | Форма загрузки |
| `/upload` | POST | бэкенд | Загрузка файла (поле `file`). Возвращает ID и ссылку |
| `/images/` | GET | бэкенд | Список загруженных картинок |
| `/images/<имя_файла>` | GET | Nginx | Сама картинка |

Правила загрузки:

- форматы: `.jpg`, `.png`, `.gif`
- размер: до 5 МБ
- файл проверяется через Pillow, что это действительно картинка
- при ошибке возвращается `400 Bad Request` с сообщением

Пример через curl:

```bash
curl -F "file=@cat.jpg" http://localhost:8080/upload
```

## Логи

Пишутся в `logs/app.log` в формате:

```text
[2025-01-24 14:00:00] Успех: изображение img1.jpg загружено.
[2025-01-24 14:01:00] Ошибка: неподдерживаемый формат файла (user_file.txt).
```

Посмотреть логи из контейнера:

```bash
docker compose exec app cat logs/app.log
```

## Структура проекта

```text
├── app.py              # бэкенд: маршруты, загрузка, логи
├── utils/file_utils.py # проверка файла и генерация имени
├── templates/          # HTML-страницы
├── requirements.txt    # зависимости Python
├── Dockerfile          # образ бэкенда (multi-stage build)
├── compose.yaml        # сервисы app и nginx, тома images и logs
└── nginx.conf          # раздача картинок и проксирование на бэкенд
```

Картинки и логи хранятся в Docker-томах `images` и `logs`, поэтому не пропадают после перезапуска.
