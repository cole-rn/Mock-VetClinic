import streamlit as st
import pandas as pd
from datetime import date, datetime, timedelta
from components import inject_css, status_badge, page_header, entity_list, module_start
from mock_data import init_data, get_next_id


def _flag(i, today):
    exp = datetime.strptime(i["expiration"], "%Y-%m-%d").date()
    if i["stock"] == 0: return "OUT OF STOCK"
    if i["stock"] <= i["reorder_point"]: return "LOW"
    if exp < today: return "EXPIRED"
    if exp <= today + timedelta(days=90): return "EXPIRING"
    return "OK"


def show():
    init_data()
    inject_css()
    page_header("Inventory", "Stock levels, reorders, and controlled substances")

    inventory = st.session_state.inventory
    today = date(2026, 3, 8)

    # ── Summary Metrics ──────────────────────────────────────────────────
    flags = [_flag(i, today) for i in inventory]
    total = len(inventory)
    low_stock, out_of_stock = flags.count("LOW"), flags.count("OUT OF STOCK")
    expiring_soon, expired = flags.count("EXPIRING"), flags.count("EXPIRED")

    m1, m2, m3, m4, m5 = st.columns(5)
    m1.metric("Total Items", total)
    m2.metric("Low Stock", low_stock,
              delta="Needs attention" if low_stock else None, delta_color="inverse")
    m3.metric("Out of Stock", out_of_stock,
              delta="Critical" if out_of_stock else None, delta_color="inverse")
    m4.metric("Expiring (90d)", expiring_soon)
    m5.metric("Expired", expired,
              delta="Remove" if expired else None, delta_color="inverse")

    # ── Tabs ───────────────────────────────────────────────────────────────
    tab_stock, tab_reorder, tab_controlled = st.tabs([
        "Stock Levels", "Reorder", "Controlled Substances",
    ])

    # ── Stock Levels (UC 16) + Auto-Deductions (UC 15) ──────────────────
    with tab_stock:
        c1, c2, c3 = st.columns(3)
        with c1:
            categories = sorted({i["category"] for i in inventory})
            cat_filter = st.selectbox("Category", ["All"] + categories, key="inv_cat")
        with c2:
            locations = sorted({i["location"] for i in inventory})
            loc_filter = st.selectbox("Location", ["All"] + locations, key="inv_loc")
        with c3:
            status_filter = st.selectbox("Status", ["All", "Low Stock", "Out of Stock",
                                                     "Expiring Soon", "Expired"], key="inv_status")

        filtered = inventory[:]
        if cat_filter != "All":
            filtered = [i for i in filtered if i["category"] == cat_filter]
        if loc_filter != "All":
            filtered = [i for i in filtered if i["location"] == loc_filter]
        _STATUS_MAP = {"Low Stock": "LOW", "Out of Stock": "OUT OF STOCK",
                       "Expiring Soon": "EXPIRING", "Expired": "EXPIRED"}
        if status_filter in _STATUS_MAP:
            filtered = [i for i in filtered if _flag(i, today) == _STATUS_MAP[status_filter]]

        if not filtered:
            st.info("No items match the selected filters.")
        else:
            rows = [{
                "Name": i["name"], "Category": i["category"],
                "Stock": i["stock"], "Reorder At": i["reorder_point"],
                "Location": i["location"], "Expiration": i["expiration"],
                "Unit Cost": f"${i['unit_cost']:.2f}",
                "Controlled": "\u2705" if i["controlled"] else "",
                "Alert": _flag(i, today),
            } for i in filtered]
            st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

        with st.expander("Recent Auto-Deductions"):
            recent_meds = sorted(st.session_state.med_admin_log,
                                 key=lambda m: (m["date"], m["time"]), reverse=True)[:10]
            if recent_meds:
                st.dataframe(
                    pd.DataFrame(recent_meds)[["date", "time", "medication", "dosage", "case_id"]],
                    use_container_width=True, hide_index=True,
                )
            else:
                st.caption("No recent deductions.")

    # ── Reorder Queue (UC 17) ───────────────────────────────────────────
    with tab_reorder:
        flagged = [i for i in inventory if i["stock"] <= i["reorder_point"]]

        col_alerts, col_po = st.columns([2, 3])

        with col_alerts:
            st.markdown("##### Reorder Alerts")
            if not flagged:
                st.success("All items above reorder thresholds.")
            else:
                for item in flagged:
                    msg = (f"**{item['name']}** \u2014 Stock: **{item['stock']}** / "
                           f"Reorder at: {item['reorder_point']}\n\n"
                           f"Qty: {item['reorder_qty']} &bull; {item['vendor']}")
                    (st.error if item["stock"] == 0 else st.warning)(msg)

        with col_po:
            st.markdown("##### Create Purchase Order")
            with st.form("po_form"):
                c1, c2 = st.columns(2)
                with c1:
                    vendors = sorted({i["vendor"] for i in inventory})
                    vendor = st.selectbox("Vendor *", vendors, key="po_vendor")
                with c2:
                    delivery_date = st.date_input("Expected Delivery",
                                                  value=date(2026, 3, 15), key="po_delivery")
                vendor_items = [i for i in inventory if i["vendor"] == vendor]

                order_rows = []
                for item in vendor_items:
                    c1, c2, c3 = st.columns([3, 1, 1])
                    stock_warn = " \u26a0\ufe0f" if item["stock"] <= item["reorder_point"] else ""
                    c1.write(f"{item['name']} (Stock: {item['stock']}){stock_warn}")
                    qty = c2.number_input("Qty", min_value=0,
                                          value=item["reorder_qty"] if item["stock"] <= item["reorder_point"] else 0,
                                          key=f"po_qty_{item['id']}", label_visibility="collapsed")
                    c3.write(f"@ ${item['unit_cost']:.2f}")
                    if qty > 0:
                        order_rows.append({"name": item["name"], "qty": qty, "unit_cost": item["unit_cost"]})

                if order_rows:
                    po_total = sum(r["qty"] * r["unit_cost"] for r in order_rows)
                    st.markdown(f"**Order Total: ${po_total:,.2f}**")

                submitted = st.form_submit_button("Create Purchase Order", type="primary",
                                                   use_container_width=True)

            if submitted:
                if not order_rows:
                    st.error("No items selected.")
                else:
                    po_total = sum(r["qty"] * r["unit_cost"] for r in order_rows)
                    po_id = f"PO-{get_next_id('po')}"
                    st.session_state.purchase_orders.append({
                        "id": po_id, "vendor": vendor, "status": "Submitted",
                        "created": str(date.today()), "items": order_rows, "total": po_total,
                    })
                    st.success(f"Purchase Order **{po_id}** \u2014 **${po_total:,.2f}**")
                    st.rerun()

        # PO History
        pos = st.session_state.purchase_orders
        if pos:
            with st.expander(f"Purchase Order History ({len(pos)} orders)"):
                for po in sorted(pos, key=lambda p: p["created"], reverse=True):
                    with st.container():
                        module_start()
                        c1, c2, c3 = st.columns([3, 1, 1])
                        c1.markdown(f"**{po['id']}** \u2014 {po['vendor']} ({po['created']})")
                        c2.markdown(f"**${po['total']:,.2f}**")
                        c3.markdown(status_badge(po["status"]), unsafe_allow_html=True)
                        if po["status"] == "Submitted":
                            if st.button("Mark Received", key=f"po_recv_{po['id']}",
                                         use_container_width=True):
                                po["status"] = "Received"
                                for po_item in po["items"]:
                                    for inv in st.session_state.inventory:
                                        if inv["name"] == po_item["name"]:
                                            inv["stock"] += po_item["qty"]
                                            break
                                st.success(f"PO {po['id']} received. Inventory updated.")
                                st.rerun()

    # ── Controlled Substances (UC 18) ───────────────────────────────────
    with tab_controlled:
        controlled_inv = [i for i in inventory if i["controlled"]]
        log = st.session_state.controlled_log

        if controlled_inv:
            cols = st.columns(len(controlled_inv))
            for idx, item in enumerate(controlled_inv):
                with cols[idx]:
                    st.metric(item["name"].split(" ")[0], f"{item['stock']} units",
                              delta="Low" if item["stock"] <= item["reorder_point"] else None,
                              delta_color="inverse")

        col_log, col_tx = st.columns([2, 3])

        with col_log:
            st.markdown('<div class="section-label">Recent Transactions</div>', unsafe_allow_html=True)
            if log:
                for entry in log[:8]:
                    tx_color = ("rgba(255,107,107,0.1)" if entry["type"] in
                                ["Administer", "Dispense", "Waste"]
                                else "rgba(59,130,246,0.1)")
                    st.markdown(
                        f'<div style="background:{tx_color};padding:8px 12px;'
                        f'border-radius:8px;margin:4px 0;">'
                        f'<strong>{entry["type"]}</strong> &mdash; {entry["substance"]}'
                        f'<br><span style="font-size:0.85em;color:rgba(255,255,255,0.5);">'
                        f'{entry["date"]} {entry["time"]} &bull; '
                        f'{entry["quantity"]} {entry["unit"]} &bull; '
                        f'Vet: {entry["vet"]} &bull; Balance: {entry["running_balance"]}'
                        f'</span></div>',
                        unsafe_allow_html=True,
                    )
            else:
                st.caption("No transactions recorded.")

        with col_tx:
            st.markdown('<div class="section-label">New Transaction</div>', unsafe_allow_html=True)
            with st.form("ctrl_tx_form"):
                c1, c2 = st.columns(2)
                with c1:
                    tx_type = st.selectbox("Type *",
                                           ["Administer", "Receive", "Dispense",
                                            "Waste", "Transfer", "Adjustment"], key="ctrl_type")
                with c2:
                    substance = st.selectbox("Substance *",
                                             [i["name"] for i in controlled_inv], key="ctrl_sub")
                c1, c2, c3 = st.columns(3)
                with c1:
                    quantity = st.number_input("Qty *", min_value=0.1, step=0.1, key="ctrl_qty")
                with c2:
                    unit = st.selectbox("Unit", ["mL", "mg", "tablet", "patch", "vial"], key="ctrl_unit")
                with c3:
                    vet = st.selectbox("Vet *", [v["name"] for v in st.session_state.vets], key="ctrl_vet")
                c1, c2 = st.columns(2)
                with c1:
                    patient = st.text_input("Patient", placeholder="Animal name/ID", key="ctrl_patient")
                with c2:
                    witness = st.selectbox("Witness *",
                                           [s["name"] for s in st.session_state.staff], key="ctrl_witness")
                submitted = st.form_submit_button("Record", type="primary", use_container_width=True)

            if submitted:
                inv_item = next((i for i in controlled_inv if i["name"] == substance), None)
                if inv_item:
                    if tx_type in ["Administer", "Dispense", "Waste", "Transfer"]:
                        if quantity > inv_item["stock"]:
                            st.error(f"Exceeds balance ({inv_item['stock']}).")
                        else:
                            inv_item["stock"] -= quantity
                            _log_controlled(substance, tx_type, quantity, unit,
                                            patient, vet, witness, inv_item["stock"])
                            st.rerun()
                    else:
                        inv_item["stock"] += quantity
                        _log_controlled(substance, tx_type, quantity, unit,
                                        patient, vet, witness, inv_item["stock"])
                        st.rerun()

        # Audit report
        with st.expander("Generate Audit Report"):
            with st.form("ctrl_report_form"):
                c1, c2 = st.columns(2)
                with c1:
                    start_date = st.date_input("Start Date", value=date(2026, 3, 1), key="ctrl_start")
                with c2:
                    end_date = st.date_input("End Date", value=date(2026, 3, 8), key="ctrl_end")
                sub_filter = st.selectbox("Substance",
                                          ["All"] + [i["name"] for i in controlled_inv], key="ctrl_report_sub")
                report_type = st.radio("Type", ["Transaction Log", "Discrepancy Report"],
                                       horizontal=True, key="ctrl_report_type")
                if st.form_submit_button("Generate Report", type="primary", use_container_width=True):
                    filtered_log = [entry for entry in log
                                    if start_date <= datetime.strptime(entry["date"], "%Y-%m-%d").date() <= end_date]
                    if sub_filter != "All":
                        filtered_log = [entry for entry in filtered_log if entry["substance"] == sub_filter]
                    st.success(f"**{report_type}** \u2014 {len(filtered_log)} transactions found.")
                    st.info("Report ready for download/print. (Mock)")


def _log_controlled(substance, tx_type, quantity, unit, patient, vet, witness, balance):
    st.session_state.controlled_log.insert(0, {
        "id": f"CL-{get_next_id('controlled'):03d}",
        "date": str(date.today()), "time": datetime.now().strftime("%H:%M"),
        "substance": substance, "type": tx_type,
        "quantity": quantity, "unit": unit,
        "patient": patient or "N/A", "vet": vet,
        "witness": witness, "notes": "",
        "running_balance": balance,
    })
    st.success(f"{tx_type}: {quantity} {unit}. Balance: **{balance}**")
