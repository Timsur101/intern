# Proxy Service

Веб-сервис с регистрацией, личным кабинетом и десктопным клиентом для подключения к прокси.

## Как запустить

```bash
docker-compose up -d
```

- Сайт: http://localhost:3000
- API docs: http://localhost:8000/docs

## Регистрация и ключ

1. Открыть http://localhost:3000/register
2. Ввести email и пароль
3. Ключ придёт на почту (если SMTP настроен)

Если SMTP не настроен — ключ выводится в логах воркера:
```bash
docker-compose logs celery_worker
```
Или посмотреть в профиле на сайте.

## Десктопное приложение

Нужен Python 3.8+

```bash
cd desktop
pip install -r requirements.txt
python app.py
```

Вставить ключ → нажать "Подключиться".

## Тесты

```bash
cd backend
pip install -r requirements.txt
pip install aiosqlite
pytest tests/ -v
```

## SMTP (необязательно)

Прописать в docker-compose.yml переменные SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASSWORD.
Можно использовать Mailtrap для тестирования.
