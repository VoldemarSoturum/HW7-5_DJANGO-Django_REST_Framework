# Smart Home API (Django + DRF)

Мини‑проект для CRUD по **датчикам температуры** и записи **измерений**.

- Проект: `smart_home`
- Приложение: `measurement`
- Бэкенд: Django + Django REST Framework
- БД: PostgreSQL (рекомендовано) или SQLite (для быстрого локального теста)

## Содержание
- [Функциональность](#функциональность)
- [Быстрый старт](#быстрый-старт)
- [Настройка базы данных](#настройка-базы-данных)
- [Запуск сервера](#запуск-сервера)
- [Проверка API (requests.http и curl)](#проверка-api-requestshttp-и-curl)
- [Тестирование](#тестирование)
- [Структура проекта](#структура-проекта)
- [Эндпоинты](#эндпоинты)
- [Скриншоты выполнения запросов](#скриншоты-выполнения-запросов)
- [Диаграмма БД](#диаграмма-бд)

---

## Функциональность

- **Датчики (`Sensor`)**: создание, просмотр списка, получение деталей, обновление (название, описание).
- **Измерения (`Measurement`)**: добавление новых измерений (температура + авто‑время).
- Детальная карточка датчика содержит **вложенный список** его измерений.

---

## Быстрый старт

```bash
# 1) Клонируем и входим в папку проекта
git clone <repo-url>
cd EX1-DRF_and_CRUD_for_Smart_Home

# 2) Создаём и активируем виртуальное окружение
python -m venv .venv
# Windows PowerShell:
. .venv/Scripts/Activate.ps1
# macOS/Linux:
source .venv/bin/activate

# 3) Ставим зависимости
pip install -r requirements.txt
```

> **Примечание:** проект изначально рассчитан на PostgreSQL. Для быстрого локального прогона можно использовать SQLite (см. раздел «Тестирование: Вариант C»).

---

## Настройка базы данных

### Вариант 1: PostgreSQL (рекомендуется)

Создайте роль и базу в `psql` под суперпользователем (например, `postgres`):

```sql
-- создаём роль и базу, назначаем владельца
CREATE ROLE netology_smart WITH LOGIN PASSWORD 'your_password';
CREATE DATABASE netology_smart_home OWNER netology_smart ENCODING 'UTF8' TEMPLATE template0;

-- делаем доступы явными
REVOKE ALL ON DATABASE netology_smart_home FROM PUBLIC;
GRANT CONNECT, TEMP ON DATABASE netology_smart_home TO netology_smart;

-- подключаемся к базе
\c netology_smart_home

-- отдаём владение публичной схемой и разрешаем создавать объекты
ALTER SCHEMA public OWNER TO netology_smart;
GRANT USAGE, CREATE ON SCHEMA public TO netology_smart;
```

**Настройки Django** (файл `smart_home/settings.py`):
```python
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": "netology_smart_home",
        "USER": "netology_smart",
        "PASSWORD": "your_password",
        "HOST": "localhost",
        "PORT": "5432",
    }
}
```

> Для запуска **тестов** Django создаёт отдельную тестовую БД. Дайте роли право `CREATEDB`:
> ```sql
> ALTER ROLE netology_smart WITH CREATEDB;
> ```
> Либо создайте `test_netology_smart_home` вручную и запускайте тесты с `--keepdb` (см. далее).

### Вариант 2: SQLite (быстро локально)

Создайте `smart_home/settings_test.py`:
```python
from .settings import *

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}
```

Запуск с этими настройками:
```bash
python manage.py migrate --settings=smart_home.settings_test
```

---

## Запуск сервера

```bash
python manage.py migrate
python manage.py runserver
```
Сервер будет доступен на `http://localhost:8000/`.

В корневом `urls.py` проекта настроен префикс API:  
**`/api/` → include('measurement.urls')**  
Т.е. базовый URL API: `http://localhost:8000/api`.

---

## Проверка API (requests.http и curl)

### Вариант A: VS Code + REST Client

1. Установите расширение **REST Client**.
2. Откройте `requests.http` в корне проекта.
3. Жмите **Send Request** над нужным блоком.

Пример «живого» сценария (сохранение `sensorId` из ответа):
```http
@baseUrl = http://localhost:8000/api

### Список датчиков
GET {{baseUrl}}/sensors/
Content-Type: application/json

### Создать датчик
# @name createSensor
POST {{baseUrl}}/sensors/
Content-Type: application/json

{
  "name": "ESP32",
  "description": "Датчик на кухне за холодильником"
}

> {% 
  const body = JSON.parse(response.body);
  client.global.set("sensorId", body.id); 
%}

### Обновить датчик (PATCH)
PATCH {{baseUrl}}/sensors/{{sensorId}}/
Content-Type: application/json

{
  "description": "Перенес датчик на балкон"
}

### Добавить измерение
POST {{baseUrl}}/measurements/
Content-Type: application/json

{
  "sensor": {{sensorId}},
  "temperature": 22.3
}

### Детали датчика (с измерениями)
GET {{baseUrl}}/sensors/{{sensorId}}/
Content-Type: application/json
```

### Вариант B: curl

```bash
# список датчиков
curl -i http://localhost:8000/api/sensors/

# создать датчик
curl -i -X POST http://localhost:8000/api/sensors/ \
  -H "Content-Type: application/json" \
  -d '{"name":"ESP32","description":"Датчик на кухне за холодильником"}'

# обновить датчик (замените 1 на реальный id из ответа выше)
curl -i -X PATCH http://localhost:8000/api/sensors/1/ \
  -H "Content-Type: application/json" \
  -d '{"description":"Перенес датчик на балкон"}'

# добавить измерение
curl -i -X POST http://localhost:8000/api/measurements/ \
  -H "Content-Type: application/json" \
  -d '{"sensor":1,"temperature":22.3}'

# детали датчика
curl -i http://localhost:8000/api/sensors/1/
```

Ожидаемо:
- `GET /sensors/` → `200 OK`, `[]` или список датчиков.
- `POST /sensors/` → `201 Created`, созданный `{id,name,description}`.
- `PATCH /sensors/<id>/` → `200 OK`, обновлённый объект.
- `POST /measurements/` → `201 Created`, `{sensor,temperature,created_at}`.
- `GET /sensors/<id>/` → `200 OK`, объект + `measurements: [...]`.

---

## Тестирование

Тесты лежат в `measurement/tests.py` и покрывают:
- список датчиков;
- создание датчика;
- частичное обновление датчика;
- добавление измерения;
- детальную карточку датчика с вложенными измерениями.

### Запуск (PostgreSQL)

**Вариант 1:** выдать роли право создавать тестовую БД и просто запустить тесты
```sql
ALTER ROLE netology_smart WITH CREATEDB;
```
```bash
python manage.py test measurement
```

**Вариант 2:** создать тестовую БД вручную и не удалять её
```sql
CREATE DATABASE test_netology_smart_home OWNER netology_smart ENCODING 'UTF8' TEMPLATE template0;
```
```bash
python manage.py test measurement --keepdb
```

### Запуск (SQLite, локально)

```bash
python manage.py test measurement --settings=smart_home.settings_test
```

---

## Структура проекта

```
EX1-DRF_and_CRUD_for_Smart_Home/
├── manage.py
├── requirements.txt
├── requests.http
├── smart_home/                 # проект
│   ├── settings.py
│   ├── urls.py                 # path('api/', include('measurement.urls'))
│   └── ...
└── measurement/                # приложение
    ├── models.py               # Sensor, Measurement
    ├── serializers.py          # SensorSerializer, MeasurementSerializer, SensorDetailSerializer
    ├── views.py                # ListCreate, RetrieveUpdate, Create
    ├── urls.py                 # /sensors/, /sensors/<id>/, /measurements/
    └── tests.py
```

---

## Эндпоинты

- `GET /api/sensors/` — список датчиков (`id`, `name`, `description`)
- `POST /api/sensors/` — создать датчик (`name`, `description?`)
- `GET /api/sensors/<id>/` — детали датчика + список измерений
- `PATCH /api/sensors/<id>/` — обновить название/описание
- `POST /api/measurements/` — добавить измерение (`sensor`, `temperature`)

Примеры ответов соответствуют основному заданию из README Нетологии.

---

## Скриншоты выполнения запросов

>  Изображения из `requests.http` VS Code + extention REST Client.
>
> - **Список датчиков:**  
>   ![sensors-list](docs/img/sensors-list.png)
> - **Создание датчика:**  
>   ![sensor-create](docs/img/sensor-create.png)
> - **Обновление датчика:**  
>   ![sensor-update](docs/img/sensor-update.png)
> - **Добавление измерения:**  
>   ![measurement-create](docs/img/measurement-create.png)
> - **Детали датчика:**  
>   ![sensor-detail](docs/img/sensor-detail.png)


---

## Диаграмма БД

> ![db-diagram](docs/img/db-diagram.png)

—

