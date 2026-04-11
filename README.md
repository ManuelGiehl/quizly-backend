# Quizly Backend

Django REST API for **Quizly**: turn a **YouTube URL** into a persisted multiple-choice quiz. Pipeline: **yt-dlp** (audio) → **OpenAI Whisper** (local transcription) → **Google Gemini** (structured quiz JSON) → SQLite + ORM.

Authentication uses **JWT in HttpOnly cookies** (access + refresh), with optional **Authorization: Bearer** for tools like Postman.

---

## Prerequisites

| Requirement | Notes |
|-------------|--------|
| **Python** | 3.10 or newer (3.12 recommended). |
| **ffmpeg** | Must be on your `PATH` (Whisper decodes audio via ffmpeg). [Download](https://ffmpeg.org/download.html) and verify: `ffmpeg -version`. |
| **Gemini API key** | [Google AI Studio](https://aistudio.google.com/apikey) — required for `POST /api/quizzes/`. |
| **Disk / RAM** | First Whisper run downloads model weights; long videos use more RAM. Use `WHISPER_MODEL=tiny` in `.env` if needed. |

Optional: **NVIDIA GPU + CUDA** speeds up Whisper (PyTorch); CPU works, slower on long audio.

---

## Repository layout (this folder)

All paths below are relative to **`backend/`** (this directory — it contains `manage.py`).

```
.
├── .env.example             # copy to .env (never commit .env)
├── requirements.txt
├── manage.py
├── README.md                # this file
├── core/                    # Django project settings and root URLconf
├── auth_app/                # JWT cookie auth API
└── quiz_app/                # quizzes, YouTube → AI pipeline
```

All shell commands assume your **current working directory** is this folder. (the folder that contains 'manage.py').

---

## Step-by-step setup

### 1. Open a terminal in the Django project folder

`cd` into the directory that contains **`manage.py`** and **`requirements.txt`** (in some layouts that is a subfolder named `backend/`; in others the repo root is the Django project).

### 2. Create and activate a virtual environment

**Windows (PowerShell):**

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

**macOS / Linux:**

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Install Python dependencies

```bash
python -m pip install --upgrade pip
pip install -r requirements.txt
```

`openai-whisper` will pull **PyTorch** and related wheels (large download on first install).

### 4. Configure environment variables

```bash
# Windows (PowerShell), from backend/
Copy-Item .env.example .env
```

```bash
# macOS / Linux, from backend/
cp .env.example .env
```

Edit **`backend/.env`** (next to `manage.py`):

1. **`DJANGO_SECRET_KEY`** — generate once:

   ```bash
   python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
   ```

   Paste the output into `.env` (no quotes).

2. **`GEMINI_API_KEY`** — paste your key from Google AI Studio.

3. Optional: **`WHISPER_MODEL`** (`tiny`, `base`, `small`, …), **`GEMINI_MODEL`**, **`GEMINI_HTTP_TIMEOUT_MS`**, **`DJANGO_CORS_ALLOWED_ORIGINS`** (comma-separated; set this if your calling browser app’s origin is not in the default dev list in `core/settings.py`).

Save **UTF-8 without BOM** (VS Code: status bar encoding).

### 5. Apply database migrations

```bash
python manage.py migrate
```

### 6. (Optional) Create an admin user

```bash
python manage.py createsuperuser
```

Useful for inspecting data at `http://127.0.0.1:8000/admin/`.

### 7. Run the development server

```bash
python manage.py runserver
```

API base URL: **`http://127.0.0.1:8000/api/`**.

---

## Smoke-test the API

### 1. Health check (no auth)

```bash
curl -s http://127.0.0.1:8000/api/health/
```

Expected: JSON like `{"status":"ok"}`.

### 2. Register a user

```bash
curl -s -X POST http://127.0.0.1:8000/api/register/ ^
  -H "Content-Type: application/json" ^
  -d "{\"username\":\"demo\",\"email\":\"demo@example.com\",\"password\":\"YourStrongPass1!\",\"confirmed_password\":\"YourStrongPass1!\"}"
```

*(On macOS/Linux use `\` line continuation and single-line `curl`, or a JSON file with `-d @register.json`.)*

### 3. Log in (stores HttpOnly cookies)

**Windows PowerShell** — save cookies to a file:

```powershell
curl -s -c cookies.txt -X POST http://127.0.0.1:8000/api/login/ `
  -H "Content-Type: application/json" `
  -d '{"username":"demo","password":"YourStrongPass1!"}'
```

**macOS / Linux:**

```bash
curl -s -c cookies.txt -X POST http://127.0.0.1:8000/api/login/ \
  -H "Content-Type: application/json" \
  -d '{"username":"demo","password":"YourStrongPass1!"}'
```

Response body includes user info; tokens are in **`access_token`** and **`refresh_token`** cookies (not shown in JSON).

### 4. Call a protected route with cookies

```bash
curl -s -b cookies.txt http://127.0.0.1:8000/api/me/
```

Expected: `{"id":...,"username":"demo","email":"demo@example.com"}`.

### 5. Create a quiz from a YouTube URL

Uses Whisper + Gemini; **first run** may download the Whisper model and can take **minutes**. Prefer a **short** video for testing.

```bash
curl -s -b cookies.txt -X POST http://127.0.0.1:8000/api/quizzes/ ^
  -H "Content-Type: application/json" ^
  -d "{\"url\":\"https://www.youtube.com/watch?v=jNQXAC9IVRw\"}"
```

On success: **201** with full quiz JSON (title, description, transcript, questions).

### 6. List your quizzes

```bash
curl -s -b cookies.txt http://127.0.0.1:8000/api/quizzes/
```

### Postman / Insomnia

1. **Register** and **Login** with `POST` as above; enable the client’s **cookie jar** so `Set-Cookie` is stored.
2. For later requests, ensure cookies are sent (same host/port, usually fine for `127.0.0.1:8000`).
3. Alternatively, after login, copy the **`access_token`** cookie value and add header: `Authorization: Bearer <token>` (SimpleJWT is enabled alongside cookie auth).

---

## HTTP API overview

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | `/api/health/` | No | Liveness check. |
| POST | `/api/register/` | No | Create user (`username`, `email`, `password`, `confirmed_password`). |
| POST | `/api/login/` | No | Sets JWT cookies; JSON body: `username`, `password`. |
| POST | `/api/logout/` | Yes | Blacklists refresh token (if configured); clears cookies. |
| POST | `/api/token/refresh/` | No | New access token from `refresh_token` cookie. |
| GET | `/api/me/` | Yes | Current user from cookie or Bearer token. |
| GET, POST | `/api/quizzes/` | Yes | List quizzes (GET) or create from YouTube (POST JSON `{"url":"..."}`). |
| GET, PATCH, DELETE | `/api/quizzes/<id>/` | Yes | Quiz detail, partial update (`title`, `description`), or delete. |

Admin: `/admin/` (requires superuser).

---

## Troubleshooting

| Symptom | What to check |
|---------|----------------|
| **Whisper / ffmpeg errors** | `ffmpeg` on `PATH`; try `WHISPER_MODEL=tiny`; ensure audio download succeeded (check `Could not download audio` vs transcription errors). |
| **Gemini errors** | Valid `GEMINI_API_KEY`; model name (`GEMINI_MODEL`); response body often includes `HTTP` status and API message. |
| **401 on `/api/quizzes/`** | Log in again; send cookies or `Authorization: Bearer`. |
| **CORS in the browser** | Set `DJANGO_CORS_ALLOWED_ORIGINS` in `.env` to the exact origin(s) of the client app (comma-separated, no spaces unless part of URL). |
| **`DJANGO_SECRET_KEY` error** | `.env` must live in **`backend/`** next to `manage.py` (same level as `manage.py`). |

---

## Tech stack (Python packages)

See **`backend/requirements.txt`**: Django, DRF, SimpleJWT + blacklist, CORS, python-dotenv, yt-dlp, openai-whisper, google-genai.

---

## Security notes

- **Never commit `backend/.env`** — it is gitignored. Commit **`.env.example`** only.
- Production: set `DJANGO_DEBUG=False`, strong `DJANGO_SECRET_KEY`, restrict `ALLOWED_HOSTS` / CORS, enable `AUTH_COOKIE_SECURE` (HTTPS), and use a production database and static/media strategy.
