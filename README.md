# Vireo support digest

Weekly complaint digest + a fairer agent leaderboard, built from the Vireo helpdesk export.
Runs on plain pandas. **No API keys, no paid calls, about 12 seconds for 18 months of tickets.**

## Run it (clean machine)

```bash
python3 -m venv .venv && source .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -r requirements.txt
mkdir data                                               # put tickets.csv and agents.csv in data/
python run.py --tickets data/tickets.csv --agents data/agents.csv --out out
```

Options: `--week 2026-06-22` (Monday of the week to report; default is the last complete week),
`--weekly-volume 650` (Vireo's real weekly volume, used only to scale the rupee figures).

## What you get in `out/`

| File | What it is |
|---|---|
| `weekly_digest.md` | The digest: ticket count, complaint themes vs the prior 4 weeks, breaches, repeat contacts, "I already told your colleague" share |
| `leaderboard.md` / `.csv` | Agents ranked within team on tickets that **stayed closed**; Tier 2 shown on days-to-resolve, not volume |
| `summary.json` | Headline numbers, the goal statement, and data-quality counts |
| `policy_flags_refund_and_replacement.csv` | Tickets where a refund and a replacement were both issued (policy s.5) |
| `tickets_enriched.csv` | Every ticket with theme, repeat flag, shift flags (message text removed) |

`example_output/` holds a copy of a run so you can read the results without running anything.

## How it works

1. `vireo/clean.py`: drops the 653 tickets that appear twice (Freshdesk re-import), shifts legacy `resolved_at` from UTC to IST, turns legacy CSAT 0 into blank.
2. `vireo/themes.py`: typo-tolerant keyword rules assign each customer message to one of 16 themes. This replaces the intake bot's category tag, which is unreliable (see VALIDATION.md).
3. `vireo/analysis.py`: repeat contacts, shift-handover breach analysis, leaderboard, weekly digest.

Read `DECISIONS.md` for every judgement call, `VALIDATION.md` for accuracy, `MEMO.md` for the client memo.
Data files are not in the repo (client data); `data/` and `out/` are git-ignored.
