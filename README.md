# IT STEP — електронна бібліотека

Закрита Django-бібліотека для коледжу та університету: дисципліни, книги й ZIP-архіви курсових та дипломних робіт. Облікові записи створює тільки адміністратор; публічної реєстрації немає.

## Запуск

```bash
python -m venv .venv
# Windows: .venv\Scripts\activate
# Linux: source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

Шляхи: `/` — вхід; `/catalog/` — бібліотека; `/repository/` — ZIP-архіви; `/admin/` — адміністрування. Імпорт студентів: Admin → Профілі студентів → Імпортувати студентів (CSV). Поля: `username,first_name,last_name,institution_slug`.

**Безпека:** перед публікацією налаштуйте секретний ключ, HTTPS, домен, резервні копії, належні права на навчальну літературу і архіви. `.env`, `db.sqlite3`, приватні файли й паролі не завантажувати в GitHub.

## Оновлення сервера

```bash
git pull --ff-only origin main
pip install -r requirements.txt
python manage.py migrate
python manage.py collectstatic --noinput
# далі перезапуск вебсервісу
```
