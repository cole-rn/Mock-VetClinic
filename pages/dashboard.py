import streamlit as st
import pandas as pd
from components import inject_css, status_badge, page_header, entity_list, module_start
from mock_data import init_data


def show():
    init_data()
    inject_css()
    page_header("Dashboard", "Shelter operations at a glance")

    animals = st.session_state.animals
    cases = st.session_state.cases
    tasks = st.session_state.tasks
    inventory = st.session_state.inventory

    # ── Quick Actions ───────────────────────────────────────────────────────
    pages = st.session_state._pages
    qa_links = [("intake", "New Intake", ":material/add_circle:"), ("cases", "Cases", ":material/medical_services:"),
                ("taskboard", "Taskboard", ":material/checklist:"), ("discharge", "Discharge", ":material/exit_to_app:"),
                ("inventory", "Inventory", ":material/inventory_2:"), ("client_portal", "Clients", ":material/people:")]
    for col, (key, label, icon) in zip(st.columns(6), qa_links):
        col.page_link(pages[key], label=label, use_container_width=True, icon=icon)

    st.divider()

    # ── Active Cases  |  Today's Tasks ──────────────────────────────────────
    col_cases, col_tasks = st.columns(2)

    with col_cases:
        with st.container():
            module_start()
            st.markdown("##### Active Cases")
            active = [c for c in cases if c["status"] not in ["Closed"]]
            if active:
                entity_list([{
                    "title": f"{c['animal_name']} \u2014 {c['diagnosis']}" if c.get("diagnosis") else c["animal_name"],
                    "subtitle": f"{c['vet_name']}  &bull;  {c['priority']}  &bull;  Opened {c['opened']}",
                    "status": c["status"],
                } for c in active])
            else:
                st.info("No active cases.")
            st.page_link(st.session_state._pages["cases"], label="View all cases \u2192", icon=":material/medical_services:")

    with col_tasks:
        with st.container():
            module_start()
            st.markdown("##### Today's Tasks")
            pending = [t for t in tasks if t["status"] in ["Pending", "Overdue"]]
            if pending:
                rows = []
                for t in sorted(pending, key=lambda t: (t["status"] != "Overdue", t["due_time"])):
                    rows.append({
                        "Task": t["type"],
                        "Animal": t["animal_name"],
                        "Due": t["due_time"],
                        "Assigned": t["assigned_to"],
                        "Status": t["status"],
                    })
                st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
            else:
                st.success("All tasks completed.")
            st.page_link(st.session_state._pages["taskboard"], label="View taskboard \u2192", icon=":material/checklist:")

    st.divider()

    # ── Inventory Alerts  |  Upcoming Appointments ──────────────────────────
    col_alerts, col_appts = st.columns(2)

    with col_alerts:
        with st.container():
            module_start()
            st.markdown("##### Inventory Alerts")
            alerts = [i for i in inventory if i["stock"] <= i["reorder_point"]]
            if alerts:
                entity_list([{
                    "title": i["name"],
                    "subtitle": (f"OUT OF STOCK &bull; {i['location']}" if i["stock"] == 0
                                 else f"Stock: {i['stock']}/{i['reorder_point']} &bull; {i['location']}"),
                    "status": "Overdue" if i["stock"] == 0 else "Pending",
                } for i in alerts])
            else:
                st.success("All stock levels OK.")
            st.page_link(st.session_state._pages["inventory"], label="View inventory \u2192", icon=":material/inventory_2:")

    with col_appts:
        with st.container():
            module_start()
            st.markdown("##### Upcoming Appointments")
            appts = st.session_state.appointments
            if appts:
                entity_list([{
                    "title": f"{a['animal_name']} \u2014 {a['reason']}",
                    "subtitle": f"{a['date']} at {a['time']} &bull; {a['client_name']}",
                    "status": a["status"],
                } for a in appts[:4]])
            else:
                st.caption("No upcoming appointments.")
            st.page_link(st.session_state._pages["discharge"], label="View discharge \u2192", icon=":material/exit_to_app:")
