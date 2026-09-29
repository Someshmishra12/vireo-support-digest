# How do we know the theme tagger works, and how often is it wrong

The money figures depend on the tagger (repeat contacts use its theme), so this is the part that needed checking.

**Method.** Three random samples of tickets, drawn without replacement. For each I read the customer's message and marked the predicted theme right or wrong. **The labels were made by an AI assistant (Claude), not by a Vireo agent or by me alone; a human should spot-check `validation/labeled_samples.csv`.** Labels are in that file.

| Round | Code version | n | Correct | Note |
|---|---|---:|---:|---|
| 1 | first rules | 80 | 66 (82.5%) | used to find bugs |
| 2 | after fixes | 80 | 75 (93.8%) | used to find more bugs |
| **3** | **shipped code** | **60** | **54 (90.0%)** | **fresh sample, no changes after seeing it** |

Round 3 is the number to trust: **90%, 95% interval roughly 78-97% (n=60 is small)**. Rounds 1-2 were used to improve the rules, so they overstate accuracy.

**Where it is wrong (round 3, 6 errors):** typos inside multi-word phrases the fuzzy matcher cannot catch (3: "spininng circle", "repat myself", "geen light"), an OTP complaint phrased "sent me a code" (1), ambiguous dead-earbud messages that could be audio or charging (1), a snapped strap filed as damage instead of defect (1). Earlier rounds also showed a customer's *ask* ("I want a refund") overriding the real problem, and single keywords colliding ("pair" in "one pair of earbuds"). Those were fixed.

**Other checks.** 3.8% of tickets land in "Unclear / other" (down from 20% at the start). Bot tag vs text theme agree on ~83% of tickets the tagger could classify (lenient mapping; my own, so treat as rough). This is not accuracy of either one; it only shows the two disagree often enough that the bot tag can't be trusted for a digest.

**Caveats.** The messages look templated, so rules tuned here will do worse on real free text. Nothing measured for Hinglish beyond the phrases in this file.
