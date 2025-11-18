# Deployment Guide

Complete step-by-step guide for deploying the Multi-Source Job Scraper Bot.

## Pre-Deployment Checklist

### 1. Get API Credentials

#### Reddit API
1. Go to https://www.reddit.com/prefs/apps
2. Click "Create App" or "Create Another App"
3. Fill in:
   - **Name**: JobBot (or any name)
   - **Type**: Select "script"
   - **Description**: Job scraping bot
   - **Redirect URI**: http://localhost:8080 (required but not used)
4. Click "Create app"
5. Note down:
   - **Client ID**: Under the app name (random string)
   - **Client Secret**: Click "secret" to reveal

#### Discord Bot
1. Go to https://discord.com/developers/applications
2. Click "New Application"
3. Name it (e.g., "Job Scraper Bot")
4. Go to "Bot" tab → Click "Add Bot"
5. **IMPORTANT**: Under "Privileged Gateway Intents", enable:
   - ✅ Message Content Intent (REQUIRED!)
6. Copy the bot token (click "Reset Token" if needed)
7. Go to "OAuth2" → "URL Generator"
8. Select scopes:
   - ✅ bot
9. Select permissions:
   - ✅ Send Messages
   - ✅ Embed Links
   - ✅ Attach Files
   - ✅ Read Message History
10. Copy generated URL and open in browser to invite bot to your server

#### Discord Channel ID (Optional - Can be Set Later)

**Option 1: Set via Discord command** (Recommended)
- After starting the bot, use `!setchannel #channel` command in Discord
- This method allows changing channels without restarting the bot

**Option 2: Set in .env file**
1. Enable Developer Mode in Discord (User Settings → Advanced → Developer Mode)
2. Right-click your target channel → "Copy ID"
3. Add to `.env`: `DISCORD_CHANNEL_ID=your_channel_id`

### 2. Configure Environment

Copy the example environment file:
```bash
cp .env.example .env
```

Edit `.env` with your credentials:
```bash
REDDIT_CLIENT_ID=your_client_id_from_step_1
REDDIT_CLIENT_SECRET=your_client_secret_from_step_1
REDDIT_USER_AGENT=JobBot/1.0 by YourRedditUsername
DISCORD_TOKEN=your_discord_bot_token

# Optional: Set channel here, or use !setchannel command after bot starts
# DISCORD_CHANNEL_ID=your_channel_id
```

### 3. Configure Sources (Optional)

Edit `config.yaml` to enable additional sources:

```yaml
platforms:
  hackernews:
    enabled: true  # Enable HackerNews "Who is hiring?" threads
    check_frequency_hours: 6

  company_monitor:
    enabled: true  # Enable company career page monitoring
    companies:
      - name: "Shopify"
        url: "https://www.shopify.com/careers"
      - name: "Stripe"
        url: "https://stripe.com/jobs"
      - name: "Your Target Company"
        url: "https://company.com/careers"
```

### 4. Validate Setup

Run the validation script to check your configuration:

```bash
python scripts/validate_setup.py
```

Fix any issues reported before proceeding.

## Deployment Options

### Option A: Docker (Recommended)

**Advantages:**
- Isolated environment
- Easy deployment
- Automatic restarts
- Consistent across systems

**Steps:**

1. Ensure Docker and docker-compose are installed
2. Validate configuration: `python scripts/validate_setup.py`
3. Build and start:
   ```bash
   docker-compose up -d
   ```
4. Set job posting channel in Discord:
   ```
   !setchannel #jobs-channel
   ```
   (Skip if you set `DISCORD_CHANNEL_ID` in `.env`)
5. View logs:
   ```bash
   docker-compose logs -f
   ```
6. Stop bot:
   ```bash
   docker-compose down
   ```

**Updating:**
```bash
docker-compose down
git pull
docker-compose up -d --build
```

### Option B: Local Python

**Advantages:**
- Easier debugging
- Direct file access
- Faster iteration

**Steps:**

1. Create virtual environment:
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Run database migrations:
   ```bash
   python scripts/migrate_db.py
   ```

4. Validate setup:
   ```bash
   python scripts/validate_setup.py
   ```

5. Start the bot:
   ```bash
   python main.py
   ```

6. In Discord, set the job posting channel:
   ```
   !setchannel #jobs-channel
   ```
   (Skip if you set `DISCORD_CHANNEL_ID` in `.env`)

**Running in background (Linux/Mac):**
```bash
nohup python main.py > logs/bot.log 2>&1 &
```

**Using systemd (Linux):**

Create `/etc/systemd/system/redbot.service`:
```ini
[Unit]
Description=Reddit Job Scraper Bot
After=network.target

[Service]
Type=simple
User=your_username
WorkingDirectory=/path/to/redbot
Environment="PATH=/path/to/redbot/venv/bin"
ExecStart=/path/to/redbot/venv/bin/python main.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
sudo systemctl enable redbot
sudo systemctl start redbot
sudo systemctl status redbot
```

### Option C: Cloud Deployment

#### AWS EC2 / DigitalOcean / Linode

1. Create a small instance (t2.micro / $5 droplet sufficient)
2. SSH into server
3. Clone repository:
   ```bash
   git clone <repository-url>
   cd redbot
   ```
4. Follow **Option A (Docker)** or **Option B (Local Python)** steps above

#### Heroku

1. Create `Procfile`:
   ```
   worker: python main.py
   ```

2. Deploy:
   ```bash
   heroku create your-job-bot
   heroku config:set REDDIT_CLIENT_ID=xxx
   heroku config:set REDDIT_CLIENT_SECRET=xxx
   heroku config:set REDDIT_USER_AGENT=xxx
   heroku config:set DISCORD_TOKEN=xxx
   heroku config:set DISCORD_CHANNEL_ID=xxx
   git push heroku main
   heroku ps:scale worker=1
   ```

## Post-Deployment

### Verify Bot is Working

1. Check Discord - bot should show as online
2. Wait 1-2 minutes for first job check cycle
3. Run `!help` in Discord to test commands
4. Check logs for any errors

### Monitor the Bot

**Docker:**
```bash
docker-compose logs -f
```

**Local Python:**
```bash
tail -f logs/redbot.log
```

**Check job statistics:**
Type `!stats` in your Discord channel

### Troubleshooting

**Bot doesn't come online:**
- Check Discord token is correct
- Verify Message Content Intent is enabled
- Check logs for connection errors

**No jobs being posted:**
- Check Reddit credentials are correct
- Verify channel ID is correct
- Check `config.yaml` subreddits list
- Check if keywords filter is too restrictive
- View logs to see what's happening

**Commands not responding:**
- Verify Message Content Intent is enabled (critical!)
- Check bot has permissions in the channel
- Try `!help` command

**Database errors:**
- Ensure `scripts/migrate_db.py` was run
- Check file permissions on `sent_posts.db`
- Try deleting database and running migrations again

## Maintenance

### Backup Database

```bash
# Copy database file
cp sent_posts.db sent_posts.db.backup

# Or export to CSV
# Run in Discord:
!export
```

### Update Bot

```bash
# Stop bot
docker-compose down  # or Ctrl+C for local

# Update code
git pull

# Restart
docker-compose up -d --build  # or python main.py
```

### Clean Old Data

Jobs older than 365 days are automatically archived (configurable in `config.yaml`).

Manual cleanup:
```sql
sqlite3 sent_posts.db
DELETE FROM job_postings WHERE created_utc < strftime('%s', 'now', '-90 days');
```

## Monitoring & Alerts

The bot includes built-in health monitoring. Check `config.yaml`:

```yaml
health:
  heartbeat_interval_seconds: 300  # 5 minutes
  alert_threshold_minutes: 15  # Alert if source down
```

Set up external monitoring (optional):
- **UptimeRobot**: Monitor bot heartbeat endpoint
- **Sentry**: Error tracking (add sentry-sdk to requirements)
- **CloudWatch/Datadog**: System metrics for cloud deployments

## Security Best Practices

1. **Never commit `.env` file** - It contains secrets
2. **Rotate tokens regularly** - Refresh Reddit/Discord credentials quarterly
3. **Limit bot permissions** - Only grant necessary Discord permissions
4. **Keep dependencies updated** - Run `pip list --outdated` monthly
5. **Monitor rate limits** - Check logs for rate limit warnings
6. **Use firewalls** - Restrict server access (SSH only from trusted IPs)

## Performance Optimization

For high-volume deployments:

1. **Increase check frequency** (config.yaml):
   ```yaml
   scraping:
     check_frequency_seconds: 30  # More frequent checks
   ```

2. **Add more subreddits** (config.yaml):
   ```yaml
   reddit:
     subreddits:
       - forhire
       - jobbit
       - <add more>
   ```

3. **Tune rate limits** (config.yaml):
   ```yaml
   rate_limits:
     reddit: 60  # Requests per minute
   ```

4. **Database optimization**:
   ```bash
   sqlite3 sent_posts.db "VACUUM;"
   ```

## Support

- Issues: https://github.com/yourusername/redbot/issues
- Documentation: See README.md and ARCHITECTURE.md
- Logs: Check `logs/redbot.log` for detailed information
