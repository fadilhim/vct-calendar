# VCT 2026 Calendar

📅 **Subscribe to VCT 2026 matches in your calendar app.**

ICS calendar for Valorant Champions Tour 2026, automatically updated from [vlr.gg](https://www.vlr.gg).

## 🔗 Subscribe (Recommended)

Add this URL to your calendar app for automatic updates:

```
https://raw.githubusercontent.com/fadilhim/vct-calendar/main/vct-2026.ics
```

| App                 | How to Subscribe                    |
|---------------------|-------------------------------------|
| **Google Calendar** | Settings → Add calendar → From URL  |
| **Apple Calendar**  | File → New Calendar Subscription    |
| **Outlook**         | Add calendar → Subscribe from web   |
\

## 📋 Regions Included

- 🌎 Americas
- 🌍 EMEA
- 🌏 Pacific
- 🇨🇳 China

## 📅 Event Format

```
VCT 2026 Pacific Kickoff - Paper Rex vs T1 (Upper Round 2)
```

## 🛠️ For Contributors

### Setup

```bash
pip install -r requirements.txt
```

### Update (Refresh Data)

Update current and upcoming VCT 2026 events with latest data from vlr.gg:

```bash
python update_calendar.py
```

For VPS automation that refreshes and pushes `vct-2026.ics` on a cron schedule, see [docs/vps-cron.md](docs/vps-cron.md).

This updates:
- Team names (TBD → actual teams)
- Match times (reschedules)
- Match status (completed)

## 📅 VCT 2026 Stages

The update command checks all configured VCT 2026 stages, including both Masters events, and only scrapes tournaments whose end date is today or later. Past tournaments stay in the calendar but are not refreshed.

## ⚠️ Disclaimer

This project is **not affiliated with or endorsed by Riot Games or vlr.gg**.

- VALORANT and VCT are trademarks of Riot Games, Inc.
- Match data is sourced from [vlr.gg](https://www.vlr.gg)
- This is an unofficial community project

## 📄 License

MIT License - see [LICENSE](LICENSE)
