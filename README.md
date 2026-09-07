# Simhastha 360 — Backend

FastAPI backend serving the Admin Web UI, the Mobile App (Visitor/Volunteer/Field Team modes), and the IVR/SMS webhook.

## Stack
- FastAPI + SQLAlchemy (SQLite for local/dev, swap `DATABASE_URL` for Postgres in production)
- JWT auth (admin, field team, volunteer roles) via `python-jose` + `passlib`/`bcrypt`
- No login required for visitor-facing endpoints (facilities, zones, reports, SOS, lost-person, family, health card) — matches the spec's "no smartphone/account required" principle for pilgrims

## Setup
```bash
python -m venv .venv
.venv/Scripts/activate        # Windows
pip install -r requirements.txt
cp .env.example .env          # adjust secrets
uvicorn app.main:app --reload
```

On first startup, an admin account is bootstrapped from `ADMIN_BOOTSTRAP_PHONE` / `ADMIN_BOOTSTRAP_PASSWORD` (see `.env.example`) so there's always a way into `/auth/login` without a manual seed step.

API docs: http://127.0.0.1:8000/docs

## Deploying (e.g. Vercel)
Serverless platforms give the function a read-only filesystem (aside from `/tmp`), so the local SQLite file won't work in production — use a hosted Postgres instead:

1. Create a free Postgres instance (e.g. [Neon](https://neon.tech) or [Supabase](https://supabase.com)).
2. Set `DATABASE_URL` in your platform's env vars to that instance's connection string, e.g. `postgresql://user:password@host/dbname?sslmode=require`. `psycopg2-binary` is already in `requirements.txt` to support this.
3. Set `SECRET_KEY` to a real random value (`python -c "import secrets; print(secrets.token_hex(32))"`) and `ADMIN_BOOTSTRAP_PASSWORD` to something other than the default — the bootstrap admin is created fresh on first startup against whatever `DATABASE_URL` points to.
4. Leave any env var you don't want to override **unset** in the dashboard rather than present-but-blank — `Settings` tolerates blank values by falling back to defaults, but an unset var is clearer.

## Domain map (routers ↔ spec sections)
| Router | Spec section |
|---|---|
| `auth` | login for admin / field team / volunteer |
| `facilities` | 3.2, 7.2 — find help, admin facility CRUD |
| `zones` | 3.1, 7.2 — crowd levels per zone |
| `reports` | 3.4 — crowdsourced reporting, multi-device escalation |
| `incidents` | 3.3, 6.6 — SOS auto-assign nearest responder, lost-person (human-confirmed match, no facial recognition) |
| `volunteers` | 4.1–4.3, 7.3 — apply → pending → admin review → on-duty toggle |
| `tasks` | 4.3, 5, 6.3, 7.3, 7.4 — task lifecycle + AI best-fit suggestions |
| `field_team` | 5, 7.4 — admin-created accounts, live location |
| `family` | 3.3, 8 — temporary family groups, separation alerts, public no-login share link |
| `health_card` | 3.5 — opt-in QR health summary |
| `ai` | 6.1, 6.2, 6.4 — grounded chat, predictive alert heuristic, facility-placement clustering |
| `ivr` | 6.1, 9 — provider-agnostic webhook stub reusing the same AI chat brain |

## Known placeholders (see spec §10)
- `ai.chat` uses keyword-retrieval grounding, not a wired-up LLM yet — swap-in point is clearly marked in `app/routers/ai.py`.
- `ivr.py` is a provider-agnostic stub; exact request/response fields need adjusting once an Exotel/MSG91 account is provisioned.
- Mappls SDK integration (maps, routing, geofencing) is expected to live in the web/mobile clients, calling this API for facility/zone/task data.
