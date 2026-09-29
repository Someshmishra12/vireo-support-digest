"""Load and repair the export. Every fix here is documented in DECISIONS.md."""
import pandas as pd, numpy as np

SLA_MIN = {"chat": 15, "voice": 120, "social": 240, "email": 480}   # policy s.3
CONTACT_COST = {"chat": 210, "email": 260, "voice": 520, "social": 240}  # policy s.4
BREACH_CREDIT = 350            # policy s.3
TRANSFER_COST = 305            # policy s.4
IST_OFFSET_H = 5.5             # legacy resolved_at stored in UTC (policy s.9)

def load_tickets(path):
    t = pd.read_csv(path)
    for c in ["created_at", "first_response_at", "resolved_at"]:
        t[c] = pd.to_datetime(t[c])
    stats = {"rows_in": len(t)}
    # 1. Tickets re-imported from Freshdesk appear twice; keep the helpdesk copy (correct IST, real CSAT).
    dup = t.ticket_id.duplicated(keep=False)
    stats["duplicate_ticket_ids"] = int(t[dup].ticket_id.nunique())
    t = t.sort_values("source_system").drop_duplicates("ticket_id", keep="first")   # 'helpdesk' < 'legacy_fd'
    # 2. Legacy resolved_at is UTC; the rest of the file is IST.
    m = t.source_system == "legacy_fd"
    stats["legacy_resolved_before_created_raw"] = int((m & (t.resolved_at < t.created_at)).sum())
    t.loc[m, "resolved_at"] += pd.Timedelta(hours=IST_OFFSET_H)
    stats["resolved_before_created_after_fix"] = int((t.resolved_at < t.created_at).sum())
    # 3. Legacy CSAT uses 0 for "no response"; policy s.8: blank must be excluded, never averaged as 0.
    stats["legacy_csat_zero_to_blank"] = int((m & (t.csat_score == 0)).sum())
    t.loc[t.csat_score == 0, "csat_score"] = np.nan
    stats["rows_out"] = len(t)
    t["fr_min"] = (t.first_response_at - t.created_at).dt.total_seconds() / 60
    t["res_h"] = (t.resolved_at - t.created_at).dt.total_seconds() / 3600
    t["breach"] = t.fr_min > t.channel.map(SLA_MIN)
    t["week"] = t.created_at.dt.to_period("W").dt.start_time
    return t.sort_values("created_at").reset_index(drop=True), stats
