import pandas as pd, numpy as np
from .clean import CONTACT_COST, BREACH_CREDIT, TRANSFER_COST
from .themes import tag, is_chase

def add_themes(t):
    t = t.copy()
    t["theme"] = t.customer_message.map(tag)
    t["chase_msg"] = t.customer_message.map(is_chase)
    return t

def add_repeats(t, keys=("customer_id", "product_sku", "theme"), window_days=30):
    """Flag follow-up contacts: same customer + product + issue-theme, opened 0-30 days after the
    previous ticket was resolved (policy s.10). Also flags the *original* ticket as 'came_back'."""
    t = t.copy()
    keys = list(keys)
    end = t.resolved_at.fillna(t.created_at)
    s = t.assign(_end=end).sort_values(keys + ["created_at"])
    g = s.groupby(keys)
    gap_prev = (s.created_at - g["_end"].shift(1)).dt.total_seconds() / 86400
    gap_next = (g["created_at"].shift(-1) - s["_end"]).dt.total_seconds() / 86400
    t.loc[s.index, "is_repeat"] = gap_prev.between(0, window_days)
    t.loc[s.index, "came_back"] = gap_next.between(0, window_days)
    t["is_repeat"] = t.is_repeat.astype(bool); t["came_back"] = t.came_back.astype(bool)
    return t

def repeat_cost(t):
    r = t[t.is_repeat]
    return {"repeat_tickets": int(len(r)), "repeat_rate": float(t.is_repeat.mean()),
            "cost_inr": float(r.channel.map(CONTACT_COST).sum())}

def add_shift(t):
    """Shift in which the ticket was created (IST, policy s.7) vs the resolving agent's shift."""
    t = t.copy(); h = t.created_at.dt.hour
    t["created_shift"] = np.select([(h >= 6) & (h < 14), (h >= 14) & (h < 22)], ["Morning", "Day"], "Night")
    t["cross_shift"] = t.created_shift != t["shift"]
    return t

def breach_summary(t):
    """Breach rate when created and resolved in different shifts vs the same shift; excess breaches priced at the Rs 350 credit."""
    ex = 0.0
    for _, d in t.groupby("channel"):
        c = d[d.cross_shift]; ex += c.breach.sum() - len(c) * d[~d.cross_shift].breach.mean()
    return {"breach_rate_cross_shift": float(t[t.cross_shift].breach.mean()), "breach_rate_same_shift": float(t[~t.cross_shift].breach.mean()),
            "cross_shift_share": float(t.cross_shift.mean()), "excess_breaches": float(ex), "excess_credit_inr": float(ex * BREACH_CREDIT),
            "median_first_response_min_cross": float(t[t.cross_shift].fr_min.median()), "median_first_response_min_same": float(t[~t.cross_shift].fr_min.median())}

def add_roster(t, agents):
    a = agents.sort_values("from_date").drop_duplicates("agent_id", keep="last")   # latest assignment
    return t.merge(a[["agent_id", "name", "team", "shift", "tier"]].rename(columns={"team": "agent_team"}),
                   on="agent_id", how="left")

def leaderboard(t, cutoff_days=30):
    """Fairer than 'tickets closed': closed AND stayed closed, ranked within team, Tier 2 shown on days not volume."""
    last = t.created_at.max()
    att = t[t.status.isin(["resolved", "closed"])].copy()
    weeks = max(1, (t.created_at.max() - t.created_at.min()).days / 7)
    matured = att[att.resolved_at <= last - pd.Timedelta(days=cutoff_days)]   # only judge tickets old enough to have come back
    g = att.groupby(["agent_id", "name", "agent_team", "tier", "shift"])
    out = g.agg(closed=("ticket_id", "count"), csat=("csat_score", "mean"), csat_n=("csat_score", "count"),
                median_days=("res_h", lambda x: x.median() / 24), breach_rate=("breach", "mean")).reset_index()
    out = out.merge(att[~att.cross_shift].groupby("agent_id").breach.mean().rename("breach_rate_same_shift"), on="agent_id", how="left")
    sc = matured.groupby("agent_id").came_back.mean().rename("came_back_rate")
    out = out.merge(sc, on="agent_id", how="left")
    out["closed_per_week"] = out.closed / weeks
    out["stayed_closed_per_week"] = out.closed_per_week * (1 - out.came_back_rate)
    out["team_median_stayed"] = out.groupby("agent_team").stayed_closed_per_week.transform("median")
    out["vs_team_median"] = out.stayed_closed_per_week / out.team_median_stayed - 1
    out["rank_raw"] = out.closed.rank(ascending=False, method="min").astype(int)
    tier1 = out.tier == 1
    out.loc[tier1, "rank_fair_in_team"] = out[tier1].groupby("agent_team").stayed_closed_per_week.rank(ascending=False, method="min")
    return out.sort_values("closed", ascending=False)

def weekly_digest(t, week_start=None, trailing=4):
    weeks = sorted(t.week.unique())
    complete = [w for w in weeks if (t.created_at.max() - w).days >= 6]
    ws = pd.Timestamp(week_start) if week_start else complete[-1]
    cur = t[t.week == ws]
    prev = t[(t.week < ws) & (t.week >= ws - pd.Timedelta(weeks=trailing))]
    def share(d): return d.theme.value_counts()
    a, b = share(cur), share(prev) / trailing
    tab = pd.DataFrame({"this_week": a, "prior_4wk_avg": b}).fillna(0)
    tab["change"] = tab.this_week - tab.prior_4wk_avg
    tab["pct_of_week"] = tab.this_week / max(1, len(cur))
    return ws, cur, prev, tab.sort_values("this_week", ascending=False)
