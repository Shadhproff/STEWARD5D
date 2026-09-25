import streamlit as st
import mysql.connector
from mysql.connector import Error

# ==================================================
# PAGE SETTINGS
# ==================================================
st.set_page_config(
    page_title="Steward5D",
    page_icon="🦠",
    layout="centered"
)


# ==================================================
# DATABASE CONFIGURATION
# ==================================================
DB_HOST = st.secrets["mysql"]["host"]
DB_USER = st.secrets["mysql"]["user"]
DB_PASSWORD = st.secrets["mysql"]["password"]
DB_NAME = st.secrets["mysql"]["database"]
DB_PORT = int(st.secrets["mysql"]["port"])


def get_db_connection():
    """Establishes connection to the Clever Cloud MySQL database."""
    try:
        connection = mysql.connector.connect(
            host=DB_HOST,
            user=DB_USER,
            password=DB_PASSWORD,
            database=DB_NAME,
            port=DB_PORT
        )
        return connection
    except Error as e:
        st.error(f"⚠️ Database Connection Error: {e}")
        return None


def init_db():
    """Creates the student_attempts table if it does not already exist."""
    conn = get_db_connection()
    if conn and conn.is_connected():
        try:
            cursor = conn.cursor()
            create_table_query = """
            CREATE TABLE IF NOT EXISTS student_attempts (
                id INT AUTO_INCREMENT PRIMARY KEY,
                User_ID VARCHAR(255) DEFAULT 'Anonymous',
                case_name VARCHAR(100) NOT NULL,
                attempt_number INT NOT NULL,
                total_score INT NOT NULL,
                diagnosis_score INT,
                drug_score INT,
                dose_score INT,
                duration_score INT,
                deescalation_score INT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            """
            cursor.execute(create_table_query)
            conn.commit()
            cursor.close()
            conn.close()
        except Error as e:
            st.error(f"⚠️ Table Initialization Error: {e}")


def log_attempt_to_db(user_id, case_name, attempt_number, total_score, scores):
    """Inserts a single attempt record into the database."""
    conn = get_db_connection()
    if conn and conn.is_connected():
        try:
            cursor = conn.cursor()
            insert_query = """
            INSERT INTO student_attempts 
            (User_ID, case_name, attempt_number, total_score, diagnosis_score, drug_score, dose_score, duration_score, deescalation_score)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s);
            """
            data_tuple = (
                user_id if user_id else "Anonymous",
                case_name,
                attempt_number,
                total_score,
                scores.get("Diagnosis", 0),
                scores.get("Drug", 0),
                scores.get("Dose", 0),
                scores.get("Duration", 0),
                scores.get("De-escalation", 0)
            )
            cursor.execute(insert_query, data_tuple)
            conn.commit()
            cursor.close()
            conn.close()
        except Error as e:
            st.error(f"⚠️ Failed to log record to database: {e}")


# Initialize database table on app start
init_db()


# ==================================================
# INITIALIZE SESSION STATE
# ==================================================
if "submitted" not in st.session_state:
    st.session_state["submitted"] = False
if "attempt" not in st.session_state:
    st.session_state["attempt"] = 1
if "first_score" not in st.session_state:
    st.session_state["first_score"] = None
if "retry_score" not in st.session_state:
    st.session_state["retry_score"] = None
if "current_case" not in st.session_state:
    st.session_state["current_case"] = "Acute Sore Throat"


# Helper function to reset state when switching cases or starting fresh
def reset_case_state():
    st.session_state["submitted"] = False
    st.session_state["attempt"] = 1
    st.session_state["first_score"] = None
    st.session_state["retry_score"] = None
    st.session_state.pop("scores", None)
    st.session_state.pop("total_score", None)


# ==================================================
# SIDEBAR CONTROL PANEL
# ==================================================
with st.sidebar:
    st.header("⚙️ Simulator Controls")
    st.write("Use this panel to manage your session or start over.")
    
    if st.button("🔄 Reset Simulator / New User", use_container_width=True):
        reset_case_state()
        st.rerun()

    st.divider()
    st.caption("Steward5D Simulator v1.0")


# ==================================================
# TITLE & HEADER
# ==================================================
st.title("🦠 Steward5D")

st.subheader(
    "An Interactive Simulator for Practising "
    "Antimicrobial Stewardship Decisions"
)

st.write(
    "Work through five antimicrobial stewardship decisions: "
    "Diagnosis, Drug, Dose, Duration and De-escalation."
)


# ==================================================
# TRAINING NOTICE & USER IDENTIFICATION
# ==================================================
st.warning(
    "Educational use only. This simulator is designed "
    "for antimicrobial stewardship learning and is not "
    "a substitute for professional medical advice."
)

user_id = st.text_input(
    "👤 Enter your User ID / Student ID (Optional):", 
    placeholder="e.g. ST12345 / User 1"
)


# ==================================================
# SCORING FUNCTION
# ==================================================
def calculate_score(user_answers, correct_answers):
    scores = {}
    for dimension in correct_answers:
        if user_answers[dimension] == correct_answers[dimension]:
            scores[dimension] = 1
        else:
            scores[dimension] = 0
    return scores


# ==================================================
# CASE SELECTION & AUTOMATIC STATE RESET
# ==================================================
st.header("Choose a Case")

selected_case = st.selectbox(
    "Select the clinical scenario you want to practise:",
    [
        "Acute Sore Throat",
        "Uncomplicated Lower UTI"
    ],
    key="case_selector"
)

# Detect if the user changed the selected case and reset case-level states
if selected_case != st.session_state["current_case"]:
    st.session_state["current_case"] = selected_case
    reset_case_state()
    st.rerun()

case = st.session_state["current_case"]


# ==================================================
# CASE 1 — ACUTE SORE THROAT
# ==================================================
if case == "Acute Sore Throat":

    st.header("Case 1: Acute Sore Throat")
    st.info(f"📍 **Current Stage:** Attempt #{st.session_state['attempt']}")

    st.write(
        """
        A patient presents with an acute sore throat and symptoms 
        consistent with a self-limiting upper respiratory infection.

        Based on the information provided, work through the five 
        antimicrobial stewardship decisions below.
        """
    )

    st.divider()

    correct_answers = {
        "Diagnosis": "Viral upper respiratory infection",
        "Drug": "No antibiotic is indicated",
        "Dose": "No antibiotic dose is required",
        "Duration": "No antibiotic course is required",
        "De-escalation": (
            "Withhold antibiotics and reassess if the patient's "
            "condition changes"
        )
    }

    feedback_rationale = {
        "Diagnosis": (
            "Most acute sore throats are viral in etiology and self-limiting."
        ),
        "Drug": (
            "Antibiotics offer minimal benefit for uncomplicated viral sore throats "
            "and contribute to antimicrobial resistance."
        ),
        "Dose": (
            "Since no antibiotic treatment is indicated, no dose should be prescribed."
        ),
        "Duration": (
            "No course of antimicrobial therapy is necessary."
        ),
        "De-escalation": (
            "Withholding unnecessary therapy while advising the patient on symptoms "
            "to monitor is the key stewardship strategy here."
        )
    }

    # 1. DIAGNOSIS
    st.subheader("1️⃣ Diagnosis")
    diagnosis = st.radio(
        "What is the most appropriate diagnosis?",
        [
            "Viral upper respiratory infection",
            "Bacterial pneumonia",
            "Uncomplicated lower urinary tract infection",
            "Pyelonephritis"
        ],
        key=f"case1_diagnosis_att{st.session_state['attempt']}"
    )

    # 2. DRUG
    st.subheader("2️⃣ Drug")
    drug = st.radio(
        "What is the most appropriate antimicrobial approach?",
        [
            "No antibiotic is indicated",
            "Start a broad-spectrum antibiotic immediately",
            "Start two antibiotics simultaneously",
            "Use an antibiotic routinely for all sore throats"
        ],
        key=f"case1_drug_att{st.session_state['attempt']}"
    )

    # 3. DOSE
    st.subheader("3️⃣ Dose")
    dose = st.radio(
        "What is the appropriate antibiotic dose?",
        [
            "No antibiotic dose is required",
            "Use a high antibiotic dose routinely",
            "Use a low antibiotic dose routinely",
            "Double the usual antibiotic dose"
        ],
        key=f"case1_dose_att{st.session_state['attempt']}"
    )

    # 4. DURATION
    st.subheader("4️⃣ Duration")
    duration = st.radio(
        "What is the appropriate antibiotic duration?",
        [
            "No antibiotic course is required",
            "1 day of antibiotics",
            "14 days of antibiotics",
            "Continue antibiotics indefinitely"
        ],
        key=f"case1_duration_att{st.session_state['attempt']}"
    )

    # 5. DE-ESCALATION
    st.subheader("5️⃣ De-escalation")
    deescalation = st.radio(
        "What is the most appropriate stewardship action?",
        [
            "Withhold antibiotics and reassess if the patient's "
            "condition changes",
            "Start antibiotics immediately even if there is no "
            "evidence of bacterial infection",
            "Increase antibiotic exposure to prevent complications",
            "Continue antibiotics regardless of clinical changes"
        ],
        key=f"case1_deescalation_att{st.session_state['attempt']}"
    )

    user_answers = {
        "Diagnosis": diagnosis,
        "Drug": drug,
        "Dose": dose,
        "Duration": duration,
        "De-escalation": deescalation
    }

    st.divider()

    if st.button("Submit Case", type="primary"):
        scores = calculate_score(user_answers, correct_answers)
        total_score = sum(scores.values())

        if st.session_state["attempt"] == 1:
            st.session_state["first_score"] = total_score
        else:
            st.session_state["retry_score"] = total_score

        st.session_state["scores"] = scores
        st.session_state["total_score"] = total_score
        st.session_state["submitted"] = True

        # LOG TO CLEVER CLOUD MYSQL DATABASE
        log_attempt_to_db(user_id, "Acute Sore Throat", st.session_state["attempt"], total_score, scores)

    if st.session_state.get("submitted", False):
        st.divider()
        st.header(f"Results — Attempt #{st.session_state['attempt']}")

        total_score = st.session_state["total_score"]
        scores = st.session_state["scores"]

        col1, col2 = st.columns(2)
        with col1:
            st.metric("Attempt 1 Score", f"{st.session_state['first_score']} / 5")
        with col2:
            if st.session_state["retry_score"] is not None:
                delta = st.session_state["retry_score"] - st.session_state["first_score"]
                st.metric(
                    "Attempt 2 Score", 
                    f"{st.session_state['retry_score']} / 5", 
                    delta=f"{delta} pts" if delta != 0 else "No change"
                )
            else:
                st.metric("Attempt 2 Score", "Not taken yet")

        st.subheader("Feedback by Dimension")

        for dimension, score in scores.items():
            if score == 1:
                st.success(f"✅ **{dimension}**: Correct!")
                st.write(f"💡 *Rationale:* {feedback_rationale[dimension]}")
            else:
                st.error(f"❌ **{dimension}**: Needs Review")
                st.write(f"**Correct Answer:** {correct_answers[dimension]}")
                st.write(f"💡 *Rationale:* {feedback_rationale[dimension]}")
            st.write("---")

        if st.session_state["attempt"] == 1:
            st.subheader("🔄 Test Your Knowledge Improvement")
            st.write("Review your feedback above, then attempt the case a second time to see if you can reach 5/5!")
            if st.button("Retry Case (Attempt 2)"):
                st.session_state["attempt"] = 2
                st.session_state["submitted"] = False
                st.rerun()


# ==================================================
# CASE 2 — UNCOMPLICATED LOWER UTI
# ==================================================
elif case == "Uncomplicated Lower UTI":

    st.header("Case 2: Uncomplicated Lower UTI")
    st.info(f"📍 **Current Stage:** Attempt #{st.session_state['attempt']}")

    st.write(
        """
        A 32-year-old non-pregnant female presents with dysuria, frequency, and 
        urgency for 2 days. She has no systemic signs (no fever, no flank pain, 
        normal renal function). 

        Work through the five antimicrobial stewardship decisions below.
        """
    )

    st.divider()

    correct_answers_uti = {
        "Diagnosis": "Uncomplicated lower urinary tract infection (Cystitis)",
        "Drug": "Nitrofurantoin (or First-line local guideline agent)",
        "Dose": "100 mg BD (Modified Release)",
        "Duration": "5 days",
        "De-escalation": (
            "Complete targeted 5-day course without unnecessary extension or "
            "routine follow-up urine cultures if symptoms resolve"
        )
    }

    feedback_rationale_uti = {
        "Diagnosis": (
            "Classic acute dysuria, frequency, and urgency in a non-pregnant woman "
            "without systemic symptoms indicate uncomplicated lower UTI."
        ),
        "Drug": (
            "Nitrofurantoin is a recommended first-line narrow-spectrum empiric choice "
            "for uncomplicated lower UTI, preserving broad-spectrum agents like fluoroquinolones."
        ),
        "Dose": (
            "100 mg twice daily (modified release) is the standard therapeutic dose for "
            "uncomplicated lower UTI in patients with adequate renal function."
        ),
        "Duration": (
            "A short 5-day course of nitrofurantoin is clinically effective and minimizes "
            "adverse effects and resistance risks."
        ),
        "De-escalation": (
            "Stewardship dictates completing short-course targeted therapy and avoiding unnecessary "
            "broadening, treatment extensions, or post-treatment urine cultures when symptoms resolve."
        )
    }

    # 1. DIAGNOSIS
    st.subheader("1️⃣ Diagnosis")
    diagnosis_uti = st.radio(
        "What is the most appropriate diagnosis?",
        [
            "Uncomplicated lower urinary tract infection (Cystitis)",
            "Acute Pyelonephritis",
            "Asymptomatic Bacteriuria",
            "Pelvic Inflammatory Disease"
        ],
        key=f"case2_diagnosis_att{st.session_state['attempt']}"
    )

    # 2. DRUG
    st.subheader("2️⃣ Drug")
    drug_uti = st.radio(
        "What is the most appropriate first-line antimicrobial choice?",
        [
            "Nitrofurantoin (or First-line local guideline agent)",
            "Ciprofloxacin (Routine broad-spectrum fluoroquinolone)",
            "Cefuroxime (Broad-spectrum oral cephalosporin)",
            "No antibiotic treatment is indicated"
        ],
        key=f"case2_drug_att{st.session_state['attempt']}"
    )

    # 3. DOSE
    st.subheader("3️⃣ Dose")
    dose_uti = st.radio(
        "What is the correct dosing regimen for Nitrofurantoin MR?",
        [
            "100 mg BD (Modified Release)",
            "50 mg once daily",
            "100 mg QDS (4 times daily)",
            "200 mg BD"
        ],
        key=f"case2_dose_att{st.session_state['attempt']}"
    )

    # 4. DURATION
    st.subheader("4️⃣ Duration")
    duration_uti = st.radio(
        "What is the recommended treatment duration for Nitrofurantoin in acute lower UTI?",
        [
            "5 days",
            "1 day",
            "10 to 14 days",
            "21 days"
        ],
        key=f"case2_duration_att{st.session_state['attempt']}"
    )

    # 5. DE-ESCALATION
    st.subheader("5️⃣ De-escalation")
    deescalation_uti = st.radio(
        "What is the appropriate stewardship / de-escalation decision?",
        [
            "Complete targeted 5-day course without unnecessary extension or "
            "routine follow-up urine cultures if symptoms resolve",
            "Switch to intravenous broad-spectrum therapy upon clinical improvement",
            "Extend course to 14 days to prevent recurrence",
            "Repeat urine culture routinely post-treatment regardless of symptom resolution"
        ],
        key=f"case2_deescalation_att{st.session_state['attempt']}"
    )

    user_answers_uti = {
        "Diagnosis": diagnosis_uti,
        "Drug": drug_uti,
        "Dose": dose_uti,
        "Duration": duration_uti,
        "De-escalation": deescalation_uti
    }

    st.divider()

    if st.button("Submit Case", type="primary"):
        scores = calculate_score(user_answers_uti, correct_answers_uti)
        total_score = sum(scores.values())

        if st.session_state["attempt"] == 1:
            st.session_state["first_score"] = total_score
        else:
            st.session_state["retry_score"] = total_score

        st.session_state["scores"] = scores
        st.session_state["total_score"] = total_score
        st.session_state["submitted"] = True

        # LOG TO CLEVER CLOUD MYSQL DATABASE
        log_attempt_to_db(user_id, "Uncomplicated Lower UTI", st.session_state["attempt"], total_score, scores)

    if st.session_state.get("submitted", False):
        st.divider()
        st.header(f"Results — Attempt #{st.session_state['attempt']}")

        total_score = st.session_state["total_score"]
        scores = st.session_state["scores"]

        col1, col2 = st.columns(2)
        with col1:
            st.metric("Attempt 1 Score", f"{st.session_state['first_score']} / 5")
        with col2:
            if st.session_state["retry_score"] is not None:
                delta = st.session_state["retry_score"] - st.session_state["first_score"]
                st.metric(
                    "Attempt 2 Score", 
                    f"{st.session_state['retry_score']} / 5", 
                    delta=f"{delta} pts" if delta != 0 else "No change"
                )
            else:
                st.metric("Attempt 2 Score", "Not taken yet")

        st.subheader("Feedback by Dimension")

        for dimension, score in scores.items():
            if score == 1:
                st.success(f"✅ **{dimension}**: Correct!")
                st.write(f"💡 *Rationale:* {feedback_rationale_uti[dimension]}")
            else:
                st.error(f"❌ **{dimension}**: Needs Review")
                st.write(f"**Correct Answer:** {correct_answers_uti[dimension]}")
                st.write(f"💡 *Rationale:* {feedback_rationale_uti[dimension]}")
            st.write("---")

        if st.session_state["attempt"] == 1:
            st.subheader("🔄 Test Your Knowledge Improvement")
            st.write("Review your feedback above, then attempt the case a second time to see if you can reach 5/5!")
            if st.button("Retry Case (Attempt 2)"):
                st.session_state["attempt"] = 2
                st.session_state["submitted"] = False
                st.rerun()