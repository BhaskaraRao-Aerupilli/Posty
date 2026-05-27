# Deployment Instructions

## Local deployment

1. Create and activate a virtual environment:
   ```bash
   python -m venv .venv
   .\.venv\Scripts\Activate.ps1  # PowerShell
   # or .\.venv\Scripts\activate  # cmd.exe
   ```
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Configure environment variables:
   - `DJANGO_SECRET_KEY` (optional for local dev)
   - `DJANGO_DEBUG` set to `False` for production
   - `DJANGO_ALLOWED_HOSTS` set to a comma-separated list, e.g. `localhost,127.0.0.1`
4. Run migrations:
   ```bash
   python manage.py migrate
   ```
5. Collect static files:
   ```bash
   python manage.py collectstatic --noinput
   ```
6. Start the app locally:
   ```bash
   gunicorn myproject.wsgi --bind 0.0.0.0:8000
   ```

## Deploying to Heroku

1. Create a Heroku app:
   ```bash
   heroku create
   ```
2. Push code to Heroku:
   ```bash
   git add .
   git commit -m "Prepare Django deployment"
   git push heroku main
   ```
3. Set Heroku environment variables:
   ```bash
   heroku config:set DJANGO_SECRET_KEY="<your-secret-key>" DJANGO_DEBUG=False DJANGO_ALLOWED_HOSTS="<your-app-name>.herokuapp.com"
   ```
4. Run migrations on Heroku:
   ```bash
   heroku run python manage.py migrate
   ```

## Notes

- This project uses SQLite by default, which is not ideal for production. For a production deployment, use PostgreSQL or another managed database.
- Media uploads are stored in `media/`; configure an external file storage backend for durable production storage.
