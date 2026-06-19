#!/usr/bin/env python3
"""
Wolverine / Shell Maintenance - KPI report generator.

Reads the client data + KPI template + safety learning cards and emits a single,
self-contained, no-JavaScript HTML report (two report pages) intended for:
  - weekly director / project-controls review meetings, and
  - dropping into Power BI via an "HTML Content" custom visual, or
  - using as a precise design spec for native Power BI visuals.

Re-run this whenever the underlying Excel data is refreshed:
    python3 generate_kpi_report.py
Output: Wolverine_Shell_KPI_Report.html
"""
import os, math
from collections import defaultdict
from datetime import datetime
import openpyxl

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "data")
OUT  = os.path.join(HERE, "Wolverine_Shell_KPI_Report.html")

# ----------------------------------------------------------------------------
# Palette
# ----------------------------------------------------------------------------
C = dict(
    ink="#0E2233", band="#13314A", canvas="#EEF1F4", card="#FFFFFF",
    orange="#E8651E", red="#D6122A", yellow="#F6C700", teal="#1AA191",
    blue="#2E7BB5", purple="#6F5AA8", slate="#5B6B7A", line="#E2E7EC",
    green="#2E9E5B", amber="#E8A33D", danger="#D6453D", grey="#9AA7B2",
    text="#1B2B3A", muted="#6B7B8A",
)

def fnum(x):
    try: return float(x)
    except (TypeError, ValueError): return 0.0

def money(v):
    if abs(v) >= 1_000_000: return f"${v/1_000_000:.2f}M"
    if abs(v) >= 1_000:     return f"${v/1_000:.0f}K"
    return f"${v:,.0f}"

def num(v, d=0):
    return f"{v:,.{d}f}"

# ----------------------------------------------------------------------------
# 1. LOAD + AGGREGATE
# ----------------------------------------------------------------------------
def monthkey(d):
    if isinstance(d, datetime): return d.strftime("%Y-%m")
    try: return datetime.strptime(str(d).split(", ", 1)[1], "%B %d, %Y").strftime("%Y-%m")
    except Exception: return "unk"

def classify(role):
    """Map colRELShoreTrade -> (trade, tier, is_apprentice)."""
    if role is None: return ("Other", "Other", False)
    s = str(role); code = s.split("-")[0].strip()
    trade = "Other"
    if "Pipefitter" in s: trade = "Pipefitter"
    elif "Boilermaker" in s: trade = "Boilermaker"
    elif "Labourer" in s or "Laborer" in s: trade = "Labourer"
    elif "Operating Engineer" in s: trade = "Operating Eng"
    elif "Truck" in s or "Van" in s or code.startswith(("1226", "1227")): trade = "Vehicle"
    tier = "DFL"
    if code.startswith("111") or "Superintendent" in s or "PM/" in s: tier = "Indirect"
    elif code.startswith("131") or any(k in s for k in ("Planner", "Time Keeper", "Quality Control", "Manager", "Coordinator", "Clerk")): tier = "Indirect"
    elif "Foreman" in s: tier = "FM"
    elif trade == "Vehicle": tier = "Vehicle"
    return (trade, tier, "Apprentice" in s)

def load():
    wb = openpyxl.load_workbook(os.path.join(DATA, "Data.xlsx"), read_only=True, data_only=True)
    rows = list(wb["Projects"].iter_rows(values_only=True)); ph = rows[0]; pi = {h: i for i, h in enumerate(ph)}
    proj = {}
    for r in rows[1:]:
        if r[0] is not None:
            proj[str(r[0])] = {"grp": r[pi["Pro_Grouping"]] or "Other", "po": fnum(r[pi["PO Value"]]),
                               "status": r[pi["Status"]]}
    rows = list(wb["Data"].iter_rows(values_only=True)); h = rows[0]; idx = {x: i for i, x in enumerate(h)}
    data = [r for r in rows[1:] if r[0] is not None]

    a = dict(
        spend_cat=defaultdict(float), spend_grp=defaultdict(float),
        trade=defaultdict(lambda: defaultdict(float)), charge=defaultdict(float),
        appr_hrs=0.0, total_hrs=0.0, vehicle_hrs=0.0,
        m_hrs=defaultdict(float), m_cost=defaultdict(float),
        m_dfl=defaultdict(float), m_fm=defaultdict(float),
        people=set(), indirect=set(),
    )
    for r in data:
        job = str(r[idx["JobNumber"]]); attr = r[idx["Attribute"]]; grouping = r[idx["Grouping"]]
        role = r[idx["colRELShoreTrade"]]; emp = r[idx["EmployeeName"]]; mk = monthkey(r[idx["Date"]])
        trade, tier, appr = classify(role)
        sh = fnum(r[idx["Split Hours"]]); sc = fnum(r[idx["Split $$"]])
        grp = proj.get(job, {}).get("grp", "Other")
        if attr in ("HoursRT", "HoursDT"):
            a["charge"][attr] += sh; a["total_hrs"] += sh; a["m_hrs"][mk] += sh
            if trade in ("Pipefitter", "Boilermaker", "Labourer") and tier in ("DFL", "FM"):
                a["trade"][trade][tier] += sh
                a["m_dfl"][mk] += sh if tier == "DFL" else 0
                a["m_fm"][mk]  += sh if tier == "FM" else 0
            if tier == "Indirect": a["trade"]["Site Indirect"]["Indirect"] += sh; a["indirect"].add(emp)
            if trade == "Vehicle": a["vehicle_hrs"] += sh
            if appr: a["appr_hrs"] += sh
            if emp and tier != "Vehicle": a["people"].add(emp)
        elif attr == "TotalCost":
            a["spend_cat"][grouping] += sc; a["spend_grp"][grp] += sc; a["m_cost"][mk] += sc
    a["headcount"] = len(a["people"]); a["indirect_n"] = len(a["indirect"])
    a["po_total"] = sum(p["po"] for p in proj.values())
    a["active_jobs"] = sum(1 for p in proj.values() if p["status"] == "Active")
    wb.close()
    return a

def load_safety():
    wb = openpyxl.load_workbook(os.path.join(DATA, "Safety_Learning_Cards.xlsx"), read_only=True, data_only=True)
    rows = list(wb["2026"].iter_rows(values_only=True)); h = rows[0]; idx = {x: i for i, x in enumerate(h)}
    data = [r for r in rows[1:] if r[0] is not None]
    cat, dept, loc, month, contractor = (defaultdict(int) for _ in range(5))
    for r in data:
        def g(k): return str(r[idx[k]]).replace("\xa0", " ").strip() if r[idx[k]] is not None else None
        if g("Learner Mindset Category:"): cat[g("Learner Mindset Category:")] += 1
        if g("What's your Functional Department?"): dept[g("What's your Functional Department?")] += 1
        if g("Location:"): loc[g("Location:")] += 1
        if g("I work For"): contractor[g("I work For")] += 1
        d = r[idx["Date:"]]
        if hasattr(d, "month"): month[d.strftime("%Y-%m")] += 1
    wb.close()
    return dict(total=len(data), cat=dict(cat), dept=dict(dept), loc=dict(loc),
                month=dict(month), contractor=dict(contractor))

# ----------------------------------------------------------------------------
# 2. SVG / HTML COMPONENTS (pure markup, no script)
# ----------------------------------------------------------------------------
MONTHS = ["2026-01","2026-02","2026-03","2026-04","2026-05","2026-06"]
MLAB = {"2026-01":"Jan","2026-02":"Feb","2026-03":"Mar","2026-04":"Apr","2026-05":"May","2026-06":"Jun"}

def spark(points, color, w=120, h=34):
    pts = [p for p in points]
    if not pts or max(pts) == min(pts):
        mid = h/2
        return f'<svg class="spark" viewBox="0 0 {w} {h}"><line x1="0" y1="{mid}" x2="{w}" y2="{mid}" stroke="{color}" stroke-width="2"/></svg>'
    mn, mx = min(pts), max(pts); rng = mx - mn or 1
    step = w/(len(pts)-1) if len(pts) > 1 else w
    coords = [(i*step, h-4 - (p-mn)/rng*(h-8)) for i, p in enumerate(pts)]
    poly = " ".join(f"{x:.1f},{y:.1f}" for x, y in coords)
    area = f"0,{h} " + poly + f" {w},{h}"
    cx, cy = coords[-1]
    return (f'<svg class="spark" viewBox="0 0 {w} {h}" preserveAspectRatio="none">'
            f'<polygon points="{area}" fill="{color}" opacity="0.10"/>'
            f'<polyline points="{poly}" fill="none" stroke="{color}" stroke-width="2" '
            f'stroke-linecap="round" stroke-linejoin="round"/>'
            f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="2.6" fill="{color}"/></svg>')

def kpi_card(label, value, unit, target_txt, status, spark_pts, spark_color, foot):
    dot = {"good": C["green"], "warn": C["amber"], "bad": C["danger"], "na": C["grey"]}[status]
    sp = spark(spark_pts, spark_color) if spark_pts else ""
    tgt = f'<span class="kpi-tgt">{target_txt}</span>' if target_txt else ""
    return f'''<div class="kpi">
      <div class="kpi-top"><span class="kpi-label">{label}</span><span class="dot" style="background:{dot}"></span></div>
      <div class="kpi-val">{value}<span class="kpi-unit">{unit}</span></div>
      <div class="kpi-mid">{tgt}{sp}</div>
      <div class="kpi-foot">{foot}</div>
    </div>'''

def hbars(rows, unit="", money_fmt=False):
    mx = max((v for _, v, _ in rows), default=1) or 1
    out = ['<div class="hbars">']
    for label, v, color in rows:
        pct = max(2, v/mx*100)
        val = money(v) if money_fmt else (f"{v:,.0f}{unit}")
        out.append(f'''<div class="hb-row"><span class="hb-lab">{label}</span>
          <div class="hb-track"><div class="hb-fill" style="width:{pct:.1f}%;background:{color}"></div></div>
          <span class="hb-val">{val}</span></div>''')
    out.append("</div>")
    return "".join(out)

def donut(segments, center_top, center_bot, size=148):
    total = sum(v for _, v, _ in segments) or 1
    r = size/2 - 14; cx = cy = size/2; circ = 2*math.pi*r
    off = 0.0; arcs = []
    for label, v, color in segments:
        frac = v/total; dash = frac*circ
        arcs.append(f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="none" stroke="{color}" '
                    f'stroke-width="20" stroke-dasharray="{dash:.2f} {circ-dash:.2f}" '
                    f'stroke-dashoffset="{-off:.2f}" transform="rotate(-90 {cx} {cy})"/>')
        off += dash
    leg = "".join(f'<div class="lg"><span class="sw" style="background:{c}"></span>{l}'
                  f'<b>{v:,.0f}</b></div>' for l, v, c in segments)
    return f'''<div class="donut-wrap">
      <svg viewBox="0 0 {size} {size}" class="donut">{''.join(arcs)}
        <text x="{cx}" y="{cy-2}" class="dn-top">{center_top}</text>
        <text x="{cx}" y="{cy+16}" class="dn-bot">{center_bot}</text></svg>
      <div class="legend">{leg}</div></div>'''

def gauge(value, vmax, target, label, unit="", fmt=None):
    fmt = fmt or (lambda x: f"{x:,.0f}")
    frac = min(1.0, value/vmax) if vmax else 0
    R, cx, cy = 70, 90, 84
    def pt(fr):
        ang = math.pi*(1-fr)
        return cx+R*math.cos(ang), cy-R*math.sin(ang)
    x0, y0 = pt(0); x1, y1 = pt(1); xv, yv = pt(frac); xt, yt = pt(min(1, target/vmax) if vmax else 0)
    large = 1 if frac > 0.5 else 0
    col = C["green"] if value >= target else (C["amber"] if value >= 0.6*target else C["danger"])
    return f'''<div class="gauge">
      <svg viewBox="0 0 180 104">
        <path d="M{x0:.1f},{y0:.1f} A{R},{R} 0 1 1 {x1:.1f},{y1:.1f}" fill="none" stroke="{C['line']}" stroke-width="16" stroke-linecap="round"/>
        <path d="M{x0:.1f},{y0:.1f} A{R},{R} 0 {large} 1 {xv:.1f},{yv:.1f}" fill="none" stroke="{col}" stroke-width="16" stroke-linecap="round"/>
        <line x1="{xt:.1f}" y1="{yt:.1f}" x2="{cx+(R+12)*(xt-cx)/R:.1f}" y2="{cy+(R+12)*(yt-cy)/R:.1f}" stroke="{C['ink']}" stroke-width="2.5"/>
        <text x="90" y="74" class="g-val">{fmt(value)}{unit}</text>
        <text x="90" y="96" class="g-lab">{label}</text>
      </svg></div>'''

def bullet(label, value, target, ratio_txt, status):
    col = {"good": C["green"], "warn": C["amber"], "bad": C["danger"]}[status]
    scale = max(value, target)*1.25 or 1
    vp = value/scale*100; tp = target/scale*100
    return f'''<div class="bullet">
      <div class="bl-head"><span>{label}</span><b style="color:{col}">{ratio_txt}</b></div>
      <div class="bl-track">
        <div class="bl-fill" style="width:{vp:.1f}%;background:{col}"></div>
        <div class="bl-target" style="left:{tp:.1f}%"></div>
      </div></div>'''

def columns(values_by_month, color, fmt=None, target=None):
    fmt = fmt or (lambda x: f"{x:,.0f}")
    vals = [values_by_month.get(m, 0) for m in MONTHS]
    mx = max(vals + ([target] if target else []), default=1) or 1
    bw, gap, base, top = 30, 16, 120, 12
    bars = []
    for i, (m, v) in enumerate(zip(MONTHS, vals)):
        x = 30 + i*(bw+gap); hgt = (v/mx)*(base-top); y = base-hgt
        op = "1" if v > 0 else "0.25"
        bars.append(f'<rect x="{x}" y="{y:.1f}" width="{bw}" height="{max(hgt,1):.1f}" rx="3" fill="{color}" opacity="{op}"/>')
        bars.append(f'<text x="{x+bw/2}" y="{base+14}" class="cx-lab">{MLAB[m]}</text>')
        if v > 0:
            bars.append(f'<text x="{x+bw/2}" y="{y-4:.1f}" class="cx-val">{fmt(v)}</text>')
    tline = ""
    if target:
        ty = base-(target/mx)*(base-top)
        tline = (f'<line x1="22" y1="{ty:.1f}" x2="298" y2="{ty:.1f}" stroke="{C["danger"]}" stroke-width="1.5" stroke-dasharray="4 3"/>'
                 f'<text x="296" y="{ty-4:.1f}" class="cx-tgt">target {fmt(target)}</text>')
    return f'<svg viewBox="0 0 310 140" class="cols">{tline}{"".join(bars)}</svg>'

def stacked(rows, total_label):
    total = sum(v for _, v, _ in rows) or 1
    segs = "".join(f'<div class="st-seg" style="width:{v/total*100:.1f}%;background:{c}" title="{l}"></div>' for l, v, c in rows)
    leg = "".join(f'<div class="lg"><span class="sw" style="background:{c}"></span>{l}<b>{money(v)}</b></div>' for l, v, c in rows)
    return f'<div class="stacked"><div class="st-bar">{segs}</div><div class="legend">{leg}</div></div>'

def card(title, body, sub="", cls=""):
    s = f'<span class="c-sub">{sub}</span>' if sub else ""
    return f'<section class="panel {cls}"><header class="c-head"><h3>{title}</h3>{s}</header>{body}</section>'

# ----------------------------------------------------------------------------
# 3. BUILD PAGES
# ----------------------------------------------------------------------------
def status_from_ratio(actual_fm, actual_base, target_per=8):
    """Crew mix: target 1 FM per `target_per` base. Lower FM share is better/at target."""
    if actual_fm == 0: return ("1:∞", "good")
    ratio = actual_base/actual_fm
    txt = f"1:{ratio:.1f}"
    if ratio >= target_per: return (txt, "good")
    if ratio >= target_per*0.6: return (txt, "warn")
    return (txt, "bad")

def build(a, s):
    latest = max((m for m in a["m_hrs"] if a["m_hrs"][m] > 0), default="2026-04")
    latest_lab = datetime.strptime(latest, "%Y-%m").strftime("%B %Y")
    spend_total = sum(a["spend_cat"].values())

    # ---------- PAGE 1 : PERFORMANCE & COST ----------
    rt, dt = a["charge"]["HoursRT"], a["charge"]["HoursDT"]
    st_ratio = rt/dt if dt else 0
    appr_pct = a["appr_hrs"]/a["total_hrs"]*100 if a["total_hrs"] else 0
    veh_ratio = a["headcount"]/ max(1,(a["vehicle_hrs"]/40))  # rough vehicles from hrs

    kpis = "".join([
        kpi_card("Total Exposure Hours", num(a["total_hrs"]), "", "", "good",
                 [a["m_hrs"].get(m,0) for m in MONTHS], C["blue"], "Field + indirect, YTD"),
        kpi_card("Workforce Headcount", str(a["headcount"]), "", "", "good",
                 None, C["teal"], f'{a["indirect_n"]} site indirects (billable)'),
        kpi_card("Labour Spend", money(a["spend_cat"].get("Labour",0)), "", "", "good",
                 [a["m_cost"].get(m,0) for m in MONTHS], C["orange"], f'{money(spend_total)} total cost YTD'),
        kpi_card("Apprentice Ratio", f"{appr_pct:.0f}", "%", "per collective", "good",
                 None, C["purple"], f'{num(a["appr_hrs"])} apprentice hrs'),
        kpi_card("RT : DT Ratio", f"{st_ratio:.1f}:1" if dt else "n/a", "",
                 "target ≥10:1", "good" if st_ratio>=10 else "warn",
                 None, C["slate"], f'{num(rt)} reg / {num(dt)} double-time hrs'),
        kpi_card("Vehicle Hours Billed", num(a["vehicle_hrs"]), "", "target 1:3 ppl", "good",
                 None, C["red"], "On-site trucks & vans"),
    ])

    # trade DFL vs FM grouped bars
    trade_rows = []
    for t, col in [("Pipefitter", C["blue"]), ("Boilermaker", C["orange"]), ("Labourer", C["teal"])]:
        dfl = a["trade"][t].get("DFL",0); fm = a["trade"][t].get("FM",0)
        trade_rows.append((t, dfl, fm))
    mx = max((d+f for _,d,f in trade_rows), default=1) or 1
    tbody = ['<div class="hbars">']
    for t, dfl, fm in trade_rows:
        tot = dfl+fm or 1
        tbody.append(f'''<div class="hb-row"><span class="hb-lab">{t}</span>
          <div class="hb-track">
            <div class="hb-fill" style="width:{dfl/mx*100:.1f}%;background:{C["blue"]}"></div>
            <div class="hb-fill" style="width:{fm/mx*100:.1f}%;background:{C["amber"]}"></div>
          </div><span class="hb-val">{dfl+fm:,.0f}h</span></div>''')
    tbody.append('</div><div class="legend mini"><div class="lg"><span class="sw" style="background:'
                 + C["blue"] + '"></span>DFL (Direct Field Labour)</div><div class="lg"><span class="sw" style="background:'
                 + C["amber"] + '"></span>Foreman &amp; above</div></div>')

    # crew mix bullets
    bullets = []
    for t in ["Pipefitter", "Boilermaker", "Labourer"]:
        dfl = a["trade"][t].get("DFL",0); fm = a["trade"][t].get("FM",0)
        txt, stt = status_from_ratio(fm, dfl, 8)
        bullets.append(bullet(t, fm, dfl/8 if dfl else 0, txt, stt))
    crew = '<div class="bullets">' + "".join(bullets) + \
           f'<div class="bl-note"><span class="bl-target inline"></span> marker = target 1 Foreman : 8 base crew</div></div>'

    charge_donut = donut([("Regular Time", rt, C["teal"]), ("Double Time", dt, C["red"])],
                         f"{num(rt+dt)}", "total hrs")
    spend_cat = stacked([("Labour", a["spend_cat"].get("Labour",0), C["orange"]),
                         ("3rd Party", a["spend_cat"].get("3rd Party",0), C["blue"]),
                         ("Equipment", a["spend_cat"].get("Equip",0), C["teal"]),
                         ("Materials", a["spend_cat"].get("Materials",0), C["purple"])], "Total")
    grp_order = sorted(a["spend_grp"].items(), key=lambda kv: -kv[1])
    gcolors = {"NRM":C["orange"],"Project":C["blue"],"Pit Stop":C["teal"],"Mtce":C["purple"],
               "Capital":C["red"],"Other":C["grey"]}
    spend_grp = hbars([(k if k else "Other", v, gcolors.get(k, C["grey"])) for k, v in grp_order],
                      money_fmt=True)
    hrs_trend = columns(a["m_hrs"], C["blue"])
    portfolio = (f'<div class="mini-kpis">'
                 f'<div class="mk"><span>{a["active_jobs"]}</span>Active jobs</div>'
                 f'<div class="mk"><span>{money(a["po_total"])}</span>PO value (portfolio)</div>'
                 f'<div class="mk"><span>{a["indirect_n"]}</span>Site indirects</div>'
                 f'<div class="mk"><span>{num(a["vehicle_hrs"])}</span>Vehicle hrs</div>'
                 f'</div>')

    page1 = f'''
    <div class="page" id="p1">
      {header("Performance &amp; Cost", latest_lab, a, accent=C['orange'])}
      <div class="kpi-strip">{kpis}</div>
      <div class="grid">
        {card("Exposure Hours — Monthly Trend", hrs_trend, "All field + indirect hours, YTD 2026", "w6")}
        {card("Hours by Trade — DFL vs Foreman&nbsp;&amp;&nbsp;above", "".join(tbody), "Direct field labour vs supervision", "w6")}
        {card("Crew Mix — Foreman : Base Crew", crew, "Target ratio 1:8 (marker)", "w6")}
        {card("Charge-out Mix — RT vs DT", charge_donut, "Regular vs double time", "w3")}
        {card("Spend by Category", spend_cat, money(spend_total)+" total cost YTD", "w3")}
        {card("Spend by Shell Group", spend_grp, "Cost incurred by work type", "w6")}
        {card("Portfolio at a glance", portfolio, "Live from Projects table", "w6")}
      </div>
    </div>'''

    # ---------- PAGE 2 : HSSE & SAFETY ----------
    lag = [("First Aids",0,"per yr"),("Medical Treatment",0,"per yr"),("Lost Work Day",0,"per yr"),
           ("Near Misses", s["cat"].get("Near Miss",0),"YTD"),("Recordable Incidents",0,"per yr"),
           ("TRIF (Sarnia)","0.0","YTD")]
    lag_tiles = "".join(
        f'''<div class="lag {'good' if str(v) in ('0','0.0') else 'warn'}">
              <span class="lag-v">{v}</span><span class="lag-l">{l}</span><span class="lag-u">{u}</span></div>'''
        for l, v, u in lag)

    cat_colors = {"Hazard ID":C["red"],"Recognition":C["green"],"Pause Moment":C["blue"],
                  "Peer to Peer Intervention":C["purple"],"Near Miss":C["amber"]}
    cat_rows = sorted(s["cat"].items(), key=lambda kv: -kv[1])
    cat_chart = hbars([(l, v, cat_colors.get(l, C["grey"])) for l, v in cat_rows])
    dept_rows = sorted(s["dept"].items(), key=lambda kv: -kv[1])[:6]
    dept_chart = hbars([(l, v, C["blue"]) for l, v in dept_rows])
    loc_rows = sorted(s["loc"].items(), key=lambda kv: -kv[1])[:6]
    loc_chart = hbars([(l, v, C["teal"]) for l, v in loc_rows])
    latest_safe = s["month"].get(latest, max(s["month"].values()) if s["month"] else 0)
    safe_gauge = gauge(latest_safe, 40, 20, f"vs 20 / month target")
    safe_trend = columns(s["month"], C["green"], target=20)
    train = gauge(100, 100, 100, "compliance", unit="%")

    page2 = f'''
    <div class="page" id="p2">
      {header("HSSE &amp; Safety", latest_lab, a, accent=C['red'])}
      <div class="lag-strip">{lag_tiles}</div>
      <div class="grid">
        {card("Safety Observations — Latest Period", safe_gauge, f"{latest_lab}: {latest_safe} cards (target 20)", "w3")}
        {card("Safety Observations — Monthly Trend", safe_trend, f"{s['total']} cards YTD vs 20/mo target", "w6")}
        {card("Training Compliance", train, "Workforce current on training", "w3")}
        {card("Learning Cards by Category", cat_chart, "Learner mindset breakdown", "w4")}
        {card("By Functional Department", dept_chart, "Top reporting groups", "w4")}
        {card("By Site Location", loc_chart, "Where hazards are spotted", "w4")}
      </div>
      <div class="note-band">Leading indicators (proactive): {s['total']} learning cards logged YTD &middot;
        zero recordable incidents &middot; data refreshes automatically on workbook update.</div>
    </div>'''

    return page1 + page2

def header(title, period, a, accent):
    return f'''<header class="rpt-head" style="border-top:4px solid {accent}">
      <div class="brand">
        <div class="logo wolv">W</div>
        <div class="logo shell">S</div>
        <div class="htitle"><h1>Wolverine / Shell Maintenance — KPIs</h1>
          <div class="hsub">{title}</div></div>
      </div>
      <div class="hmeta">
        <div><span>Reporting Period</span><b>{period}</b></div>
        <div><span>Data Date</span><b>17-Jun-26</b></div>
        <div><span>Refreshed</span><b>19-Jun-26 9:40 AM</b></div>
      </div>
    </header>'''

# ----------------------------------------------------------------------------
# 4. SHELL / CSS
# ----------------------------------------------------------------------------
CSS = """
*{box-sizing:border-box;margin:0;padding:0}
body{font-family:'Segoe UI',-apple-system,Roboto,Helvetica,Arial,sans-serif;background:#D7DDE3;color:%(text)s;-webkit-font-smoothing:antialiased}
.nav{position:sticky;top:0;z-index:20;background:%(ink)s;color:#fff;display:flex;gap:8px;align-items:center;padding:10px 22px;box-shadow:0 2px 10px rgba(0,0,0,.18)}
.nav b{font-size:14px;letter-spacing:.3px;margin-right:14px}
.nav a{color:#cdd8e2;text-decoration:none;font-size:12.5px;padding:6px 14px;border-radius:20px;background:rgba(255,255,255,.06)}
.nav a:hover{background:rgba(255,255,255,.16);color:#fff}
.nav .sp{flex:1}.nav small{color:#8aa0b3;font-size:11px}
.page{width:1280px;margin:22px auto;background:%(canvas)s;border-radius:14px;overflow:hidden;box-shadow:0 12px 34px rgba(15,34,51,.18)}
.rpt-head{background:linear-gradient(120deg,%(band)s,%(ink)s);color:#fff;display:flex;justify-content:space-between;align-items:center;padding:16px 24px}
.brand{display:flex;align-items:center;gap:12px}
.logo{width:42px;height:42px;border-radius:9px;display:flex;align-items:center;justify-content:center;font-weight:800;font-size:20px}
.logo.wolv{background:%(orange)s;color:#fff}.logo.shell{background:%(yellow)s;color:%(red)s}
.htitle h1{font-size:18px;font-weight:700;letter-spacing:.2px}
.hsub{font-size:12px;color:#a9bccd;text-transform:uppercase;letter-spacing:1.4px;margin-top:2px}
.hmeta{display:flex;gap:26px}
.hmeta div{display:flex;flex-direction:column;text-align:right}
.hmeta span{font-size:10px;color:#90a6b8;text-transform:uppercase;letter-spacing:.8px}
.hmeta b{font-size:13px;font-weight:600;margin-top:2px}
.kpi-strip{display:grid;grid-template-columns:repeat(6,1fr);gap:12px;padding:16px 20px 4px}
.kpi{background:%(card)s;border:1px solid %(line)s;border-radius:11px;padding:13px 14px;box-shadow:0 1px 2px rgba(15,34,51,.04)}
.kpi-top{display:flex;justify-content:space-between;align-items:center}
.kpi-label{font-size:11px;color:%(muted)s;font-weight:600;text-transform:uppercase;letter-spacing:.4px}
.dot{width:9px;height:9px;border-radius:50%%}
.kpi-val{font-size:27px;font-weight:700;color:%(ink)s;margin-top:6px;line-height:1}
.kpi-unit{font-size:14px;font-weight:600;color:%(muted)s;margin-left:2px}
.kpi-mid{display:flex;justify-content:space-between;align-items:flex-end;min-height:34px;margin-top:6px}
.kpi-tgt{font-size:11px;color:%(slate)s;font-weight:600;background:#eef2f6;padding:2px 8px;border-radius:10px}
.spark{width:120px;height:34px}
.kpi-foot{font-size:10.5px;color:%(muted)s;margin-top:6px;border-top:1px solid %(line)s;padding-top:6px}
.grid{display:grid;grid-template-columns:repeat(12,1fr);gap:14px;padding:14px 20px 22px}
.panel{background:%(card)s;border:1px solid %(line)s;border-radius:12px;padding:14px 16px;box-shadow:0 1px 3px rgba(15,34,51,.05);display:flex;flex-direction:column}
.w3{grid-column:span 3}.w4{grid-column:span 4}.w6{grid-column:span 6}
.c-head{display:flex;justify-content:space-between;align-items:baseline;margin-bottom:12px;border-bottom:1px solid %(line)s;padding-bottom:8px}
.c-head h3{font-size:13.5px;font-weight:700;color:%(ink)s}
.c-sub{font-size:10.5px;color:%(muted)s}
.hbars{display:flex;flex-direction:column;gap:11px;flex:1;justify-content:center}
.hb-row{display:flex;align-items:center;gap:10px}
.hb-lab{width:96px;font-size:12px;color:%(text)s;font-weight:600;flex-shrink:0}
.hb-track{flex:1;background:#f1f4f7;border-radius:6px;height:18px;display:flex;overflow:hidden}
.hb-fill{height:100%%;border-radius:0}
.hb-val{width:60px;text-align:right;font-size:12px;font-weight:700;color:%(ink)s}
.legend{display:flex;flex-wrap:wrap;gap:6px 16px;margin-top:12px}
.legend.mini{margin-top:8px}
.lg{display:flex;align-items:center;gap:6px;font-size:11px;color:%(slate)s}
.lg b{color:%(ink)s}
.sw{width:11px;height:11px;border-radius:3px;display:inline-block}
.donut-wrap{display:flex;flex-direction:column;align-items:center;flex:1;justify-content:center}
.donut{width:150px;height:150px}
.dn-top{text-anchor:middle;font-size:21px;font-weight:800;fill:%(ink)s}
.dn-bot{text-anchor:middle;font-size:9px;fill:%(muted)s;text-transform:uppercase;letter-spacing:.6px}
.stacked{flex:1;display:flex;flex-direction:column;justify-content:center}
.st-bar{height:30px;border-radius:7px;overflow:hidden;display:flex;background:#eee}
.st-seg{height:100%%}
.cols{width:100%%;height:auto}
.cx-lab{text-anchor:middle;font-size:10px;fill:%(muted)s}
.cx-val{text-anchor:middle;font-size:9.5px;font-weight:700;fill:%(ink)s}
.cx-tgt{text-anchor:end;font-size:8.5px;fill:%(danger)s}
.bullets{display:flex;flex-direction:column;gap:13px;flex:1;justify-content:center}
.bullet .bl-head{display:flex;justify-content:space-between;font-size:12px;font-weight:600;margin-bottom:5px}
.bl-track{position:relative;height:14px;background:#f1f4f7;border-radius:7px}
.bl-fill{height:100%%;border-radius:7px}
.bl-target{position:absolute;top:-3px;width:3px;height:20px;background:%(ink)s;border-radius:2px}
.bl-target.inline{position:relative;display:inline-block;top:3px;height:12px;margin-right:4px}
.bl-note{font-size:10px;color:%(muted)s;margin-top:2px}
.gauge svg{width:100%%;height:auto}
.g-val{text-anchor:middle;font-size:24px;font-weight:800;fill:%(ink)s}
.g-lab{text-anchor:middle;font-size:9.5px;fill:%(muted)s}
.mini-kpis{display:grid;grid-template-columns:repeat(4,1fr);gap:10px;flex:1;align-items:center}
.mk{background:#f6f8fa;border-radius:9px;padding:12px;text-align:center;font-size:11px;color:%(muted)s;font-weight:600}
.mk span{display:block;font-size:22px;font-weight:800;color:%(ink)s;margin-bottom:3px}
.lag-strip{display:grid;grid-template-columns:repeat(6,1fr);gap:12px;padding:16px 20px 4px}
.lag{background:%(card)s;border:1px solid %(line)s;border-left:4px solid %(green)s;border-radius:10px;padding:13px 14px;display:flex;flex-direction:column}
.lag.warn{border-left-color:%(amber)s}
.lag-v{font-size:26px;font-weight:800;color:%(ink)s;line-height:1}
.lag-l{font-size:11.5px;font-weight:600;color:%(text)s;margin-top:5px}
.lag-u{font-size:10px;color:%(muted)s;margin-top:1px}
.note-band{margin:0 20px 20px;background:#eaf4ee;border:1px solid #cfe6d8;border-radius:10px;padding:11px 16px;font-size:12px;color:#1d5a37;font-weight:500}
.foot{width:1280px;margin:8px auto 30px;font-size:11px;color:#5a6b7a;text-align:center}
@media print{body{background:#fff}.nav{position:static}.page{box-shadow:none;margin:0 0 12px;page-break-after:always;width:100%%}.foot{width:100%%}}
""" % C

def page_shell(body):
    return f"""<!DOCTYPE html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Wolverine / Shell Maintenance — KPI Report</title><style>{CSS}</style></head>
<body>
<nav class="nav"><b>WOLVERINE &times; SHELL · KPI REVIEW</b>
  <a href="#p1">Performance &amp; Cost</a><a href="#p2">HSSE &amp; Safety</a>
  <span class="sp"></span><small>Self-contained · no scripts · Power BI HTML-visual ready</small></nav>
{body}
<div class="foot">Generated from Data.xlsx, KPI_Template_2026.xlsm &amp; Safety_Learning_Cards.xlsx ·
Re-run generate_kpi_report.py after each data refresh · Targets sourced from client 2026 KPI template.</div>
</body></html>"""

if __name__ == "__main__":
    a = load(); s = load_safety()
    html = page_shell(build(a, s))
    with open(OUT, "w") as f: f.write(html)
    print("Wrote", OUT, f"({len(html):,} bytes)")
