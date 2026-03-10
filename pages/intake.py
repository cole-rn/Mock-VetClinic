import streamlit as st
import pandas as pd
from datetime import date
from components import inject_css, status_badge, page_header, show_animal_summary, entity_list, styled_container
from mock_data import init_data, get_next_id

DOG_BREEDS = [
    "Mixed Breed", "Labrador Retriever", "Golden Retriever", "German Shepherd",
    "Beagle", "Bulldog", "Poodle", "Rottweiler", "Husky", "Boxer",
    "Dachshund", "Chihuahua", "Pit Bull", "Border Collie", "Other",
]
CAT_BREEDS = [
    "Domestic Shorthair", "Domestic Longhair", "Siamese", "Persian",
    "Maine Coon", "Ragdoll", "Bengal", "Abyssinian", "Tabby", "Other",
]
SPECIES_LIST = ["Dog", "Cat", "Bird", "Rabbit", "Reptile", "Other"]
HOUSING_OPTIONS = [
    "Kennel K-01", "Kennel K-02", "Kennel K-03", "Kennel K-04",
    "Kennel K-05", "Kennel K-08", "Kennel K-12", "Kennel K-15",
    "Cat Room C-01", "Cat Room C-02", "Cat Room C-03", "Cat Room C-05",
    "Recovery R-01", "Recovery R-02", "Recovery R-03", "Recovery R-04",
    "Isolation I-01", "Isolation I-02",
]
TRIAGE_CHECKS = [
    "General appearance assessed", "Eyes, ears, nose examined",
    "Skin and coat checked", "Limb mobility evaluated",
    "Abdomen palpated", "Oral cavity inspected",
    "Hydration status checked", "Pain assessment completed",
]


def show():
    init_data()
    inject_css()
    page_header("Intake", "Register, check in, triage, and record vitals")

    if "selected_intake_animal_id" not in st.session_state:
        st.session_state.selected_intake_animal_id = None

    col_queue, col_form = st.columns([2, 3])

    with col_queue:
        _intake_queue()

    with col_form:
        _intake_form()


def _intake_queue():
    """Left column: animals grouped by what they need next."""
    animals = st.session_state.animals

    pending = [a for a in animals if a["status"] == "Pending Intake"]
    needs_triage = [a for a in animals
                    if a["status"] in ["Checked In", "Active - In Shelter"]
                    and not a.get("triage_done")]
    needs_vitals = [a for a in animals
                    if a["status"] in ["Checked In", "Active - In Shelter"]
                    and a.get("triage_done") and not a.get("vitals_done")]

    groups = [
        ("Pending Check-In", pending, "Pending Intake",
         lambda a: f"{a['species']} &bull; {a['breed']} &bull; {a['intake_date']}"),
        ("Needs Triage", needs_triage, "Checked In",
         lambda a: f"{a['species']} &bull; {a.get('housing') or 'Unassigned'}"),
        ("Needs Vitals", needs_vitals, "Active - In Shelter",
         lambda a: f"{a['species']} &bull; Triage: {a.get('triage_level', 'N/A')}"),
    ]
    for title, group, badge_status, subtitle_fn in groups:
        if group:
            st.markdown(f"##### {title}")
            for a in group:
                styled_container(
                    f"<strong>{a['name']}</strong> ({a['id']})<br>"
                    f"<span style='font-size:0.85em;opacity:0.6;'>{subtitle_fn(a)}</span> "
                    f"{status_badge(badge_status)}")
                if st.button("Select", key=f"iq_{a['id']}", use_container_width=True):
                    st.session_state.selected_intake_animal_id = a["id"]
                    st.rerun()

    if not pending and not needs_triage and not needs_vitals:
        st.success("All animals are fully processed.")

    # Recent intakes
    st.divider()
    st.markdown("##### Recent Intakes")
    recent = sorted(animals, key=lambda a: a["intake_date"], reverse=True)[:5]
    entity_list([{
        "title": f"{a['name']} ({a['id']})",
        "subtitle": f"{a['species']} &bull; {a['breed']} &bull; {a['intake_date']}",
        "status": a["status"],
    } for a in recent])


def _intake_form():
    """Right column: context-sensitive form based on selected animal's needs."""
    animals = st.session_state.animals

    # Animal selector — shows animals that need intake processing
    intake_statuses = ["Pending Intake", "Checked In", "Active - In Shelter"]
    intake_animals = [a for a in animals if a["status"] in intake_statuses]
    options = {"Register New": None}
    for a in intake_animals:
        label = f"{a['name']} ({a['id']}) \u2014 {a['species']}, {a['breed']}"
        options[label] = a

    choice = st.selectbox("Select animal", list(options.keys()), key="intake_sel")
    animal = options.get(choice)

    # Button selection overrides dropdown when dropdown is on "Register New"
    if animal is None and st.session_state.selected_intake_animal_id:
        animal = next(
            (a for a in intake_animals
             if a["id"] == st.session_state.selected_intake_animal_id),
            None,
        )
    elif animal is not None:
        st.session_state.selected_intake_animal_id = None

    if animal is None:
        _form_register_new()
    elif animal["status"] == "Pending Intake":
        _form_checkin(animal)
    elif not animal.get("triage_done"):
        _form_triage(animal)
    elif not animal.get("vitals_done"):
        _form_vitals(animal)
    else:
        # Fully processed — show summary + allergies editor
        st.markdown("##### Animal Summary")
        show_animal_summary(animal)
        st.success("Intake complete. This animal is ready for case assignment.")
        _form_allergies(animal)


# ── Register New Animal (UC 1) ──────────────────────────────────────────
def _form_register_new():
    st.markdown("##### Register New Animal")
    with st.form("register_form", clear_on_submit=False):
        c1, c2 = st.columns(2)
        with c1:
            species = st.selectbox("Species *", SPECIES_LIST, key="reg_species")
            breeds = DOG_BREEDS if species == "Dog" else CAT_BREEDS if species == "Cat" else ["Other"]
            breed = st.selectbox("Breed *", breeds, key="reg_breed")
            est_age = st.text_input("Estimated Age", placeholder="e.g. 3 years", key="reg_age")
        with c2:
            gender = st.radio("Gender *", ["Male", "Female", "Unknown"], horizontal=True, key="reg_gender")
            source = st.selectbox("Source *",
                                  ["Stray", "Owner Surrender", "Transfer", "Confiscation", "Born in Shelter"],
                                  key="reg_source")
            name = st.text_input("Name", placeholder="If known", key="reg_name")

        c1, c2 = st.columns(2)
        with c1:
            microchip = st.text_input("Microchip Number", placeholder="Scan or enter", key="reg_chip")
        with c2:
            physical_id = st.text_area("Physical Identifiers",
                                       placeholder="Color, markings, scars\u2026", height=68, key="reg_phys")
        notes = st.text_area("Additional Notes", height=68, key="reg_notes")
        submitted = st.form_submit_button("Register Animal", type="primary", use_container_width=True)

    if submitted:
        new_id = f"A-{get_next_id('animal')}"
        st.session_state.animals.append({
            "id": new_id, "name": name or "Unknown",
            "species": species, "breed": breed,
            "est_age": est_age or "Unknown", "gender": gender,
            "status": "Pending Intake", "microchip": microchip,
            "intake_date": str(date.today()), "housing": None,
            "weight": None, "source": source, "client_id": None,
            "allergies": [], "safety_concerns": [],
            "triage_level": None, "triage_done": False,
            "vitals_done": False, "checkin_complete": False,
        })
        st.success(f"Registered **{name or 'Unknown'}** ({new_id}). Select them above to continue check-in.")
        st.rerun()


# ── Check-In (UC 2) ─────────────────────────────────────────────────────
def _form_checkin(animal):
    st.markdown("##### Check-In")
    show_animal_summary(animal)

    with st.form("checkin_form"):
        c1, c2 = st.columns(2)
        with c1:
            vacc_status = st.selectbox("Vaccination Status",
                                       ["Unknown", "Up to Date", "Partial", "None"], key="ci_vacc")
            spay_neuter = st.selectbox("Spay/Neuter",
                                       ["Unknown", "Spayed", "Neutered", "Intact"], key="ci_spay")
        with c2:
            temperament = st.selectbox("Temperament",
                                       ["Friendly", "Shy", "Fearful", "Aggressive", "Unknown"], key="ci_temp")
            housing = st.selectbox("Housing Location *", [""] + HOUSING_OPTIONS, key="ci_housing")
        behavior_notes = st.text_area("Behavior Notes", height=68, key="ci_behav")
        submitted = st.form_submit_button("Complete Check-In", type="primary", use_container_width=True)

    if submitted:
        if not housing:
            st.error("Housing location is required.")
        else:
            for a in st.session_state.animals:
                if a["id"] == animal["id"]:
                    a["status"] = "Checked In"
                    a["housing"] = housing
                    a["checkin_complete"] = True
                    break
            st.success(f"**{animal['name']}** checked in \u2192 {housing}")
            st.rerun()


# ── Triage (UC 3) ────────────────────────────────────────────────────────
def _form_triage(animal):
    st.markdown("##### Triage Assessment")
    show_animal_summary(animal)

    with st.form("triage_form"):
        st.markdown('<div class="section-label">Checklist</div>', unsafe_allow_html=True)
        c1, c2 = st.columns(2)
        for i, item in enumerate(TRIAGE_CHECKS):
            col = c1 if i % 2 == 0 else c2
            col.checkbox(item, key=f"tri_{i}")

        st.markdown('<div class="section-label">Assessment</div>', unsafe_allow_html=True)
        urgency = st.radio("Urgency Level *", ["Low", "Medium", "High", "Emergency"],
                           horizontal=True, key="tri_urgency")
        injuries = st.text_area("Injuries / Urgent Concerns", height=68, key="tri_injuries")
        submitted = st.form_submit_button("Save Triage", type="primary", use_container_width=True)

    if submitted:
        for a in st.session_state.animals:
            if a["id"] == animal["id"]:
                a["triage_level"] = urgency
                a["triage_done"] = True
                if a["status"] == "Checked In":
                    a["status"] = "Active - In Shelter"
                break
        st.success(f"Triage saved \u2014 **{animal['name']}**: {urgency}")
        if urgency == "Emergency":
            st.error("EMERGENCY \u2014 Veterinarian notified automatically.")
        st.rerun()


# ── Vitals (UC 4) ────────────────────────────────────────────────────────
def _form_vitals(animal):
    st.markdown("##### Record Vitals")
    show_animal_summary(animal)

    prev = [v for v in st.session_state.vitals_log if v["animal_id"] == animal["id"]]
    if prev:
        with st.expander(f"Previous Vitals ({len(prev)} records)"):
            st.dataframe(pd.DataFrame(prev)[["date", "weight", "temp", "heart_rate", "resp_rate", "notes"]],
                         use_container_width=True, hide_index=True)

    with st.form("vitals_form"):
        c1, c2, c3, c4 = st.columns(4)
        with c1:
            weight = st.number_input("Weight (lbs) *", min_value=0.1, max_value=300.0,
                                     value=animal.get("weight") or 10.0, step=0.1, key="vt_weight")
        with c2:
            temp = st.number_input("Temp (\u00b0F) *", min_value=95.0, max_value=110.0,
                                   value=101.5, step=0.1, key="vt_temp")
        with c3:
            hr = st.number_input("Heart Rate *", min_value=20, max_value=300,
                                 value=80, step=1, key="vt_hr")
        with c4:
            rr = st.number_input("Resp Rate *", min_value=5, max_value=80,
                                 value=18, step=1, key="vt_rr")
        notes = st.text_area("Notes", height=68, key="vt_notes")
        submitted = st.form_submit_button("Save Vitals", type="primary", use_container_width=True)

    if submitted:
        warnings = []
        if animal["species"] == "Dog":
            if temp < 100.0 or temp > 102.5:
                warnings.append(f"Temp {temp}\u00b0F outside normal (100\u2013102.5)")
            if hr < 60 or hr > 140:
                warnings.append(f"HR {hr} outside normal (60\u2013140)")
        elif animal["species"] == "Cat":
            if temp < 100.5 or temp > 102.5:
                warnings.append(f"Temp {temp}\u00b0F outside normal (100.5\u2013102.5)")
            if hr < 140 or hr > 220:
                warnings.append(f"HR {hr} outside normal (140\u2013220)")
        st.session_state.vitals_log.append({
            "animal_id": animal["id"], "date": str(date.today()),
            "weight": weight, "temp": temp, "heart_rate": hr,
            "resp_rate": rr, "notes": notes,
        })
        for a in st.session_state.animals:
            if a["id"] == animal["id"]:
                a["weight"] = weight
                a["vitals_done"] = True
                break
        st.success(f"Vitals recorded for **{animal['name']}**.")
        for w in warnings:
            st.warning(w)
        st.rerun()


# ── Allergies & Alerts (UC 6) ────────────────────────────────────────────
def _form_allergies(animal):
    with st.expander("Update Allergies & Safety Concerns"):
        with st.form("alerts_form"):
            no_allergies = st.checkbox("No known allergies",
                                       value=len(animal["allergies"]) == 0, key="al_none")
            new_allergy = st.text_input("Add Allergy",
                                        placeholder="e.g. Penicillin, Chicken, Latex",
                                        key="al_new", disabled=no_allergies)
            new_concern = st.text_input("Add Safety Concern",
                                        placeholder="e.g. Bites when stressed, Flight risk",
                                        key="al_concern")
            submitted = st.form_submit_button("Save Alerts", type="primary", use_container_width=True)

        if submitted:
            for a in st.session_state.animals:
                if a["id"] == animal["id"]:
                    if no_allergies:
                        a["allergies"] = []
                    elif new_allergy.strip():
                        if new_allergy.strip() not in a["allergies"]:
                            a["allergies"].append(new_allergy.strip())
                    if new_concern.strip():
                        if new_concern.strip() not in a["safety_concerns"]:
                            a["safety_concerns"].append(new_concern.strip())
                    break
            st.success(f"Alerts updated for **{animal['name']}**.")
            st.rerun()
