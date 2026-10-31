# Space Bounty Hunters API

REST API для охотников за головами: база разыскиваемых преступников и журнал попыток поимки.
Стек тот же, что в проектах курса: Django REST Framework, PostgreSQL, Docker Compose.

## Запуск

```bash
cp .env.example .env      # впиши свои SECRET_KEY и POSTGRES_PASSWORD
docker compose up --build
```

API будет доступен на http://localhost:8000/api/ (порт задаётся `APP_PORT` в `.env`).

### База данных и стартовые данные

Таблицы создаются миграцией `bounty/migrations/0001_initial.py`.
Миграция `0002_seed_data.py` сама заполняет базу: **6 преступников и 12 записей журнала**.
Миграции применяются автоматически при старте контейнера (`python manage.py migrate` в `CMD` Dockerfile), отдельного импорта не нужно.

Без Docker (локально, нужен запущенный PostgreSQL):

```bash
pip install -r requirements.txt
export SECRET_KEY=... POSTGRES_DB=bounty POSTGRES_USER=bounty POSTGRES_PASSWORD=... POSTGRES_HOST=localhost
python manage.py migrate
python manage.py runserver
```

Пересоздать базу с нуля: `docker compose down -v`, затем `docker compose up`.

## Модели

**WantedCriminal**: `id`, `name` (может быть `null`, если имя неизвестно), `nickname`, `reward`, последние известные координаты
(`latitude`, `longitude`, оба могут быть пустыми) и/или текстовая заметка `location_note`, `difficulty` (1–10),
`armed`, `has_crew`, `escape_master`. В ответе также есть `last_known_coordinates` (`{"latitude", "longitude"}` или `null`).

**HuntLog**: `id`, `criminal_id` (внешний ключ на WantedCriminal), `success`, `notes`, `created_at` (ставит сервер).
Связь один ко многим: у одного преступника может быть много записей журнала (`criminal.hunts`).

## Эндпоинты

### Преступники (только чтение)

| Метод | URL | Описание |
|---|---|---|
| GET | `/api/criminals/` | список, с фильтрами и сортировкой |
| GET | `/api/criminals/{id}/` | один преступник |

Параметры списка (можно сочетать):

| Параметр | Значение |
|---|---|
| `min_reward` | награда не меньше значения |
| `max_reward` | награда не больше значения |
| `armed`, `has_crew`, `escape_master` | `true` или `false` |
| `sort` | `reward` (по возрастанию) или `-reward` (по убыванию) |

Пример: `GET /api/criminals/?min_reward=5000&armed=true&sort=-reward` вернёт Black Comet (25000.00) и Red Siren (7500.00).

### Журнал охоты (CRUD)

| Метод | URL | Описание |
|---|---|---|
| GET | `/api/hunts/` | все записи; фильтр `?criminal_id=5` |
| GET | `/api/hunts/{id}/` | одна запись |
| POST | `/api/hunts/` | создать запись |
| PATCH | `/api/hunts/{id}/` | изменить `success` или `notes` |
| DELETE | `/api/hunts/{id}/` | удалить запись |

Пример `POST /api/hunts/`:

```json
{"criminal_id": 3, "success": false, "notes": "Target escaped through an asteroid field."}
```

Ответ `201`:

```json
{"id": 13, "criminal_id": 3, "success": false, "notes": "Target escaped through an asteroid field.", "created_at": "2026-10-31T13:20:11.482910+05:00"}
```

`created_at` и `id` генерирует сервер, значения из запроса игнорируются.

### Коды ответов

| Код | Когда |
|---|---|
| 200 | успешное чтение или обновление |
| 201 | запись создана |
| 204 | запись удалена |
| 400 | неверные данные: нет `criminal_id` или `notes`, несуществующий преступник, неверный тип `success`, пустые `notes`, недопустимый `sort`, нечисловой `min_reward`, смена преступника у существующей записи |
| 404 | объект не найден (в том числе неверный формат ID) |
| 405 | метод не поддерживается (например, `POST /api/criminals/` или `PUT /api/hunts/{id}/`) |

Пример ошибки: `{"criminal_id": ["Invalid pk \"9999\" - object does not exist."]}`.

## Postman

Файл: [`postman/Space_Bounty_Hunters.postman_collection.json`](postman/Space_Bounty_Hunters.postman_collection.json).
Postman → Import → выбрать файл. Переменная `baseUrl` равна `http://localhost:8000`.
В коллекции 28 запросов с проверками (48 assertions): список, фильтры, сортировка, комбинированный запрос, детали преступника,
CRUD журнала охоты и невалидные запросы (400 и 404). Запускается целиком через Runner. Тесты рассчитаны на стартовые данные из миграции.

## Тесты

```bash
SECRET_KEY=x DB_ENGINE=django.db.backends.sqlite3 POSTGRES_DB=test.sqlite3 python manage.py test
```

## Структура

```
.
├── compose.yaml        # сервисы backend и db, сеть, именованный том
├── Dockerfile          # образ бэкенда
├── .env.example        # шаблон переменных окружения
├── requirements.txt
├── manage.py
├── config/             # настройки Django (читают окружение)
├── bounty/             # модели, сериализаторы, представления, тесты
│   └── migrations/     # схема БД и стартовые данные
└── postman/            # экспорт Postman Collection
```
