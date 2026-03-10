import streamlit as st
import pandas as pd
from datetime import date, datetime
from components import (
    inject_css, status_badge, page_header, show_animal_summary,
    nav_links, case_card_html, timeline_html, priority_indicator,
    PRIORITY_COLORS, module_start,
)
from mock_data import init_data, get_next_id


def show():
    init_data()
    inject_css()
    page_header("Cases", "Medical case management")

    if "selected_case_id" not in st.session_state:
        st.session_state.selected_case_id = None

    cases = st.session_state.cases
    active = [c for c in cases if c["status"] in ["Open", "In Treatment", "Pending Discharge"]]

    # ── Header row: New Case button + status counts ─────────────────────
    hc1, hc2, hc3, hc4, hc5 = st.columns([2, 1, 1, 1, 1])
    with hc1:
        if st.button("Open New Case", icon=":material/add:", type="primary"):
            st.session_state["show_new_case_form"] = True
    with hc2:
        st.metric("In Treatment", len([c for c in active if c["status"] == "In Treatment"]))
    with hc3:
        st.metric("Open", len([c for c in active if c["status"] == "Open"]))
    with hc4:
        st.metric("Pending DC", len([c for c in active if c["status"] == "Pending Discharge"]))
    with hc5:
        st.metric("Closed", len([c for c in cases if c["status"] == "Closed"]))

    # New case form
    if st.session_state.get("show_new_case_form"):
        _new_case_form()
        return

    # ── Case selector ───────────────────────────────────────────────────
    st.markdown("##### Select Case")
    options = {"Select Case": None}
    for c in active:
        label = f"{c['id']} \u2014 {c['animal_name']} ({c['status']}) \u2014 {c['vet_name']}"
        options[label] = c
    choice = st.selectbox("Select a case to view details", list(options.keys()),
                          key="case_sel", label_visibility="collapsed",
                          placeholder="Select Case")
    case_from_dropdown = options.get(choice)

    # Dropdown takes priority
    if case_from_dropdown is not None:
        st.session_state.selected_case_id = None
        _case_detail(case_from_dropdown)
        return

    # Check if a case was selected by clicking a card
    if st.session_state.selected_case_id:
        case_from_card = next(
            (c for c in active if c["id"] == st.session_state.selected_case_id),
            None,
        )
        if case_from_card:
            if st.button("\u2190 Back to Overview", key="back_to_overview"):
                st.session_state.selected_case_id = None
                st.rerun()
            _case_detail(case_from_card)
            return
        else:
            st.session_state.selected_case_id = None

    _case_overview(active)


# ═══════════════════════════════════════════════════════════════════════════
# Case Overview - Card Grid
# ═══════════════════════════════════════════════════════════════════════════
def _case_overview(active):
    if not active:
        st.info("No active cases. Open a new case to get started.")
        return

    st.markdown("##### Active Cases")

    # Sort: Emergency first, then Urgent, then Routine; within that by date
    priority_order = {"Emergency": 0, "Urgent": 1, "Routine": 2}
    sorted_cases = sorted(active, key=lambda c: (
        priority_order.get(c["priority"], 9), c["opened"]
    ))

    # Render as 2-column card grid
    for i in range(0, len(sorted_cases), 2):
        for col, case in zip(st.columns(2), sorted_cases[i:i+2]):
            animal = next((a for a in st.session_state.animals if a["id"] == case["animal_id"]), None)
            with col:
                st.markdown(case_card_html(case, animal), unsafe_allow_html=True)
                if st.button(f"View {case['animal_name']} \u2014 {case['id']}",
                             key=f"case_card_{case['id']}", use_container_width=True):
                    st.session_state.selected_case_id = case["id"]
                    st.rerun()

    st.caption("Select a case from the dropdown above to view full details.")


# ═══════════════════════════════════════════════════════════════════════════
# Open New Case (UC 7)
# ═══════════════════════════════════════════════════════════════════════════
def _new_case_form():
    st.markdown("##### Open New Case")
    animals = st.session_state.animals
    eligible = [a for a in animals if a["status"] in ["Active - In Shelter", "Checked In"]]
    if not eligible:
        st.info("No animals eligible for a new case. Complete intake first.")
        if st.button("Cancel"):
            st.session_state["show_new_case_form"] = False
            st.rerun()
        return

    opts = {f"{a['name']} ({a['id']}) \u2014 {a['species']}, {a['breed']}": a for a in eligible}
    sel = st.selectbox("Animal *", list(opts.keys()), key="nc_animal")
    animal = opts[sel]
    show_animal_summary(animal)

    with st.form("new_case_form"):
        c1, c2 = st.columns(2)
        with c1:
            available_vets = [v for v in st.session_state.vets if v["available"]]
            vet_opts = [f"{v['name']} \u2014 {v['specialty']}" for v in available_vets]
            vet_choice = st.selectbox("Veterinarian *", vet_opts, key="nc_vet")
        with c2:
            priority = st.radio("Priority *", ["Routine", "Urgent", "Emergency"],
                                horizontal=True, key="nc_priority")
        reason = st.text_area("Treatment Reason *", height=80, key="nc_reason",
                              placeholder="Describe the reason for opening this case\u2026")
        c1, c2, _ = st.columns([1, 1, 3])
        with c1:
            submitted = st.form_submit_button("Create Case", type="primary")
        with c2:
            cancel = st.form_submit_button("Cancel")

    if submitted:
        if not reason.strip():
            st.error("Treatment reason is required.")
        else:
            vet = available_vets[vet_opts.index(vet_choice)]
            case_id = f"MC-{get_next_id('case')}"
            st.session_state.cases.append({
                "id": case_id, "animal_id": animal["id"],
                "animal_name": animal["name"],
                "vet_id": vet["id"], "vet_name": vet["name"],
                "status": "Open", "priority": priority,
                "diagnosis": "", "opened": str(date.today()),
                "consent_status": "Pending", "notes": reason.strip(),
            })
            st.session_state["show_new_case_form"] = False
            st.success(f"Case **{case_id}** created for **{animal['name']}** \u2192 {vet['name']}")
            if priority == "Emergency":
                st.error("EMERGENCY case \u2014 veterinarian notified immediately.")
            st.rerun()
    if cancel:
        st.session_state["show_new_case_form"] = False
        st.rerun()


# ═══════════════════════════════════════════════════════════════════════════
# Case Detail View (UC 5, 8, 9, 10, 11)
# ═══════════════════════════════════════════════════════════════════════════
def _case_detail(case):
    animal = next((a for a in st.session_state.animals if a["id"] == case["animal_id"]), None)

    # ── Info Panel ──────────────────────────────────────────────────────
    with st.container():
        module_start()
        ic1, ic2 = st.columns([3, 2])

        with ic1:
            # Animal info
            if animal:
                show_animal_summary(animal)
            st.markdown(
                f"**Case {case['id']}** &bull; Opened {case['opened']}"
                + (f"<br>**Diagnosis:** {case['diagnosis']}" if case.get("diagnosis") else ""),
                unsafe_allow_html=True,
            )

        with ic2:
            # Case metadata
            st.markdown(
                f"**Vet:** {case['vet_name']}<br>"
                f"**Priority:** {priority_indicator(case['priority'])}<br>"
                f"**Consent:** {status_badge(case.get('consent_status', 'Pending'))}<br>"
                f"**Status:** {status_badge(case['status'])}",
                unsafe_allow_html=True,
            )

    # ── Quick Actions ───────────────────────────────────────────────────
    links = [("View Tasks", "/taskboard", ":material/checklist:")]
    if case["status"] in ["In Treatment", "Pending Discharge"]:
        links.append(("Discharge", "/discharge", ":material/exit_to_app:"))
    nav_links(links)

    # ── Consent & Estimate (UC 5) ──────────────────────────────────────
    if case.get("consent_status") in ["Pending", None]:
        _section_consent(case)

    # ── Activity Timeline + Clinical Tabs ──────────────────────────────
    tab_timeline, tab_plan, tab_diag, tab_meds, tab_proc = st.tabs([
        "Activity", "Treatment Plan", "Diagnostics", "Medications", "Procedures",
    ])

    with tab_timeline:
        _section_timeline(case)

    with tab_plan:
        _section_treatment_plan(case)

    with tab_diag:
        _section_diagnostics(case)

    with tab_meds:
        _section_medications(case)

    with tab_proc:
        _section_procedures(case)


# ── Activity Timeline ──────────────────────────────────────────────────
def _section_timeline(case):
    """Build a case activity timeline from existing data."""
    _e = lambda time, text, typ, sort: {"time": time, "text": text, "type": typ, "sort": sort}
    entries = [_e(case["opened"],
                  f"Case opened &mdash; assigned to {case['vet_name']} ({case['priority']})",
                  "", case["opened"] + " 00:00")]

    for r in st.session_state.diagnostic_results:
        if r["case_id"] == case["id"]:
            entries.append(_e(r["ordered"],
                              f"<strong>{r['test']}</strong> ordered by {r.get('ordered_by', 'N/A')}",
                              "diag", r["ordered"] + " 08:00"))
            if r["status"] == "Completed" and r.get("result"):
                entries.append(_e(r["ordered"],
                                  f"<strong>{r['test']}</strong> result: {r['result'][:60]}",
                                  "diag", r["ordered"] + " 12:00"))

    for m in st.session_state.med_admin_log:
        if m["case_id"] == case["id"]:
            entries.append(_e(f"{m['date']} {m['time']}",
                              f"<strong>{m['medication']}</strong> {m['dosage']} ({m['method']}) by {m['administered_by']}",
                              "med", f"{m['date']} {m['time']}"))

    plan = next((p for p in st.session_state.treatment_plans if p["case_id"] == case["id"]), None)
    if plan:
        for item in plan["items"]:
            entries.append(_e(case["opened"],
                              f"Treatment: [{item['type']}] {item['description']} &mdash; {status_badge(item['status'])}",
                              "proc" if item["type"] == "Procedure" else "", case["opened"] + " 06:00"))

    if case.get("consent_status") == "Authorized":
        entries.append(_e(case["opened"], "Client consent obtained &mdash; authorized for treatment",
                          "", case["opened"] + " 05:00"))
    if case.get("notes"):
        entries.append(_e(case["opened"], f"Note: {case['notes']}", "", case["opened"] + " 04:00"))

    entries.sort(key=lambda e: e["sort"], reverse=True)
    st.markdown("##### Case Activity")
    st.markdown(timeline_html([{"time": e["time"], "text": e["text"], "type": e["type"]}
                                for e in entries]), unsafe_allow_html=True)


# ── Consent & Estimate (UC 5) ─────────────────────────────────────────
def _section_consent(case):
    with st.container():
        module_start()
        st.markdown("##### Consent & Cost Estimate")
        if f"estimate_items_{case['id']}" not in st.session_state:
            st.session_state[f"estimate_items_{case['id']}"] = [
                {"service": "Exam Fee", "cost": 75.00},
                {"service": "Lab Work", "cost": 85.00},
            ]
        edited = st.data_editor(
            pd.DataFrame(st.session_state[f"estimate_items_{case['id']}"]),
            num_rows="dynamic",
            column_config={
                "service": st.column_config.TextColumn("Service", required=True),
                "cost": st.column_config.NumberColumn("Cost ($)", min_value=0, format="%.2f", required=True),
            },
            use_container_width=True, key=f"est_editor_{case['id']}",
        )
        total = edited["cost"].sum() if len(edited) > 0 else 0
        st.markdown(f"**Estimated Total: ${total:,.2f}**")
        c1, c2, _ = st.columns([1, 1, 4])
        if c1.button("Approve", type="primary", key="consent_approve"):
            for c in st.session_state.cases:
                if c["id"] == case["id"]:
                    c["consent_status"] = "Authorized"
            st.session_state[f"estimate_items_{case['id']}"] = edited.to_dict("records")
            st.rerun()
        if c2.button("Decline", key="consent_decline"):
            for c in st.session_state.cases:
                if c["id"] == case["id"]:
                    c["consent_status"] = "Consent Declined"
            st.rerun()


# ── Treatment Plan (UC 8) ─────────────────────────────────────────────
def _section_treatment_plan(case):
    plan = next((p for p in st.session_state.treatment_plans if p["case_id"] == case["id"]), None)

    if plan and plan["items"]:
        for item in plan["items"]:
            st.markdown(
                f"\u2022 **[{item['type']}]** {item['description']} "
                f"{status_badge(item['status'])}",
                unsafe_allow_html=True,
            )
    else:
        st.caption("No treatment plan items yet.")

    # Diagnosis edit + add item
    with st.form(f"diag_form_{case['id']}"):
        diag = st.text_input("Diagnosis", value=case.get("diagnosis", ""), key=f"diag_{case['id']}")
        st.markdown('<div class="section-label">Add Treatment Item</div>', unsafe_allow_html=True)
        c1, c2 = st.columns(2)
        with c1:
            itype = st.selectbox("Type", ["Medication", "Procedure", "Monitoring", "Task"],
                                 key=f"tp_type_{case['id']}")
        with c2:
            ipri = st.selectbox("Status", ["Active", "Scheduled", "On Hold"],
                                key=f"tp_stat_{case['id']}")
        idesc = st.text_input("Description", placeholder="Describe treatment item\u2026",
                              key=f"tp_desc_{case['id']}")
        if st.form_submit_button("Save", type="primary", use_container_width=True):
            for c in st.session_state.cases:
                if c["id"] == case["id"]:
                    c["diagnosis"] = diag.strip()
                    if c["status"] == "Open":
                        c["status"] = "In Treatment"
                    break
            if idesc.strip():
                existing = next((p for p in st.session_state.treatment_plans
                                 if p["case_id"] == case["id"]), None)
                new_item = {"type": itype, "description": idesc.strip(), "status": ipri}
                if existing:
                    existing["items"].append(new_item)
                else:
                    st.session_state.treatment_plans.append({"case_id": case["id"], "items": [new_item]})
            st.rerun()


# ── Diagnostics (UC 9) ────────────────────────────────────────────────
def _section_diagnostics(case):
    results = [r for r in st.session_state.diagnostic_results if r["case_id"] == case["id"]]

    if results:
        for r in results:
            st.markdown(
                f"**{r['test']}** {status_badge(r['status'])} \u2014 {r['ordered']}"
                + (f"<br><small>{r['result']}</small>" if r.get("result") else ""),
                unsafe_allow_html=True,
            )
    else:
        st.caption("No diagnostics ordered.")

    # Order new test
    with st.form(f"diag_order_{case['id']}"):
        st.markdown('<div class="section-label">Order Test</div>', unsafe_allow_html=True)
        test_type = st.selectbox("Test Type", [
            "CBC Panel", "Chemistry Panel", "Urinalysis", "X-Ray", "Ultrasound",
            "Skin Scraping", "Fecal Exam", "FIV/FeLV Test", "Heartworm Test",
            "Cytology", "Biopsy", "Culture & Sensitivity",
        ], key=f"diag_type_{case['id']}")
        if st.form_submit_button("Order Test", type="primary", use_container_width=True):
            st.session_state.diagnostic_results.append({
                "case_id": case["id"], "test": test_type,
                "ordered": str(date.today()), "status": "Pending",
                "result": None, "ordered_by": case["vet_name"],
            })
            st.rerun()

    # Record results for pending tests
    pending_tests = [r for r in results if r["status"] == "Pending"]
    if pending_tests:
        with st.form(f"diag_result_{case['id']}"):
            st.markdown('<div class="section-label">Record Result</div>', unsafe_allow_html=True)
            test_opts = [f"{r['test']} ({r['ordered']})" for r in pending_tests]
            test_sel = st.selectbox("Test", test_opts, key=f"diag_sel_{case['id']}")
            result_text = st.text_area("Result *", height=68, key=f"diag_res_{case['id']}")
            if st.form_submit_button("Save Result", type="primary", use_container_width=True):
                if result_text.strip():
                    idx = test_opts.index(test_sel)
                    target = pending_tests[idx]
                    for r in st.session_state.diagnostic_results:
                        if (r["case_id"] == target["case_id"] and r["test"] == target["test"]
                                and r["ordered"] == target["ordered"]):
                            r["status"] = "Completed"
                            r["result"] = result_text.strip()
                            break
                    st.rerun()


# ── Medications (UC 10) ───────────────────────────────────────────────
def _section_medications(case):
    case_meds = sorted(
        [m for m in st.session_state.med_admin_log if m["case_id"] == case["id"]],
        key=lambda m: (m["date"], m["time"]), reverse=True
    )[:5]
    if case_meds:
        for m in case_meds:
            st.caption(f"**{m['medication']}** {m['dosage']} \u2014 {m['date']} {m['time']} by {m['administered_by']}")
    else:
        st.caption("No medication administrations recorded.")

    with st.form(f"med_form_{case['id']}"):
        st.markdown('<div class="section-label">Administer Medication</div>', unsafe_allow_html=True)
        c1, c2 = st.columns(2)
        with c1:
            med_options = [i["name"] for i in st.session_state.inventory
                           if i["category"] in ["Antibiotic", "NSAID", "Antiemetic",
                                                 "Opioid Analgesic", "Sedative", "Anesthetic", "Vaccine"]]
            medication = st.selectbox("Medication *", med_options, key=f"med_sel_{case['id']}")
        with c2:
            dosage = st.text_input("Dosage *", placeholder="e.g. 500mg", key=f"med_dose_{case['id']}")
        c1, c2 = st.columns(2)
        with c1:
            method = st.selectbox("Method", ["Oral", "Injection (IM)", "Injection (SQ)",
                                              "Injection (IV)", "Topical", "Transdermal"],
                                  key=f"med_method_{case['id']}")
        with c2:
            admin_by = st.selectbox("By",
                                    [s["name"] for s in st.session_state.staff
                                     if s["role"] in ["Vet Technician", "Volunteer"]],
                                    key=f"med_by_{case['id']}")
        if st.form_submit_button("Confirm", type="primary", use_container_width=True):
            if not dosage.strip():
                st.error("Dosage is required.")
            else:
                inv_item = next((i for i in st.session_state.inventory if i["name"] == medication), None)
                if inv_item and inv_item["stock"] <= 0:
                    st.error(f"Insufficient inventory for **{medication}**.")
                else:
                    st.session_state.med_admin_log.append({
                        "case_id": case["id"], "date": str(date.today()),
                        "time": datetime.now().strftime("%H:%M"),
                        "medication": medication, "dosage": dosage.strip(),
                        "method": method, "administered_by": admin_by, "notes": "",
                    })
                    if inv_item:
                        inv_item["stock"] = max(0, inv_item["stock"] - 1)
                    st.rerun()


# ── Procedures (UC 11) ────────────────────────────────────────────────
def _section_procedures(case):
    plan = next((p for p in st.session_state.treatment_plans if p["case_id"] == case["id"]), None)
    proc_items = [i for i in (plan["items"] if plan else [])
                  if i["type"] in ["Procedure", "Monitoring"]]

    if proc_items:
        for p in proc_items:
            st.markdown(
                f"\u2022 {p['description']} {status_badge(p['status'])}",
                unsafe_allow_html=True,
            )
    else:
        st.caption("No procedures scheduled. Add them in the Treatment Plan.")
        return

    pending = [p for p in proc_items if p["status"] != "Completed"]
    if not pending:
        st.success("All procedures completed.")
        return

    with st.form(f"proc_form_{case['id']}"):
        st.markdown('<div class="section-label">Record Procedure</div>', unsafe_allow_html=True)
        proc_opts = [f"[{p['type']}] {p['description']}" for p in pending]
        selected = st.selectbox("Procedure", proc_opts, key=f"proc_sel_{case['id']}")
        outcome = st.text_area("Outcome / Observations *", height=68, key=f"proc_out_{case['id']}")
        if st.form_submit_button("Complete Procedure", type="primary", use_container_width=True):
            if outcome.strip():
                idx = proc_opts.index(selected)
                pending[idx]["status"] = "Completed"
                st.rerun()
