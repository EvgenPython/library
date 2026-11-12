# IT STEP — електронна бібліотека

Django-застосунок для закритої бібліотеки коледжу й університету з каталогом літератури та ZIP-репозиторієм курсових і дипломних робіт.

**Доступ:** облікові записи створює тільки адміністрація через Django Admin. Книги та архіви завантажуються лише після авторизації та перевірки дозволеного закладу.

## Локальний запуск

```bash
python -m venv .venv
# Windows: .venv\Scripts\activate
# Linux/macOS: source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env # Windows PowerShell: Copy-Item .env.example .env
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

Головна `/` — сторінка входу. `/catalog/` — дисципліни; `/repository/` — студентські роботи; `/admin/` — керування даними.

До продакшену встановіть `DJANGO_DEBUG=0`, випадковий `DJANGO_SECRET_KEY`, HTTPS, правильний `DJANGO_ALLOWED_HOSTS`, приватне сховище та резервне копіювання. Реальні книжки, ZIP, паролі та `db.sqlite3` не комітити. Завантажувати лише матеріали з відповідними правами на поширення.