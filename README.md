# Caravan Post Bot

Telegram forwarding bot built with aiogram + Django.

## What this bot does

- Listens to live messages from `OLD_GROUP_ID`
- Forwards (copies) them to `NEW_GROUP_ID`
- Ignores old backlog messages on restart
- Uses queue + worker pool to handle high incoming traffic safely

## Local development

1. Install dependencies:
```shell
pip install -r requirements.txt
```
2. Create env file:
```shell
cp .env.example .env
```
3. Edit `.env` with your token, group IDs, and DB settings.
4. Run DB migrations:
```shell
python manage.py migrate
```
5. Start bot:
```shell
python manage.py runbot
```

## Production checklist

- Set `DEBUG=False`
- Set `ALLOWED_HOSTS` to your real domain(s) or host IPs
- Use strong `SECRET_KEY`
- Use `USE_SQLITE=False` and configure Postgres variables
- Ensure bot is admin in both groups/channels
- Set forwarding performance:
  - `FORWARD_QUEUE_MAXSIZE` (queue capacity)
  - `FORWARD_WORKERS` (parallel forward workers)
- Configure process restart policy (systemd, Docker restart, or platform worker dyno)
- Enable log collection (stdout/stderr)

## Environment variables

See `.env.example` for the full list.

Required:
- `API_TOKEN`
- `SECRET_KEY`
- `OLD_GROUP_ID`
- `NEW_GROUP_ID`

Important:
- `DEBUG` (default `False`)
- `ALLOWED_HOSTS`
- `USE_SQLITE` (`False` in production)
- `LOG_LEVEL` (`INFO` recommended)

## Deploy with Docker

Build image:
```shell
docker build -t caravan-post-bot .
```

Run bot:
```shell
docker run --env-file .env --restart unless-stopped caravan-post-bot
```

## Deploy with Docker Compose (bot + Postgres)

1. Set database and bot values in `.env`:
   - `USE_SQLITE=False`
   - `DB_USER`, `DB_PASS`, `DB_NAME`
   - `OLD_GROUP_ID`, `NEW_GROUP_ID`, `API_TOKEN`, `SECRET_KEY`
2. Start services:
```shell
docker compose up -d --build
```
3. Run migrations once:
```shell
docker compose exec bot python manage.py migrate
```
4. Check logs:
```shell
docker compose logs -f bot
```

## Procfile processes

- `worker`: bot polling (`python manage.py runbot`)
- `web`: Django app with gunicorn

Use `worker` if you only need the Telegram bot process.

## Deploy with systemd (VPS)

1. Place project at `/opt/caravan-post`
2. Create virtualenv and install requirements:
```shell
cd /opt/caravan-post
python3 -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
```
3. Copy unit file and enable service:
```shell
sudo cp deploy/caravan-bot.service /etc/systemd/system/caravan-bot.service
sudo systemctl daemon-reload
sudo systemctl enable --now caravan-bot
```
4. Verify:
```shell
sudo systemctl status caravan-bot
journalctl -u caravan-bot -f
```

Adjust `User`, `Group`, `WorkingDirectory`, and python path in `deploy/caravan-bot.service` to match your server.
