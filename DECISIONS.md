# Decisions and assumptions (things the brief left open)

**Data repairs**
1. 653 ticket ids appear under both `helpdesk` and `legacy_fd`. Kept the helpdesk copy: identical except the legacy copy has UTC `resolved_at` and different CSAT. Rows 12,528 -> 11,875.
2. Legacy-only tickets: `resolved_at` shifted +5.5h (policy s.9). Verified on the 618 duplicate pairs where both copies had a value: the gap is exactly 5.5h every time. Before the fix 1,874 legacy tickets resolved before they were created; after, zero.
3. CSAT 0 on legacy rows means "no response" (README); set to blank so it is never averaged as a score.
4. Refund amounts: legacy and helpdesk values were identical on duplicate pairs and matched the amounts in agent notes, so I did not rescale them.

**Definitions**
5. Cost per contact: policy s.4 channel figures (chat 210, email 260, voice 520, social 240), not Arjun's Rs 180 (no source) and not the flat Rs 290 blend. Repeats skew to chat/email, so they average Rs 255.
6. Repeat contact: same customer + same product + same *issue theme* (from the message text), opened 0-30 days after the earlier ticket was resolved (policy s.10 says "same issue"). Same customer + same product alone gives 28% but mixes different problems, so I did not use it.
7. Breach: first response later than policy s.3 target. Auto credit Rs 350.
8. Shift handover: ticket created in one IST shift (Morning 06-14, Day 14-22, Night 22-06), resolved by an agent rostered on a different shift. **The first responder is not in the data, so the resolver's shift is a proxy.**
9. Volume: the export averages ~152 tickets/week; the brief says ~650. I could not tell whether the export is a sample or the brief is off. Every rupee figure is shown at both scales; the headline uses 650 (x4.26) because that is what Vireo told us.

**Client ask changed**
10. Leaderboard kept (Priya said it stays) but ranked within team, on tickets that stayed closed, because 54% of the spread in raw counts is team membership. Tier 2 not ranked on volume (policy s.6; Neha asked).
11. Digest themes come from customer text, not the bot tag: the bot tag disagreed with the text theme on about 17% of tickets (using a lenient theme-to-category mapping I wrote), and a further 14% are tagged "Other", a bucket that hides real issues such as warranty claims and double charges.

**Not used**
12. `orders.csv`, `customers.csv`, `products.csv` were not available to me, so no lot-code analysis and no replacement costing.
