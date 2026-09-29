#!/usr/bin/env python3
"""Vireo support digest. Usage: python run.py --tickets tickets.csv --agents agents.csv [--week 2026-06-22] [--out out]"""
import argparse, json, os
import pandas as pd
from vireo.clean import load_tickets, CONTACT_COST, BREACH_CREDIT, TRANSFER_COST
from vireo.analysis import add_themes, add_repeats, repeat_cost, add_roster, add_shift, breach_summary, leaderboard, weekly_digest

def inr(x): return f"Rs {x:,.0f}"

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--tickets", required=True); ap.add_argument("--agents", required=True)
    ap.add_argument("--week", help="Monday of the week to report (default: last complete week)")
    ap.add_argument("--out", default="out")
    ap.add_argument("--weekly-volume", type=float, default=650, help="Vireo's stated tickets/week, used for scaling money")
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)

    t, dq = load_tickets(a.tickets)
    agents = pd.read_csv(a.agents, parse_dates=["from_date", "to_date"])
    t = add_themes(t); t = add_repeats(t); t = add_roster(t, agents); t = add_shift(t)
    t.drop(columns=["customer_message", "agent_notes"]).to_csv(f"{a.out}/tickets_enriched.csv", index=False)

    # ---- headline numbers ----
    rc = repeat_cost(t); nweeks = (t.created_at.max() - t.created_at.min()).days / 7
    exp_wk = len(t) / nweeks
    scale = a.weekly_volume / exp_wk
    per_repeat = rc["cost_inr"] / max(1, rc["repeat_tickets"])
    breaches = int(t.breach.sum())
    handoffs = int((t.agent_team != t.assigned_team).sum())
    head = {
        "tickets_after_dedupe": len(t), "weeks_covered": round(nweeks, 1), "export_tickets_per_week": round(exp_wk, 1),
        "stated_tickets_per_week": a.weekly_volume, "scale_factor": round(scale, 2),
        "repeat_rate_same_issue": round(rc["repeat_rate"], 4), "repeat_tickets": rc["repeat_tickets"],
        "repeat_cost_export_inr": round(rc["cost_inr"]), "avg_cost_per_repeat_inr": round(per_repeat),
        "repeat_cost_per_quarter_at_export_volume_inr": round(rc["cost_inr"] / (nweeks / 13)),
        "repeat_cost_per_quarter_at_650_per_week_inr": round(rc["cost_inr"] / (nweeks / 13) * scale),
        "breaches": breaches, "breach_rate": round(float(t.breach.mean()), 4), "breach_credit_export_inr": breaches * BREACH_CREDIT,
        "tickets_resolved_by_other_team": handoffs, "transfers_field_gt0": int((t.transfers > 0).sum()),
        "data_quality": dq,
    }
    bs = breach_summary(t); head["breach_handover"] = {k: round(v, 4) for k, v in bs.items()}
    q = nweeks / 13     # quarters covered by the export
    excess_q_650 = bs["excess_credit_inr"] / q * scale
    head["goal"] = (f"Cut first-response breaches from {t.breach.mean():.1%} to {bs['breach_rate_same_shift']:.1%} of tickets (the rate tickets already achieve when the same shift that received them "
                    f"answers them; tickets handed across a shift boundary breach at {bs['breach_rate_cross_shift']:.1%}). Worth about {inr(excess_q_650)} a quarter in SLA credits at {a.weekly_volume:.0f} tickets/week "
                    f"({inr(bs['excess_credit_inr'] / q)} at the export's own volume).")
    head["goal_quarterly_saving_inr_at_650"] = round(excess_q_650)
    head["repeat_contact_secondary"] = f"Repeat contacts cost {inr(rc['cost_inr'] / q * scale)} a quarter at {a.weekly_volume:.0f}/week; cutting them by a third saves about {inr(rc['cost_inr'] / q * scale / 3)}."
    json.dump(head, open(f"{a.out}/summary.json", "w"), indent=2, default=str)

    # ---- policy flags: refund AND replacement on one ticket (policy s.5 says escalate same day) ----
    both = t[t.refund_amount_inr.notna() & (t.replacement_issued == "Y")]
    both[["ticket_id", "created_at", "agent_id", "refund_amount_inr", "refund_reason_code", "replacement_issued"]].to_csv(f"{a.out}/policy_flags_refund_and_replacement.csv", index=False)
    head["refund_and_replacement_tickets"] = int(len(both)); head["refund_and_replacement_inr"] = float(both.refund_amount_inr.sum())
    json.dump(head, open(f"{a.out}/summary.json", "w"), indent=2, default=str)

    # ---- leaderboard ----
    lb = leaderboard(t); lb.round(3).to_csv(f"{a.out}/leaderboard.csv", index=False)

    # ---- weekly digest ----
    ws, cur, prev, tab = weekly_digest(t, a.week)
    L = [f"# Weekly complaint digest, week of {ws:%d %b %Y}", "",
         f"**{len(cur)} tickets** this week (prior 4-week average: {len(prev)/4:.0f}). "
         f"First-response breaches: {int(cur.breach.sum())} (= {inr(cur.breach.sum()*BREACH_CREDIT)} in auto credits), of which {int(cur[cur.cross_shift].breach.sum())} on tickets handed across a shift boundary. "
         f"Same-issue repeat contacts: {int(cur.is_repeat.sum())} ({cur.is_repeat.mean():.0%}). "
         f"Customers who open by saying they've already raised it: {int(cur.chase_msg.sum())} ({cur.chase_msg.mean():.0%}).", "",
         "## What people complained about", "", "| Theme | This week | 4-wk avg | Change |", "|---|---:|---:|---:|"]
    for th, r in tab.iterrows():
        L.append(f"| {th} | {int(r.this_week)} | {r.prior_4wk_avg:.1f} | {r.change:+.1f} |")
    L += ["", "## Products drawing the most tickets this week", ""]
    for sku, n in cur.product_sku.value_counts().head(5).items(): L.append(f"- {sku}: {n}")
    L += ["", "## Repeat contacts by theme (this week)", ""]
    for th, n in cur[cur.is_repeat].theme.value_counts().head(5).items(): L.append(f"- {th}: {n}")
    L += ["", "_Themes come from the customer's own words, not the intake bot's tag (the tag was wrong often enough that we don't trust it; see VALIDATION.md)._"]
    open(f"{a.out}/weekly_digest.md", "w").write("\n".join(L))

    # ---- leaderboard markdown ----
    T1 = lb[lb.tier == 1].sort_values(["agent_team", "rank_fair_in_team"])
    M = ["# Agent leaderboard (fairer version)", "",
         "Ranked **within team**, on tickets closed that **stayed closed** (customer did not come back on the same issue within 30 days). Raw 'tickets closed' is shown only so you can see how different the two lists are.", "",
         "| Team | Agent | Raw closed / wk | Stayed-closed / wk | Come-back rate | Breach rate, same-shift tickets | CSAT (n) | Rank in team |", "|---|---|---:|---:|---:|---:|---|---:|"]
    for _, r in T1.iterrows():
        M.append(f"| {r.agent_team} | {r['name']} | {r.closed_per_week:.1f} | {r.stayed_closed_per_week:.1f} | {r.came_back_rate:.0%} | {r.breach_rate_same_shift:.0%} | {r.csat:.2f} ({int(r.csat_n)}) | {int(r.rank_fair_in_team)} |")
    M += ["", "## Escalations & Warranty (Tier 2) is deliberately NOT ranked on volume (policy s.6, and Neha asked)", "",
          "| Agent | Closed | Median days to resolve | CSAT (n) | Come-back rate |", "|---|---:|---:|---|---:|"]
    for _, r in lb[lb.tier == 2].iterrows():
        M.append(f"| {r['name']} | {int(r.closed)} | {r.median_days:.1f} | {r.csat:.2f} ({int(r.csat_n)}) | {r.came_back_rate:.0%} |")
    open(f"{a.out}/leaderboard.md", "w").write("\n".join(M))

    print(open(f"{a.out}/weekly_digest.md").read()); print("\n" + head["goal"]); print(f"\nWrote {a.out}/ (weekly_digest.md, leaderboard.md, leaderboard.csv, summary.json, tickets_enriched.csv)")

if __name__ == "__main__":
    main()
