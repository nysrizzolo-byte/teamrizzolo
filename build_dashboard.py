#!/usr/bin/env python3
"""Rebuild the Team Rizzolo metrics dashboard (index.html) from data.json.

Splices every content pane, the nav labels, the sidebar/portal footers and the
Chart.js data arrays. The CSS, the password gate and the showPane() JS in
index.html are treated as an untouched template shell.

Usage:  python3 build_dashboard.py [data.json] [index.html]
"""
import json, re, sys, io

DATA = sys.argv[1] if len(sys.argv) > 1 else "data.json"
PAGE = sys.argv[2] if len(sys.argv) > 2 else "index.html"
d = json.load(open(DATA))
html = open(PAGE, encoding="utf-8").read()

M = d["months"]
def usd(n):
    return "$%.2fM" % (n / 1_000_000)
def usd1(n):
    return "$%.1fM" % (n / 1_000_000)
def cell(v):
    return "&mdash;" if not v else v
def vcell(v):
    return "&mdash;" if not v else "$%.1fM" % (v / 1_000_000)

# ---------------------------------------------------------------- OVERVIEW
def pane_overview():
    lc = d["lead_credit"]
    mx = max(x["ytd"] for x in lc)
    bars = "".join(
        f'<div class="bar-row"><div class="bar-name" style="color:{x["color"]}">{x["name"]}</div>'
        f'<div class="bar-n" style="color:{x["color"]}">{x["ytd"]}</div>'
        f'<div class="bar-track"><div class="bar-fill" style="width:{x["ytd"]/mx*100:.1f}%;background:{x["color"]}"></div></div>'
        f'<div class="bar-pct">{x["ytd"]/d["leads_ytd"]*100:.1f}%</div></div>' for x in lc)
    pos = "".join(f'<div class="insight-item"><span class="insight-icon">+</span>{t}</div>' for t in d["positives"])
    wat = "".join(f'<div class="insight-item"><span class="insight-icon">!</span>{t}</div>' for t in d["watching"])
    return f'''    <div class="pane active" id="pane-overview">
      <div class="page-header"><div class="page-eyebrow">2026 Year-to-Date</div><div class="page-title">Team Overview</div><div class="page-sub">{d["ytd_range"]} &middot; Leads credited per 203K-Way formula &middot; Fundings by closing date to L/O</div></div>
      <div class="kpi-grid">
        <div class="kpi"><div class="kpi-label">YTD Leads</div><div class="kpi-value" style="color:var(--blue)">{d["leads_ytd"]}</div><div class="kpi-sub">Jan&ndash;Aug</div></div>
        <div class="kpi"><div class="kpi-label">Active Pipeline</div><div class="kpi-value" style="color:var(--amber)">{d["pipeline_deals"]}</div><div class="kpi-sub">open deals</div></div>
        <div class="kpi"><div class="kpi-label">Closed / Funded</div><div class="kpi-value" style="color:var(--green)">{d["funded_ytd"]}</div><div class="kpi-sub">YTD loans</div></div>
        <div class="kpi"><div class="kpi-label">Funded Volume</div><div class="kpi-value" style="color:var(--purple)">{usd1(d["volume_ytd"])}</div><div class="kpi-sub">YTD</div></div>
        <div class="kpi"><div class="kpi-label">Pull-Through</div><div class="kpi-value" style="color:var(--teal)">{d["pull_through"]}</div><div class="kpi-sub">{d["funded_ytd"]} / {d["leads_ytd"]} leads</div></div>
      </div>
      <div class="note-strip good"><strong>{d["pipeline_note"]}</strong></div>
      <div class="note-strip"><strong>Credit rule:</strong> {d["credit_note"]}</div>
      <div class="section"><div class="section-title">Monthly Team Lead Intake</div><div class="chart-card"><div style="position:relative;width:100%;height:200px"><canvas id="teamChart"></canvas></div><div class="chart-note">Jan&ndash;Aug 2026 &middot; complete months</div></div></div>
      <div class="section"><div class="section-title">YTD Leads by Credit</div>{bars}</div>
      <div class="section"><div class="section-title">Insights &middot; {d["pull_date"]}</div>
        <div class="insight-grid">
          <div class="insight-card" style="border-color:rgba(0,200,117,.3)"><div class="insight-header" style="color:var(--green)">Positives</div>
            {pos}
          </div>
          <div class="insight-card" style="border-color:rgba(255,100,46,.3)"><div class="insight-header" style="color:var(--orange)">Worth Watching</div>
            {wat}
          </div>
        </div>
      </div>
    </div>
'''

# ---------------------------------------------------------------- BY LO
def pane_bylo():
    th = "".join(f"<th>{m}</th>" for m in M)
    rows = "".join(
        f'<tr><td style="color:{x["color"]}">{x["name"]}</td>'
        + "".join(f"<td>{cell(v)}</td>" for v in x["m"])
        + f'<td class="td-bold">{x["ytd"]}</td></tr>' for x in d["lead_credit"])
    tot = "".join(f"<td>{v}</td>" for v in d["leads_by_month"])
    pipe = "".join(
        f'<tr><td style="color:{x["color"]}">{x["name"]}</td><td>{x["deals"]}</td>'
        f'<td class="td-bold">{usd(x["vol"])}</td></tr>' for x in d["pipeline_by_lo"])
    fu = "".join(
        f'<tr><td style="color:{x["color"]}">{x["name"]}</td>'
        + "".join(f"<td>{cell(v)}</td>" for v in x["m"])
        + f'<td class="td-bold">{x["total"]}</td></tr>' for x in d["funded_by_lo"])
    ftot = "".join(f"<td>{v}</td>" for v in d["funded_by_month"])
    return f'''    <div class="pane" id="pane-bylo">
      <div class="page-header"><div class="page-eyebrow">2026 Year-to-Date</div><div class="page-title">By Loan Officer</div><div class="page-sub">Lead credit, pipeline, and funded &middot; 203K-Way formula for leads</div></div>
      <div class="section"><div class="section-title">YTD Lead Credit by Month</div>
        <div class="tbl-wrap"><div class="tbl-scroll"><table>
          <thead><tr><th>Credited To</th>{th}<th>YTD</th></tr></thead>
          <tbody>{rows}<tr class="team-row"><td>Team Total</td>{tot}<td>{d["leads_ytd"]}</td></tr></tbody>
        </table></div></div>
        <p style="font-size:10px;color:var(--text3);margin-top:8px">203K Way leads credited by Junior: Elvis Regis &rarr; Elvis - 203K Way, Jesse Cone &rarr; Jesse - 203K Way, all others &rarr; Sal - 203K Way. Non-203K = creation-log creator; Alasia entries &rarr; L/O. Dates bucketed in America/New_York.</p>
      </div>
      <div class="section"><div class="section-title">Active Rolling Pipeline by LO (open deals)</div>
        <div class="tbl-wrap"><div class="tbl-scroll"><table><thead><tr><th>Loan Officer</th><th>Open Deals</th><th>Pipeline Volume</th></tr></thead>
          <tbody>{pipe}<tr class="team-row"><td>Team Total</td><td>{d["pipeline_deals"]}</td><td>{usd(d["pipeline_value"])}</td></tr></tbody></table></div></div>
        <p style="font-size:10px;color:var(--text3);margin-top:8px">Open deals attributed by L/O column. Excludes Closed/Funded, dead, and past funded months.</p>
      </div>
      <div class="section"><div class="section-title">Closed / Funded by LO (by closing date &middot; all 2026 fundings)</div>
        <div class="tbl-wrap"><div class="tbl-scroll"><table>
          <thead><tr><th>Loan Officer</th>{th}<th>Total</th></tr></thead>
          <tbody>{fu}<tr class="team-row"><td>Team Total</td>{ftot}<td>{d["funded_ytd"]}</td></tr></tbody></table></div></div>
        <p style="font-size:10px;color:var(--text3);margin-top:8px">Funded attributed by L/O column (deal owner), not the lead-credit formula. Counts every 2026 closing regardless of pipeline-entry date.</p>
      </div>
    </div>
'''

# ---------------------------------------------------------------- LEADS VS CONTRACT
def pane_lp():
    rows = "".join(
        f'<tr><td style="color:{x["color"]}">{x["name"]}</td><td>{x["leads"]}</td><td>{x["contract"]}</td>'
        f'<td>{x["funded"]}</td><td class="td-bold">{x["pct"]}</td>'
        f'<td style="text-align:left"><span class="badge {x["badge"]}">{x["status"]}</span></td></tr>'
        for x in d["pull_through_rows"])
    return f'''    <div class="pane" id="pane-lp">
      <div class="page-header"><div class="page-eyebrow">2026 Year-to-Date</div><div class="page-title">Leads vs In Contract</div><div class="page-sub">Pull-through rate</div></div>
      <div class="kpi-grid">
        <div class="kpi"><div class="kpi-label">YTD Leads</div><div class="kpi-value" style="color:var(--blue)">{d["leads_ytd"]}</div></div>
        <div class="kpi"><div class="kpi-label">In Contract</div><div class="kpi-value" style="color:var(--amber)">{d["pipeline_deals"]}</div></div>
        <div class="kpi"><div class="kpi-label">Funded</div><div class="kpi-value" style="color:var(--green)">{d["funded_ytd"]}</div></div>
        <div class="kpi"><div class="kpi-label">Pull-Through</div><div class="kpi-value" style="color:var(--teal)">{d["pull_through"]}</div></div>
      </div>
      <div class="section"><div class="section-title">Pull-Through by LO</div>
        <div class="tbl-wrap"><div class="tbl-scroll"><table>
          <thead><tr><th>Loan Officer</th><th>YTD Leads</th><th>In Contract</th><th>Funded '26</th><th>Pull-Through</th><th style="text-align:left">Status</th></tr></thead>
          <tbody>{rows}<tr class="team-row"><td>Team Total</td><td>{d["leads_ytd"]}</td><td>{d["pipeline_deals"]}</td><td>{d["funded_ytd"]}</td><td>{d["pull_through"]}</td><td style="text-align:left"></td></tr></tbody></table></div></div>
        <p style="font-size:10px;color:var(--text3);margin-top:8px">{d["pull_through_note"]}</p>
      </div>
      <div class="section"><div class="section-title">Monthly Leads vs Funded (Team)</div>
        <div class="chart-card"><div style="display:flex;gap:16px;margin-bottom:12px;font-size:12px;color:var(--text2)"><span style="display:flex;align-items:center;gap:5px"><span style="width:10px;height:10px;border-radius:2px;background:#579bfc;display:inline-block"></span>Leads</span><span style="display:flex;align-items:center;gap:5px"><span style="width:10px;height:10px;border-radius:2px;background:#cab641;display:inline-block"></span>Funded</span></div>
        <div style="position:relative;width:100%;height:200px"><canvas id="lpChart"></canvas></div></div></div>
    </div>
'''

# ---------------------------------------------------------------- VOLUME
def pane_vol():
    mv = d["volume_by_month"]; mx = max(mv)
    bars = "".join(
        f'<div class="vol-row"><div class="vol-lbl">{M[i]}</div><div class="vol-track">'
        f'<div class="vol-fill" style="width:{v/mx*100:.1f}%;background:var(--{"green" if v==mx else "purple" if i<3 else "blue"})"></div>'
        f'<span class="vol-txt" style="color:#fff">{usd(v)}</span></div></div>' for i, v in enumerate(mv))
    kp = "".join(
        f'<div class="kpi"><div class="kpi-label">{k["label"]}</div>'
        f'<div class="kpi-value" style="color:var({k["var"]})">{k["val"]}</div>'
        f'<div class="kpi-sub">{k["sub"]}</div></div>' for k in d["vol_kpis"])
    th = "".join(f"<th>{m}</th>" for m in M)
    rows = "".join(
        f'<tr><td style="color:{x["color"]}">{x["name"]}</td>'
        + "".join(f"<td>{vcell(v)}</td>" for v in x["v"])
        + f'<td class="td-bold">{usd(x["vtotal"])}</td><td>{x["total"]}</td></tr>' for x in d["funded_by_lo"])
    tot = "".join(f"<td>{usd1(v)}</td>" for v in mv)
    return f'''    <div class="pane" id="pane-vol">
      <div class="page-header"><div class="page-eyebrow">2026 Year-to-Date</div><div class="page-title">Loan Volume</div><div class="page-sub">All 2026 fundings by closing date, attributed to L/O column</div></div>
      <div class="kpi-grid">
        <div class="kpi"><div class="kpi-label">YTD Volume</div><div class="kpi-value" style="color:var(--purple)">{usd1(d["volume_ytd"])}</div></div>
        {kp}
        <div class="kpi"><div class="kpi-label">Avg / Loan</div><div class="kpi-value" style="color:var(--teal)">${d["avg_loan"]//1000}K</div></div>
      </div>
      <div class="section"><div class="section-title">Monthly Funded Volume (Team)</div><div class="chart-card">{bars}<div class="chart-note">August is the year's best month &mdash; 14 loans, $9.16M</div></div></div>
      <div class="section"><div class="section-title">Volume by Loan Officer</div>
        <div class="tbl-wrap"><div class="tbl-scroll"><table>
          <thead><tr><th>LO</th>{th}<th>YTD Total</th><th>Loans</th></tr></thead>
          <tbody>{rows}<tr class="team-row"><td>Team Total</td>{tot}<td>{usd(d["volume_ytd"])}</td><td>{d["funded_ytd"]}</td></tr></tbody></table></div></div>
        <p style="font-size:10px;color:var(--text3);margin-top:8px">Counts every loan closed in 2026 regardless of pipeline entry. Monthly cells rounded; totals exact.</p>
      </div>
    </div>
'''

# ---------------------------------------------------------------- WEEKLY
def pane_weekly():
    w = d["weekly"]; mx = max([b["n"] for b in w["buckets"]] + [1])
    bars = "".join(
        f'<div class="bar-row"><div class="bar-name" style="color:{b["color"]}">{b["name"]}</div>'
        f'<div class="bar-n" style="color:{b["color"]}">{b["n"]}</div>'
        f'<div class="bar-track"><div class="bar-fill" style="width:{b["n"]/mx*100:.1f}%;background:{b["color"]}"></div></div>'
        f'<div class="bar-pct">{b["n"]/max(w["leads"],1)*100:.0f}%</div></div>' for b in w["buckets"])
    rows = "".join(
        f'<tr><td style="text-align:left">{r["d"]}</td><td style="text-align:left">{r["name"]}</td>'
        f'<td style="text-align:left">{r["credit"]}</td></tr>' for r in w["detail"]) \
        or '<tr><td colspan="3" style="text-align:left;color:var(--text3)">No leads logged yet this week.</td></tr>'
    return f'''<div class="pane" id="pane-weekly">
      <div class="page-header">
        <div class="page-eyebrow">Current Period</div>
        <div class="page-title">Weekly Report</div>
        <div class="page-sub">{w["label"]}, 2026 &middot; this week so far &middot; refreshed daily</div>
      </div>
      <div class="kpi-grid">
        <div class="kpi"><div class="kpi-label">Week Leads</div><div class="kpi-value" style="color:var(--blue)">{w["leads"]}</div><div class="kpi-sub">{w["label"]}</div></div>
        <div class="kpi"><div class="kpi-label">Active Sources</div><div class="kpi-value" style="color:var(--green)">{w["active_sources"]}</div></div>
        <div class="kpi"><div class="kpi-label">Zero-Lead LOs</div><div class="kpi-value" style="color:var(--red)">{w["zero_count"]}</div><div class="kpi-sub">flagged</div></div>
      </div>
      <div class="section">
        <div class="section-title">Lead Intake &mdash; Credited To</div>
        {bars}
      </div>
      <div class="section">
        <div class="section-title">Lead Detail &mdash; {w["label"]}</div>
        <div class="tbl-wrap"><div class="tbl-scroll">
        <table>
          <thead><tr><th style="text-align:left">Date</th><th style="text-align:left">Lead Name</th><th style="text-align:left">Credited To</th></tr></thead>
          <tbody>
            {rows}
          </tbody>
        </table></div></div>
        <p style="font-size:10px;color:var(--text3);margin-top:8px">No leads this week from: {w["zero_names"]}.</p>
      </div>
    </div>
'''

# ---------------------------------------------------------------- MTD
def pane_mtd():
    m = d["mtd"]
    kp = "".join(
        f'<div class="kpi"><div class="kpi-label">{k["label"]}</div>'
        f'<div class="kpi-value" style="color:var({k["var"]})">{k["val"]}</div>'
        f'<div class="kpi-sub">{k["sub"]}</div></div>' for k in m["kpis"])
    prows = []
    for i, p in enumerate(m["pace"]):
        hi = ';color:var(--amber)' if i == 0 else ''
        bold = ' class="td-bold"' if p["hl"] else ''
        prows.append(
            '<tr><td style="text-align:left%s">%s</td><td>%s</td><td>%s</td><td%s>%s</td>'
            '<td style="text-align:left;font-size:11px;color:var(--text3)">%s</td></tr>'
            % (hi, p["m"], p["leads"], p["days"], bold, p["per"], p["ctx"]))
    pace = "".join(prows)
    return f'''    <div class="pane" id="pane-mtd">
      <div class="page-header"><div class="page-eyebrow">Current Period</div><div class="page-title">{m["title"]}</div><div class="page-sub">{m["sub"]}</div></div>
      <div class="kpi-grid">
        {kp}
      </div>
      <div class="note-strip">{m["note"]}</div>
      <div class="section"><div class="section-title">Daily Lead Intake &mdash; September 2026</div><div class="chart-card"><div class="daily-wrap" id="dailyChart"></div><div class="chart-note">Sep 1&ndash;{m["days_in_month"]} &middot; each bar = 1 day</div></div></div>
      <div class="section"><div class="section-title">Pace vs Prior Months</div>
        <div class="tbl-wrap"><div class="tbl-scroll"><table>
          <thead><tr><th style="text-align:left">Month</th><th>Leads</th><th>Days</th><th>Per Day</th><th style="text-align:left">Context</th></tr></thead>
          <tbody>
            {pace}
          </tbody></table></div></div>
      </div>
    </div>
'''

# ---------------------------------------------------------------- SPLICE
starts = ['<div class="pane active" id="pane-overview">', '<div class="pane" id="pane-bylo">',
          '<div class="pane" id="pane-lp">', '<div class="pane" id="pane-vol">',
          '<div class="pane" id="pane-weekly">', '<div class="pane" id="pane-mtd">',
          '<div class="portal-footer">']
idx = []
for s in starts:
    i = html.find(s)
    if i < 0:
        sys.exit("FATAL: marker not found: " + s)
    idx.append(html.rfind("\n", 0, i) + 1)
if idx != sorted(idx):
    sys.exit("FATAL: panes out of expected order")

body = pane_overview() + "\n" + pane_bylo() + "\n" + pane_lp() + "\n" + pane_vol() + "\n" \
     + pane_weekly() + "\n" + pane_mtd() + "\n"
html = html[:idx[0]] + body + html[idx[6]:]

# nav labels
html = re.sub(r"(showPane\('weekly',this\)\"[^>]*><span[^>]*></span>)Weekly \([^)]*\)",
              r"\1Weekly (" + d["weekly"]["label"] + ")", html)
html = re.sub(r"(showPane\('mtd',this\)\"[^>]*><span[^>]*></span>)MTD \([^)]*\)",
              r"\1MTD (September 2026)", html)

# sidebar footer
html = re.sub(r'<div class="run-date">.*?</div>',
              f'<div class="run-date">Last data pull<br><strong style="color:#aaa">{d["pull_date"]}</strong>'
              f'<br><br>{d["leads_ytd"]} leads &middot; {d["funded_ytd"]} funded<br>{usd(d["volume_ytd"])} volume</div>',
              html, flags=re.S)

# portal footer
html = re.sub(r'<div class="portal-footer">.*?</div>',
              f'<div class="portal-footer">Team Rizzolo &middot; NAF &middot; Data pulled {d["pull_date"]}<br>'
              f'Leads credited per 203K-Way formula &middot; {d["leads_ytd"]} leads &middot; {d["funded_ytd"]} funded &middot; '
              f'{usd(d["volume_ytd"])} &middot; Active Rolling Pipeline {usd(d["pipeline_value"])} / {d["pipeline_deals"]} open<br><br>'
              f'Generated by build_dashboard.py from data.json.</div>', html, flags=re.S)

# chart data
labels = json.dumps(M)
html = re.sub(r"(new Chart\(document\.getElementById\('teamChart'\).*?labels:)\[[^\]]*\](,datasets:\[\{data:)\[[^\]]*\]",
              lambda m: m.group(1) + labels + m.group(2) + json.dumps(d["leads_by_month"]), html, flags=re.S)
html = re.sub(r"(backgroundColor:\[)[^\]]*(\],borderRadius:5)",
              lambda m: m.group(1) + ",".join(["'#579bfc'"] * (len(M) - 1) + ["'#00c875'"]) + m.group(2), html)
html = re.sub(r"(getElementById\('lpChart'\).*?labels:)\[[^\]]*\](.*?label:'Leads',data:)\[[^\]]*\](.*?label:'Funded',data:)\[[^\]]*\]",
              lambda m: m.group(1) + labels + m.group(2) + json.dumps(d["leads_by_month"])
                      + m.group(3) + json.dumps(d["funded_by_month"]), html, flags=re.S)
daily = [{"d": str(i + 1), "n": (d["mtd"]["daily"][i] if i < len(d["mtd"]["daily"]) else 0)}
         for i in range(d["mtd"]["days_in_month"])]
html = re.sub(r"const daily=\[.*?\];", "const daily=" + json.dumps(daily) + ";", html, flags=re.S)

open(PAGE, "w", encoding="utf-8").write(html)
print("Wrote %s (%d bytes)" % (PAGE, len(html)))
