import streamlit as st
from mock_data import init_data
from components import inject_css
from pages.dashboard import show as show_dashboard
from pages.intake import show as show_intake
from pages.cases import show as show_cases
from pages.taskboard import show as show_taskboard
from pages.discharge import show as show_discharge
from pages.inventory import show as show_inventory
from pages.client_portal import show as show_client_portal

st.set_page_config(
    page_title="VetClinic Pro",
    page_icon=":material/pets:",
    layout="wide",
    initial_sidebar_state="expanded",
)

init_data()
inject_css()


# ── Login Gate ────────────────────────────────────────────────────────────
def show_login():
    spacer_l, col, spacer_r = st.columns([1, 1, 1])
    with col:
        st.markdown("")
        st.markdown("")
        st.subheader("Login")
        with st.form("login_form"):
            st.text_input("Username", value="etorres", key="login_user")
            st.text_input("Password", value="password", type="password", key="login_pass")
            if st.form_submit_button("Sign In", use_container_width=True):
                st.session_state.logged_in = True
                st.rerun()


if not st.session_state.get("logged_in"):
    show_login()
    st.stop()

# ── Pages ─────────────────────────────────────────────────────────────────
page_dashboard = st.Page(show_dashboard, title="Dashboard", icon=":material/dashboard:", url_path="dashboard")
page_intake = st.Page(show_intake, title="Intake", icon=":material/assignment_add:", url_path="intake")
page_cases = st.Page(show_cases, title="Cases", icon=":material/medical_services:", url_path="cases")
page_taskboard = st.Page(show_taskboard, title="Taskboard", icon=":material/checklist:", url_path="taskboard")
page_discharge = st.Page(show_discharge, title="Discharge", icon=":material/exit_to_app:", url_path="discharge")
page_inventory = st.Page(show_inventory, title="Inventory", icon=":material/inventory_2:", url_path="inventory")
page_client_portal = st.Page(show_client_portal, title="Client Portal", icon=":material/people:", url_path="client-portal")

# Store page refs so page modules can use them in st.page_link()
st.session_state._pages = {
    "cases": page_cases,
    "taskboard": page_taskboard,
    "inventory": page_inventory,
    "discharge": page_discharge,
    "intake": page_intake,
    "client_portal": page_client_portal,
}

# ── Navigation ───────────────────────────────────────────────────────────
pg = st.navigation({
    "": [page_dashboard],
    "Clinical": [page_intake, page_cases, page_taskboard],
    "Operations": [page_discharge, page_inventory],
    "Client Services": [page_client_portal],
})

# ── Sidebar ──────────────────────────────────────────────────────────────
with st.sidebar:
    animals = st.session_state.animals
    cases = st.session_state.cases
    tasks = st.session_state.tasks
    inventory = st.session_state.inventory

    in_shelter = len([a for a in animals if a["status"] not in ["Discharged"]])
    active_cases = len([c for c in cases if c["status"] in ["Open", "In Treatment"]])
    overdue = len([t for t in tasks if t["status"] == "Overdue"])
    low_stock = len([i for i in inventory if i["stock"] <= i["reorder_point"]])

    c1, c2 = st.columns(2)
    c1.metric("In Care", in_shelter)
    c2.metric("Cases", active_cases)
    c1, c2 = st.columns(2)
    c1.metric("Overdue", overdue, delta="!" if overdue else None, delta_color="inverse")
    c2.metric("Low Stock", low_stock, delta="!" if low_stock else None, delta_color="inverse")

    st.divider()
    st.caption("Logged in as: **Emily Torres** (Administrator)")

pg.run()
