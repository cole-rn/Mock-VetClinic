import streamlit as st

# Color palettes
_G, _B, _Y, _R, _X = ("#d4edda", "#155724"), ("#cce5ff", "#004085"), ("#fff3cd", "#856404"), ("#f8d7da", "#721c24"), ("#e2e3e5", "#383d41")
_P, _T = ("#e2d5f1", "#5b2c8f"), ("#d1ecf1", "#0c5460")

STATUS_COLORS = {
    "Active - In Shelter": _G, "Checked In": _T, "Pending Intake": _Y,
    "Pending Discharge": _P, "Discharged": _X, "In Treatment": _B,
    "Open": _B, "Pending": _Y, "Closed": _X, "Completed": _G,
    "Overdue": _R, "Paid": _G, "Partial": _Y, "Authorized": _G,
    "Consent Declined": _R, "Routine": _G, "Urgent": ("#fff3cd", "#92400e"),
    "Emergency": _R, "Scheduled": _B, "Submitted": _B, "Received": _G,
    "Active": _G, "On Hold": _X, "Low": _G, "Medium": _Y, "High": _R,
}

TASK_TYPE_STYLES = {
    "Feeding": ("#3b82f6", "#dbeafe"), "Medication": ("#10b981", "#d1fae5"),
    "Walking": ("#f59e0b", "#fef3c7"), "Monitoring": ("#8b5cf6", "#ede9fe"),
    "Procedure": ("#ef4444", "#fee2e2"), "Other": ("#6b7280", "#f3f4f6"),
}

PRIORITY_COLORS = {"Routine": "#10b981", "Urgent": "#f59e0b", "Emergency": "#ef4444"}


def inject_css():
    st.markdown("""<style>
    .block-container { padding-top: 1.5rem !important; }

    /* Module backgrounds */
    [data-testid="stForm"], [data-testid="stExpander"] {
        box-shadow: inset 0 0 0 1000px #354d65 !important;
        outline: 1px solid rgba(14,165,233,0.12) !important;
        border-radius: 10px !important;
    }
    [data-testid="stMetric"] {
        box-shadow: inset 0 0 0 1000px #354d65 !important;
        outline: 1px solid rgba(14,165,233,0.12) !important;
        border-radius: 8px !important; padding: 10px 14px !important;
    }
    [data-testid="stVerticalBlock"]:has(> [data-testid="stElementContainer"] .module-marker) {
        box-shadow: inset 0 0 0 1000px #354d65 !important;
        outline: 1px solid rgba(14,165,233,0.12) !important;
        border-radius: 10px !important; padding: 16px !important;
    }

    /* Sidebar */
    section[data-testid="stSidebar"] [data-testid="stSidebarNav"] a {
        outline: 1px solid rgba(255,255,255,0.08) !important; border-radius: 6px !important; margin-bottom: 2px !important;
    }
    section[data-testid="stSidebar"] [data-testid="stSidebarNav"] a:hover {
        outline: 1px solid rgba(14,165,233,0.3) !important;
    }
    section[data-testid="stSidebar"] [data-testid="stSidebarNav"] a[aria-current="page"] {
        box-shadow: inset 0 0 0 1000px rgba(14,165,233,0.15), inset 3px 0 0 #0ea5e9 !important;
        outline: 1px solid rgba(14,165,233,0.25) !important;
    }
    section[data-testid="stSidebar"] .stMetric label { font-size: 0.78em !important; }
    section[data-testid="stSidebar"] .stMetric [data-testid="stMetricValue"] { font-size: 1.3em !important; }

    /* Typography & dividers */
    .main h1, .main h2, .main h3 { color: #7dd3fc !important; }
    hr, [data-testid="stSeparator"] { border-color: rgba(14,165,233,0.12) !important; }

    /* Badges & tags */
    .status-badge { display: inline-block; padding: 2px 10px; border-radius: 12px; font-size: 0.82em; font-weight: 600; line-height: 1.6; white-space: nowrap; }
    .allergy-tag, .safety-tag { display: inline-block; padding: 2px 8px; border-radius: 4px; font-size: 0.85em; margin: 2px; font-weight: 500; }
    .allergy-tag { background: #f8d7da; color: #721c24; }
    .safety-tag { background: #fff3cd; color: #856404; }

    /* Entity cards */
    .entity-card { padding: 10px 14px; border-radius: 8px; margin-bottom: 6px; transition: all 0.15s ease; }
    .entity-card .ec-title { font-weight: 600; font-size: 0.92em; margin-bottom: 2px; }
    .entity-card .ec-sub { font-size: 0.8em; color: rgba(255,255,255,0.5); }
    .section-label { font-size: 0.72em; text-transform: uppercase; letter-spacing: 0.1em; color: #38bdf8; font-weight: 700; margin: 14px 0 6px 0; }

    /* Calendar */
    .cal-time { font-size: 0.8em; color: rgba(255,255,255,0.25); font-weight: 600; font-variant-numeric: tabular-nums; padding-top: 2px; }
    .cal-time-active { font-size: 0.85em; color: rgba(255,255,255,0.7); font-weight: 700; }
    .cal-divider { border-top: 1px solid rgba(14,165,233,0.06); margin: 10px 0; }
    .cal-now-marker { border-top: 2px solid #0ea5e9; margin: 4px 0; position: relative; }
    .cal-now-marker::before { content: 'NOW'; position: absolute; top: -9px; left: 0; font-size: 0.65em; font-weight: 700; padding: 0 6px; }

    /* Task events */
    .task-event { padding: 8px 12px; border-radius: 8px; margin: 3px 0; border-left: 3px solid transparent; font-size: 0.9em; background: rgba(14,165,233,0.02); }
    .task-event-done { opacity: 0.5; }
    .task-event-overdue { background: rgba(239,68,68,0.06); border-left-color: #ef4444 !important; }
    .type-dot { display: inline-block; width: 10px; height: 10px; border-radius: 3px; margin-right: 6px; vertical-align: middle; }

    /* Case cards */
    .case-card { padding: 16px 18px; border-radius: 10px; transition: all 0.15s ease; margin-bottom: 4px; }
    .case-card .cc-priority { font-size: 0.7em; text-transform: uppercase; font-weight: 700; letter-spacing: 0.08em; margin-bottom: 4px; }
    .case-card .cc-name { font-weight: 700; font-size: 1.05em; margin-bottom: 2px; }
    .case-card .cc-diag { font-size: 0.88em; color: rgba(255,255,255,0.5); margin-bottom: 8px; }
    .case-card .cc-meta { font-size: 0.8em; color: rgba(255,255,255,0.35); }
    .case-card .cc-vet { font-size: 0.85em; color: rgba(255,255,255,0.55); margin-bottom: 6px; }

    /* Timeline */
    .tl-item { position: relative; padding-left: 24px; padding-bottom: 14px; border-left: 2px solid rgba(14,165,233,0.12); margin-left: 6px; }
    .tl-item:last-child { border-left-color: transparent; }
    .tl-item::before { content: ''; position: absolute; left: -5px; top: 4px; width: 8px; height: 8px; border-radius: 50%; background: #0ea5e9; }
    .tl-item-med::before { background: #10b981; }
    .tl-item-diag::before { background: #8b5cf6; }
    .tl-item-proc::before { background: #ef4444; }
    .tl-time { font-size: 0.75em; color: rgba(255,255,255,0.3); margin-bottom: 2px; }
    .tl-text { font-size: 0.88em; }

    /* Nav links */
    [data-testid="stPageLink-NavLink"] { outline: 1px solid rgba(14,165,233,0.2) !important; border-radius: 8px !important; padding: 6px 12px !important; }
    [data-testid="stPageLink-NavLink"]:hover { outline: 1px solid rgba(14,165,233,0.5) !important; box-shadow: inset 0 0 0 1000px rgba(14,165,233,0.08) !important; }

    /* Buttons */
    .stButton > button { box-shadow: inset 0 0 0 1000px #0ea5e9 !important; color: #fff !important; font-weight: 600 !important; }
    .stButton > button:hover { box-shadow: inset 0 0 0 1000px #0284c7 !important; color: #fff !important; }

    /* Tabs */
    .stTabs [data-baseweb="tab-highlight"] { background-color: #0ea5e9 !important; }
    .stTabs [data-baseweb="tab"][aria-selected="true"] { color: #7dd3fc !important; }

    /* Forms & inputs */
    .main [data-testid="stForm"] { padding: 16px !important; }
    [data-baseweb="select"] > div, [data-baseweb="input"] > div,
    [data-testid="stTextInput"] input, [data-testid="stTextArea"] textarea,
    [data-testid="stNumberInput"] input, [data-testid="stDateInput"] input,
    [data-testid="stTimeInput"] input { background: #1a2838 !important; }

    /* Misc */
    .legend-chip { display: inline-flex; align-items: center; gap: 5px; padding: 3px 10px; border-radius: 12px; font-size: 0.78em; font-weight: 600; margin: 2px 3px; }
    .info-panel { border-radius: 10px; padding: 16px 18px; }
    .info-row { display: flex; justify-content: space-between; padding: 4px 0; border-bottom: 1px solid rgba(14,165,233,0.06); font-size: 0.88em; }
    .info-row:last-child { border-bottom: none; }
    .info-label { color: rgba(255,255,255,0.4); }
    .info-value { font-weight: 600; }
    </style>""", unsafe_allow_html=True)


def status_badge(status):
    bg, fg = STATUS_COLORS.get(status, ("#e2e3e5", "#383d41"))
    return f'<span class="status-badge" style="background:{bg};color:{fg};">{status}</span>'


def page_header(title, description=None):
    st.markdown(f"## {title}")
    if description:
        st.caption(description)


def entity_list(items, empty_msg="No items found."):
    if not items:
        st.caption(empty_msg)
        return
    for item in items:
        badge = status_badge(item["status"]) if item.get("status") else ""
        st.markdown(
            f'<div class="entity-card" style="background:#2a3f55;border:1px solid rgba(14,165,233,0.10);">'
            f'<div class="ec-title">{item["title"]} &nbsp;{badge}</div>'
            f'<div class="ec-sub">{item.get("subtitle", "")}</div></div>',
            unsafe_allow_html=True)


def styled_container(content_html):
    st.markdown(
        f'<div style="background:#354d65;border:1px solid rgba(14,165,233,0.12);'
        f'border-radius:10px;padding:14px 16px;margin-bottom:8px;">{content_html}</div>',
        unsafe_allow_html=True)


def module_start():
    st.markdown('<div class="module-marker" style="display:none;"></div>', unsafe_allow_html=True)


def show_animal_summary(animal):
    badge = status_badge(animal["status"])
    alerts = ""
    if animal.get("allergies"):
        alerts += " ".join(f'<span class="allergy-tag">{a}</span>' for a in animal["allergies"])
    if animal.get("safety_concerns"):
        alerts += " ".join(f'<span class="safety-tag">{s}</span>' for s in animal["safety_concerns"])
    st.markdown(
        f"**{animal['name']}** &nbsp;{badge}&nbsp; "
        f"{animal['species']} &bull; {animal['breed']} &bull; "
        f"{animal.get('est_age', '')} &bull; {animal['gender']}"
        + (f" &bull; Housing: {animal['housing']}" if animal.get("housing") else "")
        + (f"<br>{alerts}" if alerts else ""),
        unsafe_allow_html=True)


def nav_links(links):
    pages = st.session_state.get("_pages", {})
    cols = st.columns(len(links))
    for col, (label, page_ref, icon) in zip(cols, links):
        if isinstance(page_ref, str):
            page_ref = pages.get(page_ref.strip("/"), page_ref)
        col.page_link(page_ref, label=label, icon=icon)


def case_selector(key="case_sel", status_filter=None, label="Select Case"):
    cases = st.session_state.cases
    if status_filter:
        if isinstance(status_filter, str):
            status_filter = [status_filter]
        cases = [c for c in cases if c["status"] in status_filter]
    if not cases:
        return None
    options = {f"{c['id']} \u2014 {c['animal_name']} ({c['status']})": c for c in cases}
    choice = st.selectbox(label, ["Select Case"] + list(options.keys()), key=key)
    return options.get(choice)


def task_type_legend():
    chips = "".join(
        f'<span class="legend-chip" style="background:{bg};color:{color};">'
        f'<span class="type-dot" style="background:{color};"></span>{ttype}</span>'
        for ttype, (color, bg) in TASK_TYPE_STYLES.items())
    st.markdown(chips, unsafe_allow_html=True)


def priority_indicator(priority):
    color = PRIORITY_COLORS.get(priority, "#6b7280")
    return (f'<span style="color:{color};font-weight:700;font-size:0.78em;'
            f'text-transform:uppercase;letter-spacing:0.06em;">'
            f'<span style="display:inline-block;width:8px;height:8px;'
            f'border-radius:50%;background:{color};margin-right:4px;'
            f'vertical-align:middle;"></span>{priority}</span>')


def case_card_html(case, animal=None):
    pri_color = PRIORITY_COLORS.get(case["priority"], "#6b7280")
    consent_icon = {"Authorized": '<span style="color:#10b981">Consent OK</span>',
                    "Pending": '<span style="color:#f59e0b">Consent Pending</span>',
                    "Consent Declined": '<span style="color:#ef4444">Consent Declined</span>',
                    }.get(case.get("consent_status", "Pending"), "")
    species_icon = ""
    if animal:
        species_icon = {"Dog": "Dog", "Cat": "Cat"}.get(animal["species"], animal["species"])
    diag = case.get("diagnosis", "No diagnosis yet") or "No diagnosis yet"
    if len(diag) > 45:
        diag = diag[:42] + "..."
    alerts_html = ""
    if animal:
        if animal.get("allergies"):
            alerts_html += " ".join(f'<span class="allergy-tag">{a}</span>' for a in animal["allergies"])
        if animal.get("safety_concerns"):
            alerts_html += " ".join(f'<span class="safety-tag">{s}</span>' for s in animal["safety_concerns"])
    return (f'<div class="case-card" style="background:#2a3f55;border:1px solid rgba(14,165,233,0.10);">'
            f'<div class="cc-priority" style="color:{pri_color};">{case["priority"]}</div>'
            f'<div class="cc-name">{case["animal_name"]} &mdash; {case["id"]}</div>'
            f'<div class="cc-diag">{diag}</div>'
            f'<div class="cc-vet">{case["vet_name"]}</div>'
            f'<div style="margin-bottom:6px;">{status_badge(case["status"])} &nbsp;{consent_icon}</div>'
            + (f'<div style="margin-bottom:4px;">{alerts_html}</div>' if alerts_html else "")
            + f'<div class="cc-meta">Opened {case["opened"]}'
            + (f' &bull; {species_icon}' if species_icon else "")
            + f'</div></div>')


def timeline_html(entries):
    if not entries:
        return '<span style="font-size:0.85em;color:rgba(255,255,255,0.35);">No activity recorded.</span>'
    return "".join(
        f'<div class="tl-item tl-item-{e.get("type", "")}">'
        f'<div class="tl-time">{e["time"]}</div>'
        f'<div class="tl-text">{e["text"]}</div></div>'
        for e in entries)
