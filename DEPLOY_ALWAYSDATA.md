AlwaysData deployment notes

1. Upload project
- Push repository to Git (or upload via SFTP).

2. Create a Python virtualenv on AlwaysData
- SSH to your AlwaysData shell
- From your project folder:

```bash
python3 -m venv venv
. venv/bin/activate
pip install -r requirements.txt
```

3. Environment variables
- Configure `BOT_TOKEN`, `DATABASE_URL`, `ADMIN_IDS`, and other secrets either via the AlwaysData web panel (Environment variables) or place a `.env` file in the project root (the app loads it with python-dotenv).

4. Database
- Use AlwaysData managed PostgreSQL or an external DB. Set `DATABASE_URL` like:

```
postgresql+asyncpg://USER:PASSWORD@HOST:PORT/DBNAME
```

5. Start the bot
- Use AlwaysData "Background processes" feature. Command example:

```
/your/path/venv/bin/python /your/path/main.py
```

Or make the process executable with `run_bot.sh` and run that.

6. Keepalive & restarts
- Configure AlwaysData background process to restart on crash. Monitor logs in the panel.

Notes
- The bot uses long-polling; AlwaysData supports long-running processes. Ensure the account plan allows persistent processes.
- If you prefer webhooks, you'd need an HTTPS endpoint and a public URL with valid certs.
