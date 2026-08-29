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

## Deploying to Render

1. Connect your GitHub repo to Render and select the `main` branch.
2. Render will detect `render.yaml` and configure the web service.
3. Confirm the service settings:
   - Build command: `pip install -r requirements.txt`
   - Start command: `gunicorn myproject.wsgi --bind 0.0.0.0:$PORT`
   - Note: startup now runs `python manage.py migrate` before starting the app.
4. Ensure Render environment variables are set:
   - `DJANGO_DEBUG=False`
   - `DJANGO_ALLOWED_HOSTS=*`
   - `DJANGO_SECRET_KEY` is generated automatically by Render if configured via `render.yaml`
5. Deploy the service from the Render dashboard.

### GitHub Actions auto-deploy (optional)

This repository includes a workflow that can trigger a Render deploy via the Render API. To enable it:

1. In your GitHub repo settings, add the following **Repository secrets**:
   - `RENDER_API_KEY` — your Render API key (from Render dashboard -> Account -> API Keys)
   - `RENDER_SERVICE_ID` — the Render service ID (from the service URL or service settings)

2. After adding these secrets, a push to `main` will automatically call the Render API and trigger a deploy. You can also manually trigger the workflow from the Actions tab.

Example: find the service id in the Render dashboard URL (it appears as a long alphanumeric id in the service settings). If you prefer, trigger deploys manually from Render instead of using this workflow.

## Notes

- This project is fully configured for Render with persistent PostgreSQL support (`DATABASE_URL`).
- Media uploads and live CDN images are served seamlessly in production.

