import streamlit as st
import pandas as pd
from components import inject_css, status_badge, page_header, entity_list, show_animal_summary, module_start
from mock_data import init_data


def show():
    init_data()
    inject_css()
    page_header("Client Portal", "Client information, communications, and billing")

    if "selected_client_id" not in st.session_state:
        st.session_state.selected_client_id = None

    clients = st.session_state.clients

    # ── Client selector ──────────────────────────────────────────────────
    options = {"Select Client": None}
    for c in clients:
        options[f"{c['name']} ({c['id']}) \u2014 {c['email']}"] = c
    choice = st.selectbox("Select a client", list(options.keys()),
                          key="client_sel", label_visibility="collapsed",
                          placeholder="Select Client")
    client_from_dropdown = options.get(choice)

    # Dropdown takes priority
    if client_from_dropdown is not None:
        st.session_state.selected_client_id = None
        _client_detail(client_from_dropdown)
        return

    # Check if a client was selected by clicking a button
    if st.session_state.selected_client_id:
        client_from_btn = next(
            (c for c in clients if c["id"] == st.session_state.selected_client_id),
            None,
        )
        if client_from_btn:
            if st.button("\u2190 Back to Overview", key="back_to_clients"):
                st.session_state.selected_client_id = None
                st.rerun()
            _client_detail(client_from_btn)
            return
        else:
            st.session_state.selected_client_id = None

    _client_overview(clients)


# ═══════════════════════════════════════════════════════════════════════════
# Client Overview
# ═══════════════════════════════════════════════════════════════════════════
def _client_overview(clients):
    st.markdown("##### All Clients")
    if not clients:
        st.info("No clients registered.")
        return
    for c in clients:
        with st.container():
            module_start()
            col_info, col_btn = st.columns([5, 1])
            with col_info:
                st.markdown(
                    f"**{c['name']}** ({c['id']})<br>"
                    f"<span style='font-size:0.85em;opacity:0.6;'>"
                    f"{c['email']} &bull; {c['phone']} &bull; Preferred: {c['preferred_contact']}"
                    f"</span>",
                    unsafe_allow_html=True,
                )
            with col_btn:
                if st.button("View", key=f"client_btn_{c['id']}", use_container_width=True):
                    st.session_state.selected_client_id = c["id"]
                    st.rerun()


# ═══════════════════════════════════════════════════════════════════════════
# Client Detail View
# ═══════════════════════════════════════════════════════════════════════════
def _client_detail(client):
    _section_contact_info(client)

    tab_animals, tab_messages, tab_invoices = st.tabs([
        "Animals", "Communications", "Invoices",
    ])

    with tab_animals:
        _section_animals(client)
    with tab_messages:
        _section_messages(client)
    with tab_invoices:
        _section_invoices(client)


# ── Contact Info ─────────────────────────────────────────────────────────
def _section_contact_info(client):
    client_animals = [a for a in st.session_state.animals
                      if a.get("client_id") == client["id"]]
    client_invoices = [inv for inv in st.session_state.invoices
                       if inv["client_name"] == client["name"]]
    client_msgs = [m for m in st.session_state.messages
                   if m["client_id"] == client["id"]]

    with st.container():
        module_start()
        c1, c2 = st.columns([3, 2])
        with c1:
            st.markdown(f"### {client['name']}")
            st.markdown(
                f"**Phone:** {client['phone']}<br>"
                f"**Email:** {client['email']}<br>"
                f"**Address:** {client['address']}<br>"
                f"**Preferred Contact:** {client['preferred_contact']}",
                unsafe_allow_html=True,
            )
        with c2:
            m1, m2, m3 = st.columns(3)
            m1.metric("Animals", len(client_animals))
            m2.metric("Invoices", len(client_invoices))
            m3.metric("Threads", len(client_msgs))


# ── Animals Tab ──────────────────────────────────────────────────────────
def _section_animals(client):
    animals = [a for a in st.session_state.animals
               if a.get("client_id") == client["id"]]
    if not animals:
        st.caption("No animals linked to this client.")
        return

    st.markdown(f"##### Animals ({len(animals)})")
    for animal in animals:
        with st.container():
            module_start()
            show_animal_summary(animal)
            animal_cases = [c for c in st.session_state.cases
                            if c["animal_id"] == animal["id"]
                            and c["status"] != "Closed"]
            if animal_cases:
                for case in animal_cases:
                    st.markdown(
                        f"Active case: **{case['id']}** \u2014 "
                        f"{case['diagnosis'] or 'No diagnosis'} "
                        f"{status_badge(case['status'])}",
                        unsafe_allow_html=True,
                    )


# ── Communications Tab ───────────────────────────────────────────────────
def _section_messages(client):
    messages = [m for m in st.session_state.messages
                if m["client_id"] == client["id"]]
    if not messages:
        st.caption("No communication history for this client.")
        return

    st.markdown(f"##### Message Threads ({len(messages)})")
    for msg in messages:
        with st.expander(f"{msg['animal_name']} \u2014 Case {msg['case_id']}"):
            for entry in msg["thread"]:
                is_clinic = entry["sender"] == "Clinic"
                name = "assistant" if is_clinic else "user"
                with st.chat_message(name):
                    st.markdown(f"**{entry['sender']}** \u2014 {entry['time']}")
                    st.write(entry["text"])


# ── Invoices Tab ─────────────────────────────────────────────────────────
def _section_invoices(client):
    invoices = [inv for inv in st.session_state.invoices
                if inv["client_name"] == client["name"]]
    if not invoices:
        st.caption("No invoices for this client.")
        return

    total_billed = sum(inv["total"] for inv in invoices)
    total_paid = sum(inv["paid"] for inv in invoices)
    outstanding = total_billed - total_paid

    m1, m2, m3 = st.columns(3)
    m1.metric("Total Billed", f"${total_billed:,.2f}")
    m2.metric("Total Paid", f"${total_paid:,.2f}")
    m3.metric("Outstanding", f"${outstanding:,.2f}",
              delta="Due" if outstanding > 0 else None,
              delta_color="inverse")

    for inv in invoices:
        with st.container():
            module_start()
            c1, c2, c3 = st.columns([3, 1, 1])
            c1.markdown(f"**{inv['id']}** \u2014 {inv['animal_name']} ({inv['date']})")
            c2.markdown(f"**${inv['total']:,.2f}**")
            c3.markdown(status_badge(inv["status"]), unsafe_allow_html=True)

            with st.expander("Line Items"):
                rows = [{
                    "Description": item["description"],
                    "Qty": item["qty"],
                    "Unit Price": f"${item['unit_price']:.2f}",
                    "Total": f"${item['qty'] * item['unit_price']:.2f}",
                } for item in inv["items"]]
                st.dataframe(pd.DataFrame(rows),
                             use_container_width=True, hide_index=True)
