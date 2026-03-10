import streamlit as st
import pandas as pd
from datetime import date, datetime, timedelta
from components import (
    inject_css, status_badge, page_header, show_animal_summary, entity_list,
    case_selector, module_start,
)
from mock_data import init_data, get_next_id


def show():
    init_data()
    inject_css()
    page_header("Discharge & Checkout", "Discharge, billing, follow-up, and client communication")

    if "selected_dc_case_id" not in st.session_state:
        st.session_state.selected_dc_case_id = None

    col_queue, col_flow = st.columns([1, 2])

    with col_queue:
        _discharge_queue()

    with col_flow:
        _discharge_flow()


def _discharge_queue():
    """Left column: cases ready for discharge + recent invoices."""
    cases = st.session_state.cases
    ready = [c for c in cases
             if c["status"] in ["Pending Discharge"]
             or (c["status"] == "In Treatment"
                 and c.get("consent_status") == "Authorized")]

    st.markdown("##### Ready for Discharge")
    if ready:
        for c in ready:
            with st.container():
                module_start()
                st.markdown(
                    f"**{c['id']}** \u2014 {c['animal_name']}<br>"
                    f"<span style='font-size:0.85em;opacity:0.6;'>"
                    f"{c['vet_name']} &bull; {c['diagnosis'][:35]}"
                    f"</span> {status_badge(c['status'])}",
                    unsafe_allow_html=True,
                )
                if st.button("Select", key=f"dc_q_{c['id']}", use_container_width=True):
                    st.session_state.selected_dc_case_id = c["id"]
                    st.rerun()
    else:
        st.caption("No cases ready for discharge.")

    invoices = st.session_state.invoices
    with st.expander(f"Recent Invoices ({len(invoices)})"):
        if invoices:
            entity_list([{
                "title": f"{inv['id']} \u2014 {inv['animal_name']}",
                "subtitle": f"{inv['client_name']} &bull; ${inv['total']:,.2f} &bull; Paid: ${inv['paid']:,.2f}",
                "status": inv["status"],
            } for inv in invoices[-5:]])
        else:
            st.caption("No invoices yet.")

    appts = st.session_state.appointments
    with st.expander(f"Upcoming Follow-Ups ({len(appts)})"):
        if appts:
            entity_list([{
                "title": f"{a['animal_name']} \u2014 {a['reason']}",
                "subtitle": f"{a['date']} at {a['time']} &bull; {a['client_name']}",
                "status": a["status"],
            } for a in appts])
        else:
            st.caption("No follow-ups scheduled.")


def _discharge_flow():
    """Right column: the discharge workflow."""
    case = case_selector(key="dc_case",
                         status_filter=["In Treatment", "Pending Discharge", "Closed"],
                         label="Select case for discharge")

    # Button selection overrides dropdown when dropdown is empty
    if not case and st.session_state.selected_dc_case_id:
        case = next(
            (c for c in st.session_state.cases
             if c["id"] == st.session_state.selected_dc_case_id),
            None,
        )
    elif case:
        st.session_state.selected_dc_case_id = None

    if not case:
        st.caption("Select a case from the dropdown or the queue to begin the discharge workflow.")
        st.page_link(st.session_state._pages["cases"], label="View active cases \u2192",
                     icon=":material/medical_services:")
        return

    animal = next((a for a in st.session_state.animals if a["id"] == case["animal_id"]), None)
    if animal:
        show_animal_summary(animal)
    st.caption(f"Case {case['id']} &bull; {case['diagnosis']}")

    client = None
    if animal and animal.get("client_id"):
        client = next((c for c in st.session_state.clients if c["id"] == animal["client_id"]), None)
    if client:
        st.caption(f"Client: **{client['name']}** &bull; {client['email']} &bull; {client['phone']}")

    if st.button("View Case \u2192", key="dc_view_case", icon=":material/medical_services:"):
        st.session_state.selected_case_id = case["id"]
        st.switch_page(st.session_state._pages["cases"])

    # ── Workflow tabs ──────────────────────────────────────────────────
    tab_dc, tab_inv, tab_fu, tab_portal = st.tabs([
        "Discharge", "Checkout & Invoice", "Follow-Up", "Client Portal",
    ])

    with tab_dc:
        _tab_discharge(case, animal)

    with tab_inv:
        _tab_checkout(case, client)

    with tab_fu:
        _tab_followup(case, client)

    with tab_portal:
        _tab_client_portal(case, client)


# ── Discharge Tab (UC 13) ─────────────────────────────────────────────
def _tab_discharge(case, animal):
    if case["status"] == "Closed":
        st.success("Already discharged.")
    else:
        with st.form("dc_form"):
            instructions = st.text_area("Home Care Instructions *", height=80, key="dc_inst",
                                        placeholder="Rest, activity restrictions, wound care, diet\u2026")
            st.markdown('<div class="section-label">Take-Home Medications</div>', unsafe_allow_html=True)
            med_data = st.data_editor(
                pd.DataFrame(columns=["Medication", "Dosage", "Frequency", "Duration"]),
                num_rows="dynamic",
                column_config={
                    "Medication": st.column_config.TextColumn(required=True),
                    "Dosage": st.column_config.TextColumn(required=True),
                    "Frequency": st.column_config.SelectboxColumn(
                        options=["Once daily", "Twice daily", "Three times daily",
                                 "Every 12 hours", "As needed"], required=True),
                    "Duration": st.column_config.TextColumn(required=True),
                },
                use_container_width=True, key="dc_meds",
            )
            if st.form_submit_button("Finalize Discharge", type="primary", use_container_width=True):
                if not instructions.strip():
                    st.error("Home care instructions are required.")
                else:
                    for c in st.session_state.cases:
                        if c["id"] == case["id"]:
                            c["status"] = "Closed"
                            break
                    for a in st.session_state.animals:
                        if a["id"] == case["animal_id"]:
                            a["status"] = "Discharged"
                            a["housing"] = None
                            break
                    st.success(f"**{case['animal_name']}** discharged. Case closed.")
                    st.rerun()


# ── Checkout & Invoice Tab (UC 19) ────────────────────────────────────
def _tab_checkout(case, client):
    st.markdown("##### Generate Invoice")

    if f"inv_items_{case['id']}" not in st.session_state:
        # Auto-populate from treatment plan if available
        items = [{"description": "Exam Fee", "qty": 1, "unit_price": 75.00}]
        plan = next((p for p in st.session_state.treatment_plans if p["case_id"] == case["id"]), None)
        if plan:
            for item in plan["items"]:
                if item["type"] == "Medication":
                    items.append({"description": item["description"][:40], "qty": 1, "unit_price": 42.00})
                elif item["type"] == "Procedure":
                    items.append({"description": item["description"][:40], "qty": 1, "unit_price": 150.00})
        # Add diagnostics
        diags = [d for d in st.session_state.diagnostic_results if d["case_id"] == case["id"]]
        for d in diags:
            items.append({"description": d["test"], "qty": 1, "unit_price": 85.00})
        st.session_state[f"inv_items_{case['id']}"] = items

    edited = st.data_editor(
        pd.DataFrame(st.session_state[f"inv_items_{case['id']}"]),
        num_rows="dynamic",
        column_config={
            "description": st.column_config.TextColumn("Description", required=True),
            "qty": st.column_config.NumberColumn("Qty", min_value=1, default=1, required=True),
            "unit_price": st.column_config.NumberColumn("Unit Price ($)",
                                                        min_value=0, format="%.2f", required=True),
        },
        use_container_width=True, key=f"inv_editor_{case['id']}",
    )

    if len(edited) > 0:
        edited["subtotal"] = edited["qty"] * edited["unit_price"]
        total = edited["subtotal"].sum()
    else:
        total = 0

    # Invoice summary
    with st.container():
        module_start()
        sc1, sc2 = st.columns(2)
        with sc1:
            st.markdown(f"### ${total:,.2f}")
            st.caption("Invoice Total")
        with sc2:
            # Check existing invoices for this case
            existing = [inv for inv in st.session_state.invoices if inv["case_id"] == case["id"]]
            paid_so_far = sum(inv["paid"] for inv in existing)
            if paid_so_far > 0:
                st.markdown(f"Previously Paid: **${paid_so_far:,.2f}**")
                st.caption(f"Remaining: ${max(0, total - paid_so_far):,.2f}")

    st.markdown('<div class="section-label">Payment</div>', unsafe_allow_html=True)
    c1, c2, c3 = st.columns(3)
    with c1:
        payment_method = st.selectbox("Method",
                                      ["Credit Card", "Debit Card", "Cash", "Check", "Payment Plan"],
                                      key="inv_method")
    with c2:
        payment_type = st.radio("Type", ["Full", "Partial"], horizontal=True, key="inv_ptype")
    with c3:
        if payment_type == "Partial":
            amount = st.number_input("Amount ($)", min_value=0.01,
                                     max_value=float(total) if total > 0 else 9999.0,
                                     value=float(total / 2) if total > 0 else 0.01,
                                     step=0.01, key="inv_amount")
        else:
            amount = total
            st.metric("Amount", f"${total:,.2f}")

    if st.button("Process Payment", type="primary", key="inv_pay", use_container_width=True):
        inv_id = f"INV-{get_next_id('invoice')}"
        inv_status = "Paid" if amount >= total else "Partial"
        st.session_state.invoices.append({
            "id": inv_id, "case_id": case["id"],
            "client_name": client["name"] if client else "N/A",
            "animal_name": case["animal_name"],
            "status": inv_status, "date": str(date.today()),
            "items": edited.drop(columns=["subtotal"], errors="ignore").to_dict("records"),
            "total": total, "paid": amount, "payment_method": payment_method,
        })
        if inv_status == "Paid":
            st.success(f"**${amount:,.2f}** processed. Invoice **{inv_id}** \u2014 PAID.")
        else:
            st.warning(f"Partial: **${amount:,.2f}**. Remaining: **${total - amount:,.2f}**.")
        st.rerun()


# ── Follow-Up Tab (UC 14) ─────────────────────────────────────────────
def _tab_followup(case, client):
    # Show existing follow-ups for this case
    existing_appts = [a for a in st.session_state.appointments
                      if a["animal_id"] == case["animal_id"]]
    if existing_appts:
        st.markdown("##### Scheduled Follow-Ups")
        entity_list([{
            "title": f"{a['animal_name']} \u2014 {a['reason']}",
            "subtitle": f"{a['date']} at {a['time']} &bull; Reminder: {a['reminder']}",
            "status": a["status"],
        } for a in existing_appts])
        st.divider()

    st.markdown("##### Schedule New Follow-Up")
    with st.form("followup_form"):
        c1, c2, c3 = st.columns(3)
        with c1:
            apt_date = st.date_input("Date *", min_value=date.today(),
                                     value=date.today() + timedelta(days=7), key="fu_date")
        with c2:
            apt_time = st.time_input("Time *", key="fu_time")
        with c3:
            reminder = st.selectbox("Reminder",
                                    ["1 day before", "3 days before",
                                     "1 week before", "1 day + 1 week before"], key="fu_reminder")
        reason = st.text_input("Reason *", placeholder="e.g. Suture removal, Post-op check",
                               key="fu_reason")
        if st.form_submit_button("Schedule", type="primary", use_container_width=True):
            if not reason.strip():
                st.error("Reason is required.")
            else:
                st.session_state.appointments.append({
                    "id": f"APT-{get_next_id('appointment'):03d}",
                    "animal_id": case["animal_id"],
                    "animal_name": case["animal_name"],
                    "client_name": client["name"] if client else "N/A",
                    "date": str(apt_date), "time": apt_time.strftime("%H:%M"),
                    "reason": reason.strip(), "reminder": reminder, "status": "Scheduled",
                })
                st.success(f"Follow-up scheduled: **{apt_date}** at {apt_time.strftime('%H:%M')}")
                st.rerun()


def _append_msg(case, client, text):
    """Append a clinic message to the case thread, creating one if needed."""
    thread = next((m for m in st.session_state.messages if m["case_id"] == case["id"]), None)
    entry = {"sender": "Clinic", "text": text, "time": datetime.now().strftime("%Y-%m-%d %H:%M")}
    if thread:
        thread["thread"].append(entry)
    else:
        st.session_state.messages.append({
            "id": f"MSG-{get_next_id('message'):03d}",
            "client_id": client["id"], "client_name": client["name"],
            "case_id": case["id"], "animal_name": case["animal_name"],
            "thread": [entry],
        })


# ── Client Portal Tab (UC 20) ─────────────────────────────────────────
def _tab_client_portal(case, client):
    if not client:
        st.info("No client linked to this animal. Client portal features require a linked client.")
        return

    # Client info
    with st.container():
        module_start()
        cc1, cc2 = st.columns(2)
        with cc1:
            st.markdown(f"**{client['name']}**")
            st.caption(f"{client['email']} &bull; {client['phone']}")
        with cc2:
            st.caption(f"Preferred: {client['preferred_contact']}")
            st.caption(f"Address: {client['address']}")

    # ── Visit Summary Generation ──────────────────────────────────────
    st.markdown("##### Visit Summary")

    # Auto-compose summary from case data
    diags = [d for d in st.session_state.diagnostic_results if d["case_id"] == case["id"]]
    meds = [m for m in st.session_state.med_admin_log if m["case_id"] == case["id"]]
    plan = next((p for p in st.session_state.treatment_plans if p["case_id"] == case["id"]), None)

    summary_parts = [
        f"Visit Summary for {case['animal_name']}",
        f"Case: {case['id']} | Veterinarian: {case['vet_name']}",
        f"Diagnosis: {case.get('diagnosis', 'Pending')}",
        f"Status: {case['status']}",
    ]
    if plan:
        summary_parts.append(f"Treatment items: {len(plan['items'])}")
    if diags:
        completed_diags = [d for d in diags if d["status"] == "Completed"]
        summary_parts.append(f"Diagnostics: {len(completed_diags)} completed, {len(diags) - len(completed_diags)} pending")
    if meds:
        summary_parts.append(f"Medications administered: {len(meds)}")

    summary_text = "\n".join(summary_parts)

    with st.container():
        module_start()
        st.text_area("Summary Preview", value=summary_text, height=120, key="portal_summary",
                     disabled=True)

    delivery = st.selectbox("Delivery Method", ["Client Portal", "Email", "Both", "SMS"], key="msg_delivery")

    if st.button("Send Visit Summary", type="primary", key="msg_send", use_container_width=True,
                 icon=":material/send:"):
        _append_msg(case, client, summary_text)
        st.success(f"Summary sent via **{delivery}** to **{client['name']}**.")
        st.rerun()

    # ── Message Thread ────────────────────────────────────────────────
    st.divider()
    st.markdown("##### Message Thread")

    thread = next((m for m in st.session_state.messages if m["case_id"] == case["id"]), None)
    if thread and thread["thread"]:
        for msg in thread["thread"]:
            is_clinic = msg["sender"] == "Clinic"
            align = "right" if is_clinic else "left"
            bg = "rgba(59,130,246,0.1)" if is_clinic else "rgba(255,255,255,0.04)"
            st.markdown(
                f'<div style="text-align:{align};margin:6px 0;">'
                f'<div style="display:inline-block;background:{bg};'
                f'padding:8px 14px;border-radius:12px;max-width:80%;text-align:left;">'
                f'<div style="font-size:0.78em;color:rgba(255,255,255,0.35);">'
                f'{msg["sender"]} &bull; {msg["time"]}</div>'
                f'<div style="font-size:0.9em;margin-top:2px;">{msg["text"]}</div>'
                f'</div></div>',
                unsafe_allow_html=True,
            )
    else:
        st.caption("No messages yet for this case.")

    # Send new message
    with st.form("client_msg_form"):
        new_msg = st.text_area("New Message", height=68, key="client_new_msg",
                               placeholder="Type a message to send to the client...")
        if st.form_submit_button("Send Message", use_container_width=True):
            if new_msg.strip():
                _append_msg(case, client, new_msg.strip())
                st.rerun()

    # ── Billing Summary for Client ───────────────────────────────────
    st.divider()
    st.markdown("##### Billing Summary")
    case_invoices = [inv for inv in st.session_state.invoices if inv["case_id"] == case["id"]]
    if case_invoices:
        for inv in case_invoices:
            with st.container():
                module_start()
                ic1, ic2, ic3 = st.columns([3, 1, 1])
                ic1.markdown(f"**{inv['id']}** &mdash; {inv['date']}")
                ic2.markdown(f"**${inv['total']:,.2f}**")
                ic3.markdown(
                    f"{status_badge(inv['status'])} "
                    f"<br><small>Paid: ${inv['paid']:,.2f}</small>",
                    unsafe_allow_html=True,
                )
    else:
        st.caption("No invoices generated for this case yet.")
        st.page_link(st.session_state._pages["discharge"],
                     label="Go to Checkout tab to generate an invoice")
