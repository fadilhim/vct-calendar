# VCT 2026 Calendar

ICS calendar for Valorant Champions Tour 2026 events, scraped from [vlr.gg](https://www.vlr.gg).

## Setup

```bash
pip install -r requirements.txt
```

## Usage

### Generate Calendar (Initial)

```bash
python generate_calendar.py
```

Options:
- `--stage`: Stage to generate (kickoff, masters, stage1, stage2, champions)
- `--output`: Output file path (default: vct-2026.ics)

### Update Calendar (Refresh Data)

```bash
python update_calendar.py
```

Updates existing events with latest data from vlr.gg:
- Team names (TBD → actual teams)
- Match times (if rescheduled)
- Match status

**Note:** Update script never adds new events - only updates existing ones.

Options:
- `--input`: Input ICS file (default: vct-2026.ics)
- `--output`: Output file path (default: same as input)
- `--stage`: Stage(s) to update. Auto-detects from calendar if not specified.

### Adding New Stages

See the [Adding New Stages Tutorial](#adding-new-stages-tutorial) section below for a comprehensive guide.

### Import to Calendar App

1. Run `python generate_calendar.py`
2. Import `vct-2026.ics` into your calendar application:
   - **Google Calendar**: Settings → Import & Export → Import
   - **Apple Calendar**: File → Import
   - **Outlook**: File → Open & Export → Import/Export

## Features

- Scrapes all matches from VCT 2026 Kickoff (Americas, EMEA, Pacific)
- Stable UIDs for each match (allows updating without duplicates)
- 2-hour event duration for Bo3 matches
- Match URLs included in event description
- Times converted from WIB (UTC+7) to UTC

## File Structure

```
VCT Calendar/
├── vct-2026.ics              # Main calendar (all stages)
├── calendars/                # Individual stage calendars
│   ├── kickoff.ics
│   ├── masters.ics
│   └── ...
├── src/
│   ├── config.py             # Configuration (stages, regions)
│   ├── models.py             # Data classes (Match, Tournament)
│   ├── scraper.py            # vlr.gg scraping logic
│   └── calendar_generator.py # ICS generation
├── generate_calendar.py      # Initial generation script
├── update_calendar.py        # Update existing events
└── requirements.txt          # Python dependencies
```

---

## Adding New Stages Tutorial

This guide walks you through adding new VCT stages to your calendar as they become available throughout the 2026 season.

### VCT 2026 Stage Schedule

| Stage | Typical Timing | Stage ID | Command |
|-------|---------------|----------|---------|
| Kickoff | January-February | `kickoff` | `--stage kickoff` |
| Masters | March-April | `masters` | `--stage masters` |
| Stage 1 | May-June | `stage1` | `--stage stage1` |
| Stage 2 | July-August | `stage2` | `--stage stage2` |
| Champions | September | `champions` | `--stage champions` |

### Workflow Overview

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│  New stage      │     │  Append to      │     │  Regular        │
│  announced on   │ ──► │  existing       │ ──► │  updates with   │
│  vlr.gg         │     │  calendar       │     │  update script  │
└─────────────────┘     └─────────────────┘     └─────────────────┘
```

### Step 1: Check if Stage is Available

Before adding a new stage, verify it's listed on vlr.gg:

1. Visit https://www.vlr.gg/vct
2. Check if the stage tab shows tournaments (e.g., "Masters" tab)
3. Ensure match schedules are posted

### Step 2: Add the New Stage

**Option A: Append to main calendar (recommended)**

```bash
python generate_calendar.py --stage masters --append
```

This adds all Masters matches to your existing `vct-2026.ics` without affecting Kickoff events.

**Option B: Append and save individual stage file**

```bash
python generate_calendar.py --stage masters --append --save-stage
```

This does the same as Option A, plus saves `calendars/masters.ics` for stage-specific use.

**Option C: Generate stage-only calendar**

```bash
python generate_calendar.py --stage masters --output calendars/masters.ics
```

Creates a separate calendar with only Masters events (does not modify main calendar).

### Step 3: Verify the Addition

After adding a new stage, verify everything worked:

```bash
python update_calendar.py
```

Expected output:
```
Loading existing calendar from vct-2026.ics...
Found 180 existing events
Auto-detected stages: kickoff, masters    ← Should show both stages

Scraping latest data from vlr.gg...
  Fetching kickoff...
  Fetching masters...
Found 180 total matches from vlr.gg
```

### Step 4: Re-import to Calendar App

After adding new stages, re-import the updated `vct-2026.ics`:

| App | Re-import Method |
|-----|-----------------|
| **Google Calendar** | Delete old calendar → Import new file |
| **Apple Calendar** | File → Import (updates existing events by UID) |
| **Outlook** | Import will merge based on UIDs |

> **Tip:** Most calendar apps handle duplicate UIDs gracefully - they update existing events rather than creating duplicates.

### Step 5: Keep Updated

Run the update script periodically to refresh match data:

```bash
python update_calendar.py
```

The update script automatically:
- Detects all stages in your calendar
- Fetches latest data for each stage
- Updates team names (TBD → actual teams)
- Updates match times (if rescheduled)
- Updates match status (completed matches)

### Example: Full Season Setup

Here's how to build your calendar throughout the VCT 2026 season:

```bash
# January: Start with Kickoff
python generate_calendar.py --stage kickoff --save-stage

# March: Add Masters when announced
python generate_calendar.py --stage masters --append --save-stage

# May: Add Stage 1
python generate_calendar.py --stage stage1 --append --save-stage

# July: Add Stage 2
python generate_calendar.py --stage stage2 --append --save-stage

# September: Add Champions
python generate_calendar.py --stage champions --append --save-stage
```

Your final calendar structure:
```
vct-2026.ics           # All 450 events (90 per stage × 5 stages)
calendars/
├── kickoff.ics        # 90 events
├── masters.ics        # 90 events
├── stage1.ics         # 90 events
├── stage2.ics         # 90 events
└── champions.ics      # 90 events
```

### Troubleshooting

**Q: I accidentally ran without `--append` and lost my other stages**

A: Re-run with each stage:
```bash
python generate_calendar.py --stage kickoff
python generate_calendar.py --stage masters --append
# ... repeat for other stages
```

**Q: Duplicate events appearing in my calendar app**

A: This shouldn't happen due to stable UIDs, but if it does:
1. Delete the calendar from your app
2. Re-import `vct-2026.ics`

**Q: A stage shows 0 matches**

A: The stage might not be available on vlr.gg yet. Check https://www.vlr.gg/vct to verify matches are posted.

**Q: How do I update only one specific stage?**

A:
```bash
python update_calendar.py --stage masters
```

**Q: How do I update multiple specific stages?**

A:
```bash
python update_calendar.py --stage kickoff --stage masters
```
