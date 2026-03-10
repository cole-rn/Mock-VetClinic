import streamlit as st
from datetime import date, datetime, timedelta


def init_data():
    if "logged_in" not in st.session_state:
        st.session_state.logged_in = False
    if "data_init" in st.session_state:
        return

    today = date(2026, 3, 8)

    # ── Factory helpers ───────────────────────────────────────────────────
    def _animal(id, name, sp, breed, age, gender, status, **kw):
        return {"id": id, "name": name, "species": sp, "breed": breed, "est_age": age,
                "gender": gender, "status": status, "microchip": "", "intake_date": "",
                "housing": None, "weight": None, "source": "Stray", "client_id": None,
                "allergies": [], "safety_concerns": [], "triage_level": "Low",
                "triage_done": True, "vitals_done": True, "checkin_complete": True, **kw}

    def _case(id, aid, aname, vid, vname, status, pri, diag, opened, consent="Authorized", notes=""):
        return {"id": id, "animal_id": aid, "animal_name": aname, "vet_id": vid,
                "vet_name": vname, "status": status, "priority": pri, "diagnosis": diag,
                "opened": opened, "consent_status": consent, "notes": notes}

    def _inv(id, name, cat, stock, rp, rq, loc, exp, cost, vendor, ctrl=False):
        return {"id": id, "name": name, "category": cat, "stock": stock,
                "reorder_point": rp, "reorder_qty": rq, "location": loc,
                "expiration": exp, "unit_cost": cost, "controlled": ctrl, "vendor": vendor}

    def _task(id, cid, name, typ, status, staff, time, notes, day=None):
        return {"id": id, "case_id": cid, "animal_name": name, "type": typ,
                "status": status, "assigned_to": staff,
                "due_date": str(day or today), "due_time": time, "notes": notes}

    def _ctrl(id, dt, tm, sub, typ, qty, unit, patient, vet, witness, notes, bal):
        return {"id": id, "date": dt, "time": tm, "substance": sub, "type": typ,
                "quantity": qty, "unit": unit, "patient": patient, "vet": vet,
                "witness": witness, "notes": notes, "running_balance": bal}

    # ── Animals ───────────────────────────────────────────────────────────
    st.session_state.animals = [
        _animal("A-1001", "Bella", "Dog", "Golden Retriever", "3 years", "Female",
                "Active - In Shelter", microchip="985121033456789", intake_date="2026-02-15",
                housing="Kennel K-12", weight=65.2, source="Owner Surrender",
                client_id="C-101", allergies=["Penicillin"]),
        _animal("A-1002", "Max", "Dog", "German Shepherd", "5 years", "Male",
                "Active - In Shelter", microchip="985121033456790", intake_date="2026-02-18",
                housing="Kennel K-08", weight=78.5,
                safety_concerns=["Aggressive with other dogs"], triage_level="Medium"),
        _animal("A-1003", "Luna", "Cat", "Siamese", "2 years", "Female",
                "Active - In Shelter", microchip="985121033456791", intake_date="2026-02-20",
                housing="Cat Room C-03", weight=9.1, source="Transfer"),
        _animal("A-1004", "Rocky", "Dog", "Labrador Retriever", "7 years", "Male",
                "Pending Discharge", microchip="985121033456792", intake_date="2026-02-10",
                housing="Recovery R-02", weight=72.0, source="Owner Surrender",
                client_id="C-103", allergies=["Sulfa drugs"]),
        _animal("A-1005", "Cleo", "Cat", "Persian", "4 years", "Female",
                "Active - In Shelter", microchip="985121033456793", intake_date="2026-03-01",
                housing="Cat Room C-05", weight=10.3, source="Owner Surrender", client_id="C-105"),
        _animal("A-1006", "Duke", "Dog", "Beagle", "1 year", "Male",
                "Checked In", microchip="985121033456794", intake_date="2026-03-07",
                housing="Kennel K-15", weight=24.0,
                triage_level=None, triage_done=False, vitals_done=False),
        _animal("A-1007", "Milo", "Cat", "Domestic Shorthair", "6 years", "Male",
                "Active - In Shelter", microchip="985121033456795", intake_date="2026-02-25",
                housing="Recovery R-04", weight=11.5,
                safety_concerns=["Bites when stressed"], triage_level="High"),
        _animal("A-1008", "Daisy", "Dog", "Poodle", "8 years", "Female",
                "Discharged", microchip="985121033456796", intake_date="2026-01-20",
                weight=45.0, source="Owner Surrender", client_id="C-104"),
        _animal("A-1009", "Shadow", "Cat", "Domestic Shorthair", "3 years", "Male",
                "Pending Intake", intake_date="2026-03-08",
                triage_level=None, triage_done=False, vitals_done=False, checkin_complete=False),
        _animal("A-1010", "Buddy", "Dog", "English Bulldog", "4 years", "Male",
                "Active - In Shelter", microchip="985121033456798", intake_date="2026-03-03",
                housing="Kennel K-04", weight=50.2, source="Owner Surrender",
                allergies=["Chicken-based food"]),
    ]

    # ── Clients ───────────────────────────────────────────────────────────
    st.session_state.clients = [
        {"id": "C-101", "name": "John Smith", "phone": "(555) 123-4567",
         "email": "john.smith@email.com", "address": "123 Main St, Springfield", "preferred_contact": "Email"},
        {"id": "C-102", "name": "Maria Garcia", "phone": "(555) 234-5678",
         "email": "maria.garcia@email.com", "address": "456 Oak Ave, Springfield", "preferred_contact": "Phone"},
        {"id": "C-103", "name": "Emily Chen", "phone": "(555) 345-6789",
         "email": "emily.chen@email.com", "address": "789 Pine Rd, Springfield", "preferred_contact": "Email"},
        {"id": "C-104", "name": "Sarah Kim", "phone": "(555) 456-7890",
         "email": "sarah.kim@email.com", "address": "321 Elm St, Springfield", "preferred_contact": "Portal"},
        {"id": "C-105", "name": "David Brown", "phone": "(555) 567-8901",
         "email": "david.brown@email.com", "address": "654 Maple Dr, Springfield", "preferred_contact": "Email"},
    ]

    st.session_state.vets = [
        {"id": "V-001", "name": "Dr. Sarah Chen", "specialty": "General Practice", "available": True},
        {"id": "V-002", "name": "Dr. James Wilson", "specialty": "Surgery", "available": True},
        {"id": "V-003", "name": "Dr. Maria Lopez", "specialty": "Internal Medicine", "available": False},
        {"id": "V-004", "name": "Dr. Kevin Park", "specialty": "Emergency", "available": True},
    ]

    st.session_state.staff = [
        {"id": "S-001", "name": "Emily Torres", "role": "Vet Technician"},
        {"id": "S-002", "name": "Michael Brown", "role": "Vet Technician"},
        {"id": "S-003", "name": "Lisa Park", "role": "Volunteer"},
        {"id": "S-004", "name": "David Kim", "role": "Inventory Manager"},
        {"id": "S-005", "name": "Rachel Adams", "role": "Client Services"},
        {"id": "S-006", "name": "Tom Harris", "role": "Staff"},
    ]

    # ── Cases ─────────────────────────────────────────────────────────────
    st.session_state.cases = [
        _case("MC-2001", "A-1001", "Bella", "V-001", "Dr. Sarah Chen",
              "In Treatment", "Routine", "Mild dermatitis - left flank", "2026-02-16",
              notes="Responding well to antibiotics"),
        _case("MC-2002", "A-1002", "Max", "V-002", "Dr. James Wilson",
              "In Treatment", "Urgent", "Hip dysplasia - bilateral", "2026-02-19",
              notes="Scheduled for surgical consult"),
        _case("MC-2003", "A-1005", "Cleo", "V-003", "Dr. Maria Lopez",
              "Open", "Routine", "Annual wellness exam", "2026-03-02",
              consent="Pending", notes="Routine checkup"),
        _case("MC-2004", "A-1004", "Rocky", "V-001", "Dr. Sarah Chen",
              "Pending Discharge", "Routine", "Post-neuter recovery", "2026-02-11",
              notes="Recovery on track, ready for discharge"),
        _case("MC-2005", "A-1007", "Milo", "V-002", "Dr. James Wilson",
              "In Treatment", "Urgent", "Left forelimb fracture", "2026-02-26",
              notes="Post-surgery, monitoring healing"),
        _case("MC-2006", "A-1008", "Daisy", "V-003", "Dr. Maria Lopez",
              "Closed", "Routine", "Dental cleaning and extraction", "2026-01-21",
              notes="Completed successfully"),
    ]

    st.session_state.treatment_plans = [
        {"case_id": "MC-2001", "items": [
            {"type": "Medication", "description": "Cephalexin 500mg - 2x daily for 14 days", "status": "Active"},
            {"type": "Procedure", "description": "Wound cleaning - every 48hrs", "status": "Active"},
            {"type": "Monitoring", "description": "Daily skin assessment", "status": "Active"}]},
        {"case_id": "MC-2002", "items": [
            {"type": "Medication", "description": "Carprofen 75mg - 1x daily", "status": "Active"},
            {"type": "Procedure", "description": "Surgical consultation", "status": "Scheduled"},
            {"type": "Monitoring", "description": "Mobility assessment - weekly", "status": "Active"}]},
        {"case_id": "MC-2005", "items": [
            {"type": "Medication", "description": "Meloxicam 1.5mg - 1x daily", "status": "Active"},
            {"type": "Procedure", "description": "Splint change - every 5 days", "status": "Active"},
            {"type": "Monitoring", "description": "X-ray follow-up in 2 weeks", "status": "Scheduled"}]},
    ]

    # ── Inventory ─────────────────────────────────────────────────────────
    st.session_state.inventory = [
        _inv("INV-001", "Amoxicillin 250mg", "Antibiotic", 450, 100, 500, "Pharmacy A-1", "2027-03-15", 0.45, "VetSupply Co."),
        _inv("INV-002", "Cephalexin 500mg", "Antibiotic", 200, 80, 300, "Pharmacy A-1", "2027-06-20", 0.62, "VetSupply Co."),
        _inv("INV-003", "Carprofen 75mg", "NSAID", 120, 50, 200, "Pharmacy A-2", "2027-01-10", 1.15, "PharmaVet Inc."),
        _inv("INV-004", "Meloxicam 1.5mg/mL", "NSAID", 35, 20, 60, "Pharmacy A-2", "2026-12-01", 2.30, "PharmaVet Inc."),
        _inv("INV-005", "Ketamine 100mg/mL", "Anesthetic", 15, 10, 25, "Controlled Cabinet C-1", "2026-09-30", 8.50, "MedVet Supplies", True),
        _inv("INV-006", "Buprenorphine 0.3mg/mL", "Opioid Analgesic", 8, 5, 15, "Controlled Cabinet C-1", "2026-11-15", 12.75, "MedVet Supplies", True),
        _inv("INV-007", "Rabies Vaccine", "Vaccine", 85, 30, 100, "Refrigerator R-1", "2026-08-20", 3.25, "VaxVet Corp."),
        _inv("INV-008", "DHPP Vaccine", "Vaccine", 60, 25, 80, "Refrigerator R-1", "2026-10-05", 4.50, "VaxVet Corp."),
        _inv("INV-009", "Surgical Sutures (3-0)", "Surgical Supply", 40, 15, 50, "Surgery S-1", "2028-01-01", 5.00, "SurgiPet Ltd."),
        _inv("INV-010", "IV Fluid LRS 1L", "Fluid", 22, 20, 48, "Supply Room B-2", "2027-05-30", 3.80, "VetSupply Co."),
        _inv("INV-011", "Fentanyl Patches 25mcg", "Opioid Analgesic", 4, 5, 10, "Controlled Cabinet C-1", "2026-07-15", 18.00, "MedVet Supplies", True),
        _inv("INV-012", "Metronidazole 500mg", "Antibiotic", 180, 60, 250, "Pharmacy A-1", "2027-04-22", 0.38, "PharmaVet Inc."),
        _inv("INV-013", "Cerenia 24mg", "Antiemetic", 0, 15, 30, "Pharmacy A-2", "2026-06-01", 6.20, "PharmaVet Inc."),
        _inv("INV-014", "Disposable Gloves (Box)", "Supply", 12, 10, 24, "Supply Room B-1", "2028-12-31", 8.50, "SurgiPet Ltd."),
        _inv("INV-015", "Diazepam 5mg/mL", "Sedative", 10, 5, 20, "Controlled Cabinet C-1", "2026-10-30", 9.25, "MedVet Supplies", True),
    ]

    # ── Tasks ─────────────────────────────────────────────────────────────
    st.session_state.tasks = [
        _task("T-001", "MC-2001", "Bella", "Feeding", "Pending", "Lisa Park", "08:00", "Standard diet, monitor appetite"),
        _task("T-002", "MC-2001", "Bella", "Medication", "Pending", "Emily Torres", "09:00", "Cephalexin 500mg oral"),
        _task("T-003", "MC-2002", "Max", "Walking", "Completed", "Tom Harris", "07:00", "Leash walk only, 15 min max"),
        _task("T-004", "MC-2002", "Max", "Medication", "Pending", "Michael Brown", "10:00", "Carprofen 75mg with food"),
        _task("T-005", "MC-2005", "Milo", "Monitoring", "Pending", "Emily Torres", "08:30", "Check splint, assess swelling"),
        _task("T-006", "MC-2005", "Milo", "Feeding", "Completed", "Lisa Park", "07:30", "Wet food, elevated bowl"),
        _task("T-007", "MC-2005", "Milo", "Medication", "Pending", "Emily Torres", "11:00", "Meloxicam 1.5mg oral"),
        _task("T-008", "MC-2001", "Bella", "Procedure", "Pending", "Michael Brown", "14:00", "Wound cleaning - left flank"),
        _task("T-009", "MC-2004", "Rocky", "Monitoring", "Completed", "Emily Torres", "06:30", "Post-op vitals check"),
        _task("T-010", "MC-2002", "Max", "Monitoring", "Overdue", "Michael Brown", "16:00",
              "Mobility assessment - OVERDUE", today - timedelta(days=1)),
        _task("T-011", "MC-2001", "Bella", "Feeding", "Pending", "Lisa Park", "12:00", "Lunch - standard diet"),
        _task("T-012", "MC-2002", "Max", "Feeding", "Pending", "Tom Harris", "12:30", "Lunch with medication mixed in"),
        _task("T-013", "MC-2005", "Milo", "Monitoring", "Pending", "Emily Torres", "15:00", "Afternoon splint check, pain assessment"),
        _task("T-014", "MC-2004", "Rocky", "Monitoring", "Pending", "Michael Brown", "16:00", "Afternoon vitals check"),
        _task("T-015", "MC-2001", "Bella", "Feeding", "Pending", "Lisa Park", "17:00", "Dinner - standard diet"),
        _task("T-016", "MC-2002", "Max", "Feeding", "Pending", "Tom Harris", "17:00", "Dinner"),
        _task("T-017", "MC-2005", "Milo", "Feeding", "Pending", "Lisa Park", "17:30", "Dinner - wet food, elevated bowl"),
        _task("T-018", "MC-2001", "Bella", "Medication", "Pending", "Michael Brown", "21:00", "Evening Cephalexin 500mg oral"),
        _task("T-019", "MC-2005", "Milo", "Medication", "Pending", "Emily Torres", "20:00", "Evening Meloxicam 1.5mg oral"),
    ]

    # ── Invoices ──────────────────────────────────────────────────────────
    st.session_state.invoices = [
        {"id": "INV-3001", "case_id": "MC-2006", "client_name": "Sarah Kim",
         "animal_name": "Daisy", "status": "Paid", "date": "2026-02-05",
         "items": [{"description": "Dental cleaning", "qty": 1, "unit_price": 250.00},
                   {"description": "Tooth extraction (2)", "qty": 1, "unit_price": 180.00},
                   {"description": "Anesthesia", "qty": 1, "unit_price": 120.00},
                   {"description": "Post-op medication", "qty": 1, "unit_price": 45.00}],
         "total": 595.00, "paid": 595.00, "payment_method": "Credit Card"},
        {"id": "INV-3002", "case_id": "MC-2004", "client_name": "Emily Chen",
         "animal_name": "Rocky", "status": "Pending", "date": "2026-03-06",
         "items": [{"description": "Neuter procedure", "qty": 1, "unit_price": 200.00},
                   {"description": "Anesthesia", "qty": 1, "unit_price": 100.00},
                   {"description": "Pain medication (7-day)", "qty": 1, "unit_price": 35.00},
                   {"description": "E-collar", "qty": 1, "unit_price": 15.00}],
         "total": 350.00, "paid": 0.00, "payment_method": None},
        {"id": "INV-3003", "case_id": "MC-2001", "client_name": "John Smith",
         "animal_name": "Bella", "status": "Partial", "date": "2026-03-01",
         "items": [{"description": "Exam fee", "qty": 1, "unit_price": 75.00},
                   {"description": "Skin scraping/culture", "qty": 1, "unit_price": 85.00},
                   {"description": "Cephalexin (14-day)", "qty": 1, "unit_price": 42.00},
                   {"description": "Medicated shampoo", "qty": 1, "unit_price": 28.00}],
         "total": 230.00, "paid": 100.00, "payment_method": "Credit Card"},
    ]

    # ── Messages ──────────────────────────────────────────────────────────
    st.session_state.messages = [
        {"id": "MSG-001", "client_id": "C-101", "client_name": "John Smith",
         "case_id": "MC-2001", "animal_name": "Bella", "thread": [
             {"sender": "Clinic", "text": "Bella's skin culture results are back. The infection is responding well to antibiotics.", "time": "2026-03-05 10:30"},
             {"sender": "John Smith", "text": "That's great news! How much longer on the medication?", "time": "2026-03-05 11:15"},
             {"sender": "Clinic", "text": "We recommend completing the full 14-day course. She should be done by March 1st.", "time": "2026-03-05 11:45"}]},
        {"id": "MSG-002", "client_id": "C-103", "client_name": "Emily Chen",
         "case_id": "MC-2004", "animal_name": "Rocky", "thread": [
             {"sender": "Clinic", "text": "Rocky's neuter surgery went well. He is recovering and should be ready for pickup tomorrow.", "time": "2026-03-06 15:00"},
             {"sender": "Emily Chen", "text": "Thank you! What time can I pick him up?", "time": "2026-03-06 15:30"},
             {"sender": "Clinic", "text": "Anytime between 10 AM and 5 PM. We will have discharge instructions ready.", "time": "2026-03-06 15:45"}]},
    ]

    # ── Controlled Substances Log ─────────────────────────────────────────
    st.session_state.controlled_log = [
        _ctrl("CL-001", "2026-03-07", "09:15", "Ketamine 100mg/mL", "Administer",
              2.0, "mL", "Milo (A-1007)", "Dr. James Wilson", "Emily Torres", "Pre-surgical sedation", 13.0),
        _ctrl("CL-002", "2026-03-06", "14:30", "Buprenorphine 0.3mg/mL", "Administer",
              0.5, "mL", "Milo (A-1007)", "Dr. James Wilson", "Michael Brown", "Post-surgical pain management", 7.5),
        _ctrl("CL-003", "2026-03-05", "08:00", "Ketamine 100mg/mL", "Receive",
              5.0, "mL", "N/A", "Dr. Kevin Park", "David Kim", "Restocking from PO-401", 15.0),
        _ctrl("CL-004", "2026-03-04", "11:00", "Diazepam 5mg/mL", "Administer",
              1.0, "mL", "Bella (A-1001)", "Dr. Sarah Chen", "Emily Torres", "Anxiety during wound cleaning", 9.0),
        _ctrl("CL-005", "2026-03-03", "16:45", "Fentanyl Patches 25mcg", "Administer",
              1.0, "patch", "Max (A-1002)", "Dr. James Wilson", "Michael Brown", "Pain management for hip dysplasia", 3.0),
    ]

    # ── Remaining collections ─────────────────────────────────────────────
    st.session_state.appointments = [
        {"id": "APT-001", "animal_id": "A-1008", "animal_name": "Daisy", "client_name": "Sarah Kim",
         "date": "2026-03-15", "time": "10:00", "reason": "Post-dental follow-up",
         "reminder": "3 days before", "status": "Scheduled"},
        {"id": "APT-002", "animal_id": "A-1004", "animal_name": "Rocky", "client_name": "Emily Chen",
         "date": "2026-03-22", "time": "14:00", "reason": "Suture removal - neuter",
         "reminder": "1 day before", "status": "Scheduled"},
    ]

    st.session_state.purchase_orders = [
        {"id": "PO-401", "vendor": "MedVet Supplies", "status": "Received", "created": "2026-03-04",
         "items": [{"name": "Ketamine 100mg/mL", "qty": 5, "unit_cost": 8.50}], "total": 42.50},
        {"id": "PO-402", "vendor": "PharmaVet Inc.", "status": "Submitted", "created": "2026-03-07",
         "items": [{"name": "Cerenia 24mg", "qty": 30, "unit_cost": 6.20},
                   {"name": "Meloxicam 1.5mg/mL", "qty": 60, "unit_cost": 2.30}], "total": 324.00},
        {"id": "PO-403", "vendor": "VetSupply Co.", "status": "Submitted", "created": "2026-03-07",
         "items": [{"name": "IV Fluid LRS 1L", "qty": 48, "unit_cost": 3.80}], "total": 182.40},
    ]

    st.session_state.vitals_log = [
        {"animal_id": "A-1001", "date": "2026-02-15", "weight": 65.2, "temp": 101.3, "heart_rate": 80, "resp_rate": 18, "notes": "Normal baseline"},
        {"animal_id": "A-1002", "date": "2026-02-18", "weight": 78.5, "temp": 101.8, "heart_rate": 90, "resp_rate": 22, "notes": "Slightly elevated HR, anxious"},
        {"animal_id": "A-1007", "date": "2026-02-25", "weight": 11.5, "temp": 102.5, "heart_rate": 180, "resp_rate": 30, "notes": "Elevated temp, pain response"},
        {"animal_id": "A-1004", "date": "2026-03-06", "weight": 72.0, "temp": 101.0, "heart_rate": 76, "resp_rate": 16, "notes": "Post-op, stable"},
    ]

    st.session_state.med_admin_log = [
        {"case_id": "MC-2001", "date": "2026-03-07", "time": "09:00", "medication": "Cephalexin 500mg",
         "dosage": "500mg", "method": "Oral", "administered_by": "Emily Torres", "notes": "Taken with food"},
        {"case_id": "MC-2001", "date": "2026-03-07", "time": "21:00", "medication": "Cephalexin 500mg",
         "dosage": "500mg", "method": "Oral", "administered_by": "Michael Brown", "notes": "Evening dose"},
        {"case_id": "MC-2002", "date": "2026-03-07", "time": "08:30", "medication": "Carprofen 75mg",
         "dosage": "75mg", "method": "Oral", "administered_by": "Emily Torres", "notes": "Given with breakfast"},
        {"case_id": "MC-2005", "date": "2026-03-07", "time": "10:00", "medication": "Meloxicam 1.5mg",
         "dosage": "1.5mg", "method": "Oral", "administered_by": "Michael Brown", "notes": "Standard dose"},
    ]

    st.session_state.diagnostic_results = [
        {"case_id": "MC-2001", "test": "Skin Scraping", "ordered": "2026-02-16", "status": "Completed",
         "result": "Bacterial infection confirmed - Staphylococcus", "ordered_by": "Dr. Sarah Chen"},
        {"case_id": "MC-2001", "test": "CBC Panel", "ordered": "2026-02-16", "status": "Completed",
         "result": "WBC slightly elevated, consistent with infection", "ordered_by": "Dr. Sarah Chen"},
        {"case_id": "MC-2002", "test": "Hip X-Ray (bilateral)", "ordered": "2026-02-19", "status": "Completed",
         "result": "Moderate bilateral hip dysplasia confirmed", "ordered_by": "Dr. James Wilson"},
        {"case_id": "MC-2005", "test": "Forelimb X-Ray", "ordered": "2026-02-26", "status": "Completed",
         "result": "Simple transverse fracture, left radius", "ordered_by": "Dr. James Wilson"},
        {"case_id": "MC-2005", "test": "Follow-up X-Ray", "ordered": "2026-03-08", "status": "Pending",
         "result": None, "ordered_by": "Dr. James Wilson"},
    ]

    st.session_state.next_ids = {
        "animal": 1011, "case": 2007, "task": 20, "invoice": 3004,
        "message": 3, "controlled": 6, "appointment": 3, "po": 404,
        "vitals": 5, "med_admin": 5, "diagnostic": 6,
    }

    st.session_state.data_init = True


def get_next_id(entity):
    current = st.session_state.next_ids[entity]
    st.session_state.next_ids[entity] = current + 1
    return current
