# Server — Центральный диспетчерский сервер

Серверная часть системы Genius Loci: FastAPI бекенд и React фронтенд.

## Структура

```
Server/
├── backend/                  # FastAPI сервер
│   ├── main.py               # Точка входа
│   ├── config.py             # Конфигурация сервера
│   ├── requirements.txt      # Python-зависимости
│   ├── core/
│   │   └── logger.py         # Логгер
│   └── app/
│       ├── models/
│       │   └── database.py   # SQLAlchemy модели
│       ├── schemas/
│       │   └── schemas.py    # Pydantic схемы
│       ├── routers/          # Роутеры API
│       │   ├── auth.py       # JWT-аутентификация
│       │   ├── robots.py     # Управление роботами
│       │   ├── tasks.py      # Управление задачами
│       │   ├── maps.py       # Карты склада
│       │   └── logs.py       # Системные логи
│       └── services/
│           ├── websocket_manager.py  # WebSocket-менеджер
│           └── dispatcher.py         # Диспетчер задач
│
└── frontend/                 # React Web AIS
    ├── package.json
    ├── vite.config.ts
    └── src/
        ├── components/       # Layout, RobotMap
        ├── pages/            # Dashboard, Tasks, Map, etc.
        ├── hooks/            # useWebSocket
        └── store.ts          # Zustand state
```

## Быстрый старт

### Бекенд

```bash
cd Server/backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python main.py
# Сервер на http://localhost:8000
# Swagger: http://localhost:8000/docs
```

### Фронтенд

```bash
cd Server/frontend
npm install
npm run dev
# Интерфейс на http://localhost:5173
```

## Переменные окружения

| Переменная | По умолчанию | Описание |
|------------|--------------|----------|
| `DATABASE_URL` | `sqlite:///./genius_loci.db` | URL базы данных |
| `SERVER_HOST` | `0.0.0.0` | Хост сервера |
| `SERVER_PORT` | `8000` | Порт сервера |
| `JWT_SECRET` | `change-this-secret-in-production` | Секрет JWT |
