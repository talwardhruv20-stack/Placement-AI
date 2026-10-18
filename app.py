import streamlit as st
import pandas as pd
import sqlite3
import plotly.express as px
from datetime import datetime
import google.generativeai as genai

# ==========================================
# PAGE CONFIGURATION & DARK THEME STYLING
# ==========================================
st.set_page_config(
    page_title="Intelligent Student Placement Management System", 
    page_icon="🎓", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Dark Theme CSS Styling
st.markdown("""
    <style>
    .main {
        background-color: #0e1117;
        color: #ffffff;
    }
    .stSidebar {
        background-color: #161b22;
    }
    div.stButton > button {
        background-color: #238636;
        color: white;
        border-radius: 6px;
        padding: 0.5rem 1rem;
        font-weight: 600;
        border: none;
    }
    div.stButton > button:hover {
        background-color: #2ea043;
    }
    </style>
""", unsafe_allow_html=True)

# ==========================================
# 1. DATABASE SETUP & INITIALIZATION
# ==========================================
def init_db():
    conn = sqlite3.connect("placement_system.db")
    cursor = conn.cursor()
    
    # Students Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS students (
            roll_no TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            department TEXT NOT NULL,
            batch TEXT NOT NULL,
            cgpa REAL NOT NULL,
            skills TEXT,
            eligibility_status TEXT DEFAULT 'Eligible',
            placement_status TEXT DEFAULT 'Unplaced'
        )
    ''')
    
    # Companies Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS companies (
            company_id INTEGER PRIMARY KEY AUTOINCREMENT,
            company_name TEXT NOT NULL,
            job_role TEXT NOT NULL,
            package_lpa REAL NOT NULL,
            visit_date TEXT
        )
    ''')
    
    # Placement Offers & History Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS placement_history (
            history_id INTEGER PRIMARY KEY AUTOINCREMENT,
            roll_no TEXT,
            company_name TEXT,
            job_role TEXT,
            package_lpa REAL,
            status TEXT,
            updated_at TEXT,
            FOREIGN KEY (roll_no) REFERENCES students (roll_no)
        )
    ''')
    
    conn.commit()
    conn.close()

init_db()

def get_connection():
    return sqlite3.connect("placement_system.db")

# ==========================================
# 2. APPLICATION NAVIGATION & HEADER
# ==========================================
st.title("🎓 Intelligent Student Placement Record Management System")
st.markdown("*Prompt Manthan - Round 2 | Technophilia 2K26*")
st.markdown("---")

menu = [
    "📊 Placement Dashboard", 
    "💡 AI Placement Assistant",
    "👨‍🎓 Student Management", 
    "🏢 Company & Offers", 
    "📜 History & Interview Log", 
    "📑 Reports & Data Export"
]
choice = st.sidebar.selectbox("Navigation Menu", menu)

# ==========================================
# REQUIREMENT 4: PLACEMENT DASHBOARD
# ==========================================
if choice == "📊 Placement Dashboard":
    st.header("📊 Placement Progress Dashboard")
    
    conn = get_connection()
    df_students = pd.read_sql_query("SELECT * FROM students", conn)
    conn.close()
    
    if df_students.empty:
        st.info("No student data available. Please add students or upload data in 'Student Management'.")
    else:
        total_students = len(df_students)
        placed_students = len(df_students[df_students['placement_status'] == 'Placed'])
        unplaced_students = len(df_students[df_students['placement_status'] == 'Unplaced'])
        in_process = len(df_students[df_students['placement_status'] == 'In Process'])
        not_eligible = len(df_students[df_students['placement_status'] == 'Not Eligible'])
        
        placement_pct = (placed_students / total_students * 100) if total_students > 0 else 0
        
        # Metric Cards
        col1, col2, col3, col4, col5 = st.columns(5)
        col1.metric("Total Students", total_students)
        col2.metric("Placed Students", placed_students, delta=f"{placement_pct:.1f}%")
        col3.metric("Unplaced Students", unplaced_students)
        col4.metric("In Process", in_process)
        col5.metric("Not Eligible", not_eligible)
        
        st.markdown("---")
        
        c1, c2 = st.columns(2)
        with c1:
            st.subheader("Placement Breakdown")
            fig_pie = px.pie(
                df_students, 
                names='placement_status', 
                title="Overall Status Distribution",
                color='placement_status',
                color_discrete_map={
                    'Placed': '#2ecc71',
                    'Unplaced': '#e74c3c',
                    'In Process': '#f1c40f',
                    'Not Eligible': '#95a5a6'
                },
                template="plotly_dark"
            )
            st.plotly_chart(fig_pie, use_container_width=True)
            
        with c2:
            st.subheader("Department-wise Placement Analysis")
            dept_stats = df_students.groupby(['department', 'placement_status']).size().reset_index(name='Count')
            fig_bar = px.bar(
                dept_stats, 
                x='department', 
                y='Count', 
                color='placement_status', 
                barmode='group',
                title="Status by Department",
                template="plotly_dark"
            )
            st.plotly_chart(fig_bar, use_container_width=True)

# ==========================================
# AI INTEGRATION: GEMINI PROMPT ASSISTANT
# ==========================================
elif choice == "💡 AI Placement Assistant":
    st.header("💡 AI-Powered Placement Assistant (Gemini API)")
    st.markdown("Query records in plain text, shortlist candidates for specific job roles, or draft company emails using AI.")
    
    api_key = st.text_input("Enter Google Gemini API Key", type="password", help="Enter your Gemini API key to activate AI features.")
    
    if api_key:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        conn = get_connection()
        df_students = pd.read_sql_query("SELECT * FROM students", conn)
        df_companies = pd.read_sql_query("SELECT * FROM companies", conn)
        conn.close()
        
        tab_ai1, tab_ai2 = st.tabs(["🤖 Natural Language Query", "✉️ AI Email & Communication Generator"])
        
        with tab_ai1:
            st.subheader("Ask Anything About Student & Placement Records")
            user_prompt = st.text_area(
                "Enter Prompt", 
                value="Find all eligible unplaced students with CGPA above 8.0 who know Python and recommend them for an AI Developer role.",
                height=100
            )
            
            if st.button("Run AI Prompt"):
                if not df_students.empty:
                    with st.spinner("Analyzing database with Gemini..."):
                        system_context = f"""
                        You are an expert AI Placement Officer Assistant at a university.
                        Here is the current live student dataset in CSV format:
                        {df_students.to_csv(index=False)}
                        
                        Here is the registered company dataset in CSV format:
                        {df_companies.to_csv(index=False)}
                        
                        User Request: {user_prompt}
                        
                        Respond professionally, accurately, and present data cleanly in tables or structured bullet points where applicable.
                        """
                        response = model.generate_content(system_context)
                        st.markdown("### AI Output:")
                        st.markdown(response.text)
                else:
                    st.warning("Please upload student data first.")
                    
        with tab_ai2:
            st.subheader("Generate Targeted Emails")
            email_type = st.selectbox("Select Email Goal", [
                "Invite Students to Upcoming Drive",
                "Congratulate Placed Student",
                "Placement Update Report to College Management"
            ])
            target_company = st.text_input("Company Name (if applicable)", "Google")
            
            if st.button("Draft Email with Gemini"):
                with st.spinner("Drafting professional email..."):
                    prompt = f"Draft a professional email for a university placement cell with the goal: '{email_type}'. Company: '{target_company}'. Keep the tone clear and formal."
                    response = model.generate_content(prompt)
                    st.text_area("Generated Email Draft", value=response.text, height=250)
    else:
        st.info("👈 Enter your Gemini API key above to unlock AI query and generation capabilities.")

# ==========================================
# REQUIREMENT 1 & 2: STUDENT MANAGEMENT
# ==========================================
elif choice == "👨‍🎓 Student Management":
    st.header("👨‍🎓 Student Record Management & Status Tracking")
    
    tab1, tab2, tab3 = st.tabs(["Add / Update Student", "Bulk CSV Upload", "View All Students"])
    
    with tab1:
        st.subheader("Add or Modify Student Details")
        with st.form("student_form"):
            roll_no = st.text_input("Roll Number")
            name = st.text_input("Full Name")
            dept = st.selectbox("Department", ["CSE", "AIML", "IT", "ECE", "ME", "BCA", "MCA"])
            batch = st.text_input("Batch Year", "2023-2027")
            cgpa = st.number_input("CGPA", min_value=0.0, max_value=10.0, value=7.5, step=0.1)
            skills = st.text_input("Key Skills (comma-separated)", "Python, SQL, Web Dev")
            eligibility = st.selectbox("Eligibility Status", ["Eligible", "Not Eligible"])
            status = st.selectbox("Placement Status", ["Unplaced", "Placed", "In Process", "Not Eligible"])
            
            submitted = st.form_submit_button("Save Student Record")
            
            if submitted:
                if roll_no and name:
                    conn = get_connection()
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO students (roll_no, name, department, batch, cgpa, skills, eligibility_status, placement_status)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                        ON CONFLICT(roll_no) DO UPDATE SET
                            name=excluded.name,
                            department=excluded.department,
                            batch=excluded.batch,
                            cgpa=excluded.cgpa,
                            skills=excluded.skills,
                            eligibility_status=excluded.eligibility_status,
                            placement_status=excluded.placement_status
                    ''', (roll_no, name, dept, batch, cgpa, skills, eligibility, status))
                    conn.commit()
                    conn.close()
                    st.success(f"Record successfully saved for {name} ({roll_no})!")
                else:
                    st.error("Please enter Roll Number and Name.")

    with tab2:
        st.subheader("Bulk Upload Student Records (CSV)")
        uploaded_file = st.file_uploader("Upload CSV", type=["csv"])
        if uploaded_file is not None:
            df_upload = pd.read_csv(uploaded_file)
            st.write("Preview:", df_upload.head())
            if st.button("Confirm Bulk Import"):
                try:
                    # Clean column names to prevent KeyError
                    df_upload.columns = df_upload.columns.str.strip().str.lower()
                    
                    conn = get_connection()
                    for _, row in df_upload.iterrows():
                        conn.execute('''
                            INSERT OR REPLACE INTO students (roll_no, name, department, batch, cgpa, skills, eligibility_status, placement_status)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                        ''', (
                            str(row.get('roll_no', row.get('roll no', 'N/A'))), 
                            str(row.get('name', row.get('student name', 'Unknown'))), 
                            str(row.get('department', row.get('dept', 'CSE'))), 
                            str(row.get('batch', '2023-2027')), 
                            float(row.get('cgpa', 7.0)), 
                            str(row.get('skills', '')), 
                            str(row.get('eligibility_status', 'Eligible')), 
                            str(row.get('placement_status', 'Unplaced'))
                        ))
                    conn.commit()
                    conn.close()
                    st.success("Bulk dataset imported successfully!")
                except Exception as e:
                    st.error(f"Error importing CSV: {e}")

    with tab3:
        st.subheader("Student Database")
        conn = get_connection()
        df_students = pd.read_sql_query("SELECT * FROM students", conn)
        conn.close()
        st.dataframe(df_students, use_container_width=True)

# ==========================================
# REQUIREMENT 3: COMPANY & OFFER RECORDS
# ==========================================
elif choice == "🏢 Company & Offers":
    st.header("🏢 Company & Offer Management")
    
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.subheader("Register Visiting Company")
        with st.form("company_form"):
            c_name = st.text_input("Company Name")
            c_role = st.text_input("Job Role Offered")
            c_package = st.number_input("Package (LPA)", min_value=0.0, step=0.5)
            c_date = st.date_input("Drive / Visit Date")
            
            c_submit = st.form_submit_button("Register Company")
            if c_submit and c_name:
                conn = get_connection()
                cursor = conn.cursor()
                cursor.execute("INSERT INTO companies (company_name, job_role, package_lpa, visit_date) VALUES (?, ?, ?, ?)",
                               (c_name, c_role, c_package, str(c_date)))
                conn.commit()
                conn.close()
                st.success(f"Registered {c_name} for role {c_role}.")

    with col2:
        st.subheader("Record Job Offer / Selection")
        conn = get_connection()
        df_studs = pd.read_sql_query("SELECT roll_no, name FROM students WHERE eligibility_status='Eligible'", conn)
        df_comps = pd.read_sql_query("SELECT company_id, company_name, job_role, package_lpa FROM companies", conn)
        conn.close()
        
        if not df_studs.empty and not df_comps.empty:
            with st.form("offer_form"):
                student_choice = st.selectbox("Select Student", df_studs['roll_no'] + " - " + df_studs['name'])
                selected_roll = student_choice.split(" - ")[0]
                
                company_options = df_comps.apply(lambda x: f"{x['company_name']} ({x['job_role']} @ {x['package_lpa']} LPA)", axis=1)
                comp_choice_idx = st.selectbox("Select Company Drive", range(len(company_options)), format_func=lambda x: company_options[x])
                
                sel_company = df_comps.iloc[comp_choice_idx]
                offer_status = st.selectbox("Outcome Status", ["Placed", "In Process", "Rejected"])
                
                offer_submit = st.form_submit_button("Log Selection Record")
                if offer_submit:
                    conn = get_connection()
                    cursor = conn.cursor()
                    
                    if offer_status == "Placed":
                        cursor.execute("UPDATE students SET placement_status='Placed' WHERE roll_no=?", (selected_roll,))
                    elif offer_status == "In Process":
                        cursor.execute("UPDATE students SET placement_status='In Process' WHERE roll_no=?", (selected_roll,))
                    
                    cursor.execute('''
                        INSERT INTO placement_history (roll_no, company_name, job_role, package_lpa, status, updated_at)
                        VALUES (?, ?, ?, ?, ?, ?)
                    ''', (selected_roll, sel_company['company_name'], sel_company['job_role'], sel_company['package_lpa'], offer_status, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
                    
                    conn.commit()
                    conn.close()
                    st.success("Placement outcome updated and logged successfully!")

# ==========================================
# REQUIREMENT 5: PLACEMENT HISTORY & UPDATES
# ==========================================
elif choice == "📜 History & Interview Log":
    st.header("📜 Placement History & Update Audit Trail")
    
    conn = get_connection()
    df_history = pd.read_sql_query('''
        SELECT h.history_id, h.roll_no, s.name, s.department, h.company_name, h.job_role, h.package_lpa, h.status, h.updated_at 
        FROM placement_history h
        JOIN students s ON h.roll_no = s.roll_no
        ORDER BY h.updated_at DESC
    ''', conn)
    conn.close()
    
    if df_history.empty:
        st.info("No placement activity history logged yet.")
    else:
        st.dataframe(df_history, use_container_width=True)

# ==========================================
# REQUIREMENT 6: REPORTS & DATA EXPORT
# ==========================================
elif choice == "📑 Reports & Data Export":
    st.header("📑 Reports & Data Export")
    
    conn = get_connection()
    df_all = pd.read_sql_query("SELECT * FROM students", conn)
    conn.close()
    
    st.subheader("Filter Custom Placement Reports")
    c1, c2, c3 = st.columns(3)
    
    with c1:
        filter_dept = st.multiselect("Filter Department", options=df_all['department'].unique(), default=df_all['department'].unique())
    with c2:
        filter_status = st.multiselect("Filter Placement Status", options=df_all['placement_status'].unique(), default=df_all['placement_status'].unique())
    with c3:
        filter_batch = st.multiselect("Filter Batch", options=df_all['batch'].unique(), default=df_all['batch'].unique())
        
    filtered_df = df_all[
        (df_all['department'].isin(filter_dept)) &
        (df_all['placement_status'].isin(filter_status)) &
        (df_all['batch'].isin(filter_batch))
    ]
    
    st.write(f"Showing **{len(filtered_df)}** matching records:")
    st.dataframe(filtered_df, use_container_width=True)
    
    st.markdown("### Export Report Data")
    col_exp1, col_exp2 = st.columns(2)
    
    with col_exp1:
        csv_data = filtered_df.to_csv(index=False).encode('utf-8')
        st.download_button("📥 Download Report as CSV", data=csv_data, file_name="placement_report.csv", mime="text/csv")
