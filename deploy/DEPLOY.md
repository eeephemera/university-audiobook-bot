# Deploying on a VPS

The bot uses **long polling**, so it needs no public IP, no domain and no open
inbound ports — just outbound HTTPS to `api.telegram.org`. Pick ONE of the two
options below.

> ⚠️ Run only **one** instance against a given bot token. Two pollers fight over
> updates (`Conflict: terminated by other getUpdates`).

---

## Option A — Docker (recommended)

```bash
git clone <your-repo> university-audiobook-bot
cd university-audiobook-bot
cp .env.example .env && nano .env        # set BOT_TOKEN, ADMIN_IDS, BRAND_NAME

# Build & start (compose file lives in deploy/)
docker compose -f deploy/docker-compose.yml up -d --build

# Seed the sample catalog (so something shows up immediately)
docker compose -f deploy/docker-compose.yml run --rm bot python -m scripts.seed

docker compose -f deploy/docker-compose.yml logs -f
```

The SQLite database is persisted in `./data` on the host via a volume.

To import real audio/PDF later, see the main `README.md` → *Adding materials*.

---

## Option B — systemd + virtualenv (no Docker)

```bash
sudo adduser --system --group botuser
sudo mkdir -p /opt/university-audiobook-bot
sudo chown botuser:botuser /opt/university-audiobook-bot

# as botuser: copy the project there, then
cd /opt/university-audiobook-bot
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
cp .env.example .env && nano .env
.venv/bin/python -m scripts.seed

# install the service
sudo cp deploy/bot.service /etc/systemd/system/university-audiobook-bot.service
sudo systemctl daemon-reload
sudo systemctl enable --now university-audiobook-bot
journalctl -u university-audiobook-bot -f
```

---

## Updating

```bash
git pull
# Docker:
docker compose -f deploy/docker-compose.yml up -d --build
# systemd:
.venv/bin/pip install -r requirements.txt && sudo systemctl restart university-audiobook-bot
```

## Backups

Back up a single file — the SQLite DB:

```bash
cp data/bot.db "backups/bot-$(date +%F).db"
```

Because audio/PDF live on Telegram's servers (only `file_id`s are stored), this
small file is your entire content database.
