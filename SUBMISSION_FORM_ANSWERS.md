# Submission form answers (draft; items in [BRACKETS] are yours to fill or confirm)

**1. What did you build, and what business outcome does it move? State the number and the money.**
A command-line tool that cleans the Vireo export and produces a weekly complaint digest and a fairer agent leaderboard. Headline goal: cut first-response breaches from 8.9% to 5.8% of tickets (the rate same-shift tickets already achieve; tickets handed across a shift boundary breach at 16.0%). Worth about Rs 1.0 lakh a quarter in Rs 350 SLA credits at 650 tickets/week (Rs 23,549 a quarter at the export's own ~152/week). Second lever: repeat contacts, ~10.3% of tickets, about Rs 2.2 lakh a quarter at 650/week; a one-third cut is worth about Rs 74,000.

**2. What does one run cost, and what would a month cost at ~650 tickets a week? Show the arithmetic.**
No paid calls. The tagger is rule-based, so a run costs Rs 0 and takes about 12 seconds for 11,875 tickets. Month at 650/week: 650 x 52 / 12 = about 2,817 tickets x Rs 0 = Rs 0. (I did not build an LLM fallback for the 3.8% "Unclear" tickets; that is the obvious place a paid call would go.)

**3. How do you know it works?**
Three random samples of tickets, read one by one and marked right/wrong. Final round, on the shipped code and a fresh sample: 54 of 60 correct = 90% (95% interval roughly 78-97%). Errors: typos inside multi-word phrases (3), an unusual OTP phrasing (1), ambiguous dead-earbud message (1), snapped strap filed as damage (1). Earlier rounds (82.5% and 93.8%) were used to fix the rules so they overstate accuracy. The labels were made by an AI assistant, not a Vireo agent. [Confirm/adjust if you spot-checked any.] Data repairs were checked directly: legacy resolved_at differs from the helpdesk copy by exactly 5.5h on all 618 comparable duplicate pairs; negative resolution times went from 1,874 to 0. Details: VALIDATION.md.

**4. Did you change, narrow, or push back on the client's ask?**
Yes. (a) Leaderboard kept but not "tickets closed": 54% of the spread in raw counts is team membership, and the raw top ten has no chat or voice agent. I ranked within team on tickets that stayed closed and showed Tier 2 on days to resolve (policy s.6, Neha's request). (b) Digest themes come from customer text, not the bot category tag. (c) Used policy s.4 channel costs, not Arjun's Rs 180. (d) Asked for a weekly digest; the biggest money was in something the digest alone would not show (shift-handover breaches), so I put that first in the memo.

**5. What is wrong with what you are handing us?**
- Tagger labels were made by an AI assistant, n=60 final sample, wide interval.
- Keyword rules are tuned on this export's templated-looking messages; real free text and Hinglish will do worse. No unit tests.
- Shift-handover is inferred from the resolver's shift; the first responder isn't in the data. Association, not proven cause.
- Volume mismatch: export ~152 tickets/week vs 650 stated. I scaled money by 4.26 and show both; the scaled figure assumes the pattern holds at full volume.
- Repeat-contact rate depends on the tagger (same theme), so tagger errors flow into it; it moved from 8.9% to 10.3% as I fixed rules.
- Leaderboard doesn't adjust for priority or difficulty inside a team, and short tenure isn't handled.
- Savings are ceilings (assumes handover tickets can match same-shift performance).
- orders/customers/products CSVs were not used. [Say so if you did have them and didn't load them.]

**6. What did you deliberately leave out, and why that rather than something else?**
A dashboard/UI, auth, real-time updates (Priya said she doesn't need a platform); LLM tagging (Finance doesn't want a per-ticket bill and rules hit 90%); lot-code and replacement-cost analysis (needs orders/products); a refund reason-code audit (I saw miscoding in a few notes but did not measure it); difficulty-adjusted agent scoring; forecasting. I chose these because none moves the number above.

**7. Anything you built or found that nobody asked for?**
Shift-handover finding (29.9% of tickets cross a shift boundary; 16.0% vs 5.8% breach; night agents look bad on breaches, 13% vs 5% on own-shift tickets). Test of Neha's hunch (6.2% of chat tickets open with "already told"; 53% real repeats; CSAT 2.67 vs 3.33). Four tickets with both refund and replacement (Rs 11,850). Transfers field under-records hand-offs (1,040 vs 1,448). Duplicate/timezone/CSAT repairs.

**8. What did you use AI for?**
[Edit to match what is true for you.] Claude (Anthropic chat, Sonnet 5.5) for reading the brief, exploring the data, writing all code and docs, and labelling the validation samples. Helped: found the duplicate and timezone problems and the handover pattern quickly; iterated the tagger. Wasted time: my first headline (28.5% repeat contacts, same customer + product) mixed different issues; then a bot-tag-based 12.1% figure; both thrown away for the theme-based 10.3%. Also threw away: the Rs 180 cost, a rule that let a customer's "I want a refund" override the real problem. Cost: [your plan/API cost, or Rs 0 if within a subscription]. Recording: [link].
Google Drive link: [link]

**9. Someone picks this up on Monday and you are unreachable: the three things they need to know.**
1. Run: `pip install -r requirements.txt`, put tickets.csv and agents.csv in data/, `python run.py --tickets data/tickets.csv --agents data/agents.csv`.
2. The headline (shift-handover breaches) is inferred from the resolver's shift and scaled x4.26 from the export to 650/week; get Neha to confirm the handover pattern and Sameer to confirm the true volume before quoting rupees.
3. The tagger is keyword rules: watch the "Unclear / other" share in each digest; when it climbs above ~5%, read those tickets and add phrases in vireo/themes.py.

**10. Honest hours spent.** [your number]

**11. GitHub repo link.** [your public repo URL]
