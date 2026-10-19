#!/usr/bin/env python3
"""Compute the LO Scorecard block (data.json key `lo_scorecard`) from two saved monday pulls.

Per LO, per month (by lead creation date, America/New_York):
  leads  - leads taken in that month (Lead Board + leads moved to the Master Pipeline)
  pa     - of those leads, how many are pre-approved TODAY (cohort view: a September lead
           approved in October still counts in September)
  units / vol - loans closed that month as LO (CLOSED / FUNDED, bucketed by closing date)

Credit rules (Sal, 2026-10-18):
  * Leads use the normal lead-credit chain (Richard dropped, 203K Way -> Matt + Junior,
    Alasia -> Sal, else creator). Matt + Junior buckets credit Matt; `Matt + James` also
    credits James.
  * Matt additionally gets every lead and every closing he is listed on in ANY people column
    (L/O, Junior, Biz Dev), even as Biz Dev.
  * Closings: everyone else by the LO column (deal_owner); a deal Matt shares counts for both.
  * Pre-approved: Lead Board Process Stage = "Pre Approved", or Status = Shopping / Accepted
    Offer / In Contract / CLOSED / FUNDED. Every lead that moved to the Master Pipeline counts
    as pre-approved (it reached an accepted offer).

Usage: python3 lo_scorecard.py <lead_board.json> <pipeline.json> <YYYY-MM-DD today> [data.json]
  lead_board.json: boards(ids: 6229246811) items_page(limit 500) with column_values for
    board_relation_mkw34hbe, multiple_person_mky6cr94, people_1, multiple_person_mky660ch,
    status_19, lead_status
  pipeline.json: boards(ids: 6229246816) groups { title items_page { items { name created_at
    creator column_values { id text ... on BoardRelationValue { display_value } } } } }
"""
import json, sys, collections, datetime as dt
from zoneinfo import ZoneInfo

ET = ZoneInfo("America/New_York")
LB_FILE, PL_FILE, TODAY = sys.argv[1], sys.argv[2], dt.date.fromisoformat(sys.argv[3])
DATA = sys.argv[4] if len(sys.argv) > 4 else "data.json"
YEAR, NM = TODAY.year, TODAY.month
MATT = "Matthew Porcaro"
LOS = [("Sal Rizzolo", "#579bfc"), (MATT, "#7b6bd6"), ("Felix Diaz", "#00c875"),
       ("Theresa Feehan", "#66ccff"), ("James Codomo", "#c4a35a"), ("Yhma Karimy", "#1D9E75")]
FULL = ["JANUARY", "FEBRUARY", "MARCH", "APRIL", "MAY", "JUNE", "JULY", "AUGUST",
        "SEPTEMBER", "OCTOBER", "NOVEMBER", "DECEMBER"]
JR = {"Elvis Regis": "Matt + Elvis", "Jesse Cone": "Matt + Jesse", "James Codomo": "Matt + James"}
PA_STAGE = {"Pre Approved"}
PA_STATUS = {"Shopping", "Accepted Offer", "In Contract", "CLOSED / FUNDED"}

def etd(s):
    return dt.datetime.fromisoformat(s.replace("Z", "+00:00")).astimezone(ET).date()
def col(i, cid):
    return next((c for c in i["column_values"] if c["id"] == cid), {}) or {}
def txt(i, cid):
    return col(i, cid).get("text") or ""
def people(s):
    return [p.strip() for p in (s or "").split(",") if p.strip()]

def credit(creator, ref, junior):
    """Normal lead-credit chain -> bucket name, or None (dropped)."""
    if "203K Way" in (ref or ""):
        j = [p for p in people(junior) if p != "Alasia Olivares"]
        if j and j[0] in JR:
            return JR[j[0]]
        if j and j[0] not in ("Sal Rizzolo", "Richard Luxmore", MATT):
            return "Matt + " + j[0].split()[0]
        return "Matt - 203K Way"
    if creator == "Richard Luxmore":
        return None
    if creator == "Alasia Olivares":
        return "Sal Rizzolo"
    if creator == "Lead Intake":
        return "Lead Intake (form)"
    return creator

def lead_los(bucket, listed):
    """LOs credited for one lead: bucket owner(s) + Matt if listed anywhere."""
    out = set()
    if bucket.startswith("Matt ") or bucket == MATT:
        out.add(MATT)
        if bucket == "Matt + James":
            out.add("James Codomo")
    else:
        out.add(bucket)
    if MATT in listed:
        out.add(MATT)
    return out

lb = json.load(open(LB_FILE))["boards"][0]["items_page"]["items"]
groups = json.load(open(PL_FILE))["boards"][0]["groups"]
if min(etd(i["created_at"]) for i in lb) >= dt.date(YEAR, 1, 1):
    sys.exit("FATAL: Lead Board pull does not reach back before Jan 1")

leads = []  # (month index, set(LOs), pre_approved)
seen = set()
for i in lb:
    d = etd(i["created_at"])
    if d.year != YEAR:
        continue
    ref = col(i, "board_relation_mkw34hbe").get("display_value") or ""
    b = credit((i.get("creator") or {}).get("name"), ref, txt(i, "people_1"))
    if b is None:
        continue
    listed = set(people(txt(i, "multiple_person_mky6cr94")) + people(txt(i, "people_1"))
                 + people(txt(i, "multiple_person_mky660ch")) + [(i.get("creator") or {}).get("name")])
    pa = txt(i, "status_19") in PA_STAGE or txt(i, "lead_status") in PA_STATUS
    leads.append((d.month - 1, lead_los(b, listed), pa))
    seen.add((i["name"].strip().lower(), d))

units = collections.defaultdict(lambda: [0] * NM)
vol = collections.defaultdict(lambda: [0.0] * NM)
for g in groups:
    for i in g["items_page"]["items"]:
        d = etd(i["created_at"])
        owners = people(txt(i, "deal_owner"))
        listed = set(owners + people(txt(i, "multiple_person_mky8z4g3")) + people(txt(i, "multiple_person_mm4mbf80"))
                     + [(i.get("creator") or {}).get("name")])
        # leads moved to the pipeline
        if d.year == YEAR and (i["name"].strip().lower(), d) not in seen:
            ref = col(i, "deal_contact").get("display_value") or ""
            b = credit((i.get("creator") or {}).get("name"), ref, txt(i, "multiple_person_mm4mbf80"))
            if b is not None:
                leads.append((d.month - 1, lead_los(b, listed), True))
        # closings
        w = g["title"].split()
        if (len(w) == 2 and w[1] == str(YEAR) and w[0] in FULL[:NM]
                and txt(i, "deal_stage") == "CLOSED / FUNDED"):
            m = int(txt(i, "date")[5:7]) - 1
            try:
                v = float(txt(i, "deal_actual_value"))
            except ValueError:
                v = 0.0
            cred = set(owners)
            if MATT in listed:
                cred.add(MATT)
            for lo in cred:
                units[lo][m] += 1
                vol[lo][m] += v

rows = []
for name, color in LOS:
    L, P = [0] * NM, [0] * NM
    for m, los, pa in leads:
        if name in los:
            L[m] += 1
            P[m] += pa
    rows.append(dict(name=name, color=color, leads=L, pa=P, units=units[name],
                     vol=[int(round(x)) for x in vol[name]]))
for r in rows:
    print("%-16s leads %4d  PA %3d  closed %3d  $%s" % (r["name"], sum(r["leads"]), sum(r["pa"]),
          sum(r["units"]), f"{sum(r['vol']):,}"))

d = json.load(open(DATA))
d["lo_scorecard"] = dict(rows=rows, note=(
    "Leads = leads taken in that month by creation date (Lead Board + leads moved to the Master Pipeline), "
    "credited per the lead-credit formula. Pre-Approved = of that month's leads, how many are pre-approved now "
    "(Process Stage &ldquo;Pre Approved&rdquo; or Status Shopping / Accepted Offer / In Contract / Funded; every lead "
    "that reached the Master Pipeline counts) &mdash; so a lead approved after its month still counts in its intake "
    "month. Closed = loans funded that month by closing date, credited to the LO column. Matt is credited on every lead "
    "and closing he is listed on in any role (LO, Junior, Biz Dev), so person rows do not sum to team totals."))
json.dump(d, open(DATA, "w"), indent=1, ensure_ascii=False)
