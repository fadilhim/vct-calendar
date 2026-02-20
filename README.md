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

### Generate (New Tournament)

Add a new stage/tournament to the calendar:

```bash
# First stage (creates file)
python generate_calendar.py --stage kickoff

# Additional stages (appends to existing)
python generate_calendar.py --stage masters --append
```

### Update (Refresh Data)

Update existing events with latest data from vlr.gg:

```bash
python update_calendar.py
```

This updates:
- Team names (TBD → actual teams)
- Match times (reschedules)
- Match status (completed)

Update specific stage(s) only:

```bash
python update_calendar.py --stage kickoff
python update_calendar.py --stage kickoff --stage masters
```

## 📅 VCT 2026 Stages

| Stage     | Timing  | Command             |
|-----------|---------|---------------------|
| Kickoff   | Jan-Feb | `--stage kickoff`   |
| Masters   | Mar-Apr | `--stage masters`   |
| Stage 1   | May-Jun | `--stage stage1`    |
| Stage 2   | Jul-Aug | `--stage stage2`    |
| Champions | Sep     | `--stage champions` |

## ⚠️ Disclaimer

This project is **not affiliated with or endorsed by Riot Games or vlr.gg**.

- VALORANT and VCT are trademarks of Riot Games, Inc.
- Match data is sourced from [vlr.gg](https://www.vlr.gg)
- This is an unofficial community project

## 📄 License

MIT License - see [LICENSE](LICENSE)
