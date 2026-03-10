import streamlit as st
from datetime import date, time
from components import (
    inject_css, status_badge, page_header, task_type_legend,
    TASK_TYPE_STYLES, module_start,
)
from mock_data import init_data, get_next_id


def show():
    init_data()
    inject_css()
    page_header("Taskboard", "Daily inpatient care schedule")

    all_tasks = st.session_state.tasks
    today_str = "2026-03-08"

    # ── Overdue Banner ────────────────────────────────────────────────
    overdue_tasks = [t for t in all_tasks if t["status"] == "Overdue"]
    if overdue_tasks:
        with st.container():
            module_start()
            st.markdown(
                f':material/warning: **{len(overdue_tasks)} Overdue '
                f'Task{"s" if len(overdue_tasks) != 1 else ""}**'
            )
            for t in sorted(overdue_tasks, key=lambda x: (x["due_date"], x["due_time"])):
                col_info, col_staff, col_action = st.columns([6, 2, 1])
                with col_info:
                    st.markdown(
                        f'**{t["animal_name"]}** &middot; {t["type"]} &middot; '
                        f'Due {t["due_date"]} at {t["due_time"]}',
                    )
                    if t["notes"]:
                        st.caption(t["notes"])
                with col_staff:
                    st.caption(t["assigned_to"])
                with col_action:
                    if st.button("Done", key=f"od_{t['id']}", type="primary", use_container_width=True):
                        t["status"] = "Completed"
                        st.rerun()
        st.divider()

    # ── Filters (compact row) ───────────────────────────────────────────
    fc1, fc2, fc3, fc4 = st.columns(4)
    with fc1:
        animals = sorted({t["animal_name"] for t in all_tasks})
        filter_animal = st.selectbox("Animal", ["All"] + animals, key="tb_animal")
    with fc2:
        staff = sorted({t["assigned_to"] for t in all_tasks})
        filter_staff = st.selectbox("Staff", ["All"] + staff, key="tb_staff")
    with fc3:
        filter_type = st.selectbox("Type", ["All", "Feeding", "Medication", "Walking",
                                             "Monitoring", "Procedure", "Other"], key="tb_type")
    with fc4:
        filter_status = st.selectbox("Status", ["All", "Pending", "Completed", "Overdue"], key="tb_status")

    # Apply filters — exclude overdue tasks from calendar (they appear in the banner)
    tasks = [t for t in all_tasks if t["status"] != "Overdue"]
    if filter_animal != "All":
        tasks = [t for t in tasks if t["animal_name"] == filter_animal]
    if filter_staff != "All":
        tasks = [t for t in tasks if t["assigned_to"] == filter_staff]
    if filter_type != "All":
        tasks = [t for t in tasks if t["type"] == filter_type]
    if filter_status != "All":
        tasks = [t for t in tasks if t["status"] == filter_status]

    # ── Metrics ─────────────────────────────────────────────────────────
    m1, m2, m3, m4 = st.columns(4)
    pending = len([t for t in all_tasks if t["status"] == "Pending"])
    completed = len([t for t in all_tasks if t["status"] == "Completed"])
    overdue = len([t for t in all_tasks if t["status"] == "Overdue"])
    m1.metric("Total", len(all_tasks))
    m2.metric("Pending", pending)
    m3.metric("Completed", completed)
    m4.metric("Overdue", overdue, delta="!" if overdue else None, delta_color="inverse")

    # ── Legend + Add Task ───────────────────────────────────────────────
    leg_col, add_col = st.columns([5, 1])
    with leg_col:
        task_type_legend()
    with add_col:
        _add_task_popover()

    st.divider()

    # ── Hourly Calendar ─────────────────────────────────────────────────
    if not tasks:
        st.info("No tasks match the current filters.")
    else:
        _render_calendar(tasks)


def _render_calendar(tasks):
    """Render the hourly calendar view."""
    # Determine hour range from tasks
    task_hours = set()
    for t in tasks:
        h = int(t["due_time"].split(":")[0])
        task_hours.add(h)

    if not task_hours:
        return

    min_hour = max(5, min(task_hours) - 1)
    max_hour = min(22, max(task_hours) + 1)

    for hour in range(min_hour, max_hour + 1):
        hour_tasks = [t for t in tasks if int(t["due_time"].split(":")[0]) == hour]
        hour_tasks.sort(key=lambda t: (t["due_time"], t["animal_name"]))

        time_str = _format_hour(hour)
        has_tasks = len(hour_tasks) > 0

        # Hour row
        time_col, tasks_col = st.columns([1, 9])

        with time_col:
            cls = "cal-time-active" if has_tasks else "cal-time"
            st.markdown(f'<div class="{cls}">{time_str}</div>', unsafe_allow_html=True)
        with tasks_col:
            if has_tasks:
                for task in hour_tasks:
                    _render_task_event(task)
            else:
                st.markdown('<div class="cal-divider"></div>', unsafe_allow_html=True)


def _render_task_event(task):
    """Render a single task as a compact calendar event."""
    color, bg = TASK_TYPE_STYLES.get(task["type"], ("#6b7280", "#f3f4f6"))
    is_done = task["status"] == "Completed"
    is_overdue = task["status"] == "Overdue"

    with st.container():
        module_start()
        # Main row: type indicator + info + staff + actions
        c1, c2, c3, c4 = st.columns([5, 3, 1, 1])

        with c1:
            dot = f'<span class="type-dot" style="background:{color};"></span>'
            name_type = f'**{task["animal_name"]}** &middot; {task["type"]}'
            if is_done:
                name_type = f'~~{name_type}~~'
            time_css = ("color:#ef4444;font-weight:600;" if is_overdue
                        else "color:rgba(255,255,255,0.35);" if is_done
                        else "color:rgba(255,255,255,0.4);")
            time_extra = " OVERDUE" if is_overdue else ""
            st.markdown(
                f'{dot} {name_type} &middot; '
                f'<span style="font-size:0.85em;{time_css}">{task["due_time"]}{time_extra}</span>',
                unsafe_allow_html=True,
            )
            if task["notes"]:
                st.caption(task["notes"])

        with c2:
            st.caption(task["assigned_to"])

        with c3:
            if task["status"] in ["Pending", "Overdue"]:
                if st.button(
                    "Done",
                    key=f"tc_{task['id']}",
                    type="primary",
                    use_container_width=True,
                ):
                    task["status"] = "Completed"
                    st.rerun()
            else:
                st.markdown(
                    status_badge(task["status"]),
                    unsafe_allow_html=True,
                )

        with c4:
            if task["status"] in ["Pending", "Overdue"]:
                with st.popover("...", use_container_width=True):
                    st.markdown("**Reassign Task**")
                    staff_names = [s["name"] for s in st.session_state.staff]
                    new_staff = st.selectbox(
                        "Assign to",
                        staff_names,
                        key=f"tr_{task['id']}",
                        label_visibility="collapsed",
                    )
                    if st.button("Confirm", key=f"trc_{task['id']}", use_container_width=True):
                        task["assigned_to"] = new_staff
                        st.rerun()

                    st.divider()
                    st.page_link(
                        st.session_state._pages["cases"],
                        label=f"View case",
                        icon=":material/medical_services:",
                    )


def _format_hour(h):
    return "12 AM" if h == 0 else f"{h} AM" if h < 12 else "12 PM" if h == 12 else f"{h-12} PM"


def _add_task_popover():
    with st.popover("+ Add Task", use_container_width=True):
        active_cases = [c for c in st.session_state.cases
                        if c["status"] in ["Open", "In Treatment"]]
        if not active_cases:
            st.info("No active cases.")
            return
        with st.form("tb_new"):
            task_case = st.selectbox(
                "Case *",
                [f"{c['id']} \u2014 {c['animal_name']}" for c in active_cases],
                key="tb_nc",
            )
            task_type = st.selectbox(
                "Type *",
                ["Feeding", "Medication", "Walking", "Monitoring", "Procedure", "Other"],
                key="tb_nt",
            )
            c1, c2 = st.columns(2)
            with c1:
                task_date = st.date_input("Due Date", value=date.today(), key="tb_nd")
            with c2:
                task_time = st.time_input("Due Time", key="tb_ntm")
            task_assignee = st.selectbox(
                "Assign To *",
                [s["name"] for s in st.session_state.staff],
                key="tb_na",
            )
            task_notes = st.text_input("Notes", key="tb_nn")
            if st.form_submit_button("Add Task", type="primary", use_container_width=True):
                cid = task_case.split(" \u2014 ")[0]
                aname = task_case.split(" \u2014 ")[1]
                st.session_state.tasks.append({
                    "id": f"T-{get_next_id('task'):03d}",
                    "case_id": cid, "animal_name": aname,
                    "type": task_type, "status": "Pending",
                    "assigned_to": task_assignee,
                    "due_date": str(task_date),
                    "due_time": task_time.strftime("%H:%M"),
                    "notes": task_notes,
                })
                st.success("Task added.")
                st.rerun()
