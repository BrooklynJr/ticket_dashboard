import streamlit as st
import pandas as pd
import os
import shutil
import plotly.express as px
from datetime import datetime

from PIL import Image
# ============ CSS STYLE ==============
st.markdown("""
<style>
/* background หลัก */
body {
    background-color: #f5f7fa;
}

/* กล่อง AI */
.ai-box {
    background-color: #0a8f3c;
    padding: 20px;
    border-radius: 12px;
    color: white;
}

/* กล่องปกติ */
.card {
    background-color: #ffffff;
    padding: 15px;
    border-radius: 10px;
    border: 1px solid #eee;
    margin-bottom: 10px;
}

/* SLA Critical */
.danger {
    background-color: #d90429;
    color: white;
    padding: 10px;
    border-radius: 8px;
}

/* Warning */
.warning {
    background-color: #ffba08;
    padding: 10px;
    border-radius: 8px;
}

/* Suggestion */
.success {
    background-color: #2a9d8f;
    color: white;
    padding: 10px;
    border-radius: 8px;
}
</style>
""", unsafe_allow_html=True)

# =========== HEADER ==============
col1, col2 = st.columns([1, 6])

with col1:
    st.image("assets/PTG_logo.png", width=80)

with col2:
    st.markdown("""
    <h2 style='margin-bottom:0;color:#0a8f3c;'>
    🧠 ระบบวิเคราะห์ Ticket อัตโนมัติ
    </h2>
    <p style='margin-top:0;color:gray;'>
    วิเคราะห์สถานการณ์ • แจ้งเตือน • แนะนำการแก้ไข
    </p>
    """, unsafe_allow_html=True)

st.divider()

# ============ END HEADER ==============

st.markdown("""
<div style="
    background-color:#0a8f3c;
    padding:20px;
    border-radius:12px;
    color:white;
    margin-bottom:20px;
">
<h3>🧠 AI วิเคราะห์ล่าสุด</h3>
<p>ระบบประเมินสถานการณ์ Ticket จากข้อมูลล่าสุด</p>
</div>
""", unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)
# LOGO =================

st.set_page_config(page_title="Ticket Dashboard", layout="wide")

st.subheader("📊 Ticket Analysis")

# ===== Upload CSV =====
uploaded_file = st.file_uploader("Upload new ticket CSV", type=["csv"])

# ===== BEFORE UPLOAD (หน้า Preview) =====
if uploaded_file is None:

    st.info("📂 อัปโหลดไฟล์ Ticket (CSV) เพื่อเริ่มวิเคราะห์ข้อมูลอัตโนมัติ")

    st.markdown("""
    ### 🔍 ระบบนี้ช่วยอะไรคุณ?

    - วิเคราะห์ Ticket อัตโนมัติ
    - แจ้งเตือนความเสี่ยง SLA
    - สรุปปัญหาที่พบบ่อย
    - แนะนำแนวทางแก้ไข
    """)

    st.markdown("""
    <div class="ai-box">
    <h3>🧠 ตัวอย่างการวิเคราะห์</h3>
    <ul>
    <li>📊 ปริมาณ Ticket เพิ่มขึ้น 25%</li>
    <li>⚠️ Ticket ระดับ High เพิ่มขึ้น</li>
    <li>🚨 มี Ticket เกิน SLA</li>
    <li>💡 แนะนำเพิ่มเจ้าหน้าที่ในช่วงเวลา Peak</li>
    </ul>
    </div>
    """, unsafe_allow_html=True)

    st.stop()  # ❗ หยุดตรงนี้ ไม่ให้ code ด้านล่างรัน

# ===== AFTER UPLOAD (Dashboard จริง) =====
df = pd.read_csv(uploaded_file)

# backup (optional)
archive_dir = "data/archive/"
os.makedirs(archive_dir, exist_ok=True)
timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
backup_file = os.path.join(archive_dir, f"tickets_{timestamp}.csv")

with open(backup_file, "wb") as f:
    f.write(uploaded_file.getbuffer())

st.success("✅ CSV uploaded successfully!")

# ===== Clean columns =====
df.columns = df.columns.str.strip().str.lower()

# ===== Column mapping =====
column_map = {
    'id':'ticket_id',
    'created':'created_date',
    'time closed':'resolved_date',
    'priority':'priority',
    'สถานะ':'status',
    'หมวดหมู่3':'issue'
}
existing_map = {k:v for k,v in column_map.items() if k in df.columns}
df.rename(columns=existing_map, inplace=True)
df['created_date'] = pd.to_datetime(df['created_date'], errors='coerce')
df['resolved_date'] = pd.to_datetime(df['resolved_date'], errors='coerce')

st.write("Columns:", df.columns.tolist())
st.dataframe(df.head())

# ===== Branch Analysis 🔥 =====
st.subheader("🏢 Branch Analysis")

if 'branch_name' in df.columns:
    # ใช้ filtered_df ถ้าอยาก filter ตาม priority/status
    branch_counts = df['branch_name'].value_counts().reset_index()
    branch_counts.columns = ['Branch', 'Ticket Count']
    
    st.write("Top Branches:")
    st.dataframe(branch_counts.head(10))  # แสดง Top 10
    
    # Horizontal Bar Chart ด้วย Plotly
    fig = px.bar(
        branch_counts.head(20),  # Top 20 branch
        x='Ticket Count',
        y='Branch',
        orientation='h',
        text='Ticket Count',
        labels={'Ticket Count':'Tickets','Branch':'Branch Name'},
        height=600  # ปรับสูงสุด
    )
    fig.update_layout(yaxis={'categoryorder':'total ascending'})  # เรียงจากเยอะไปน้อย
    st.plotly_chart(fig, use_container_width=True)
    
else:
    st.warning("No 'branch_name' column found")

# ===== AI INSIGHT PANEL (LAYOUT ใหม่) =====

st.markdown("## 🧠 AI วิเคราะห์สถานการณ์")

# --- เตรียมตัวแปร ---
total_tickets = len(df)
high_count = 0

# --- Top issue ---
top_issue = None
top_issue_count = 0
if 'issue' in df.columns and not df['issue'].dropna().empty:
    top_issue = df['issue'].value_counts().idxmax()
    top_issue_count = df['issue'].value_counts().max()

# --- High priority ---
if 'priority' in df.columns:
    high_count = df[df['priority'].astype(str).str.lower() == 'high'].shape[0]

# --- SLA ---
over_sla_count = 0
if 'resolved_date' in df.columns and 'created_date' in df.columns:
    df_valid = df.dropna(subset=['created_date', 'resolved_date']).copy()
    if not df_valid.empty:
        df_valid['resolution_time'] = (
            df_valid['resolved_date'] - df_valid['created_date']
        ).dt.total_seconds() / 3600
        over_sla_count = df_valid[df_valid['resolution_time'] > 4].shape[0]

# =========================
# 🔴 1. HERO: SLA CRITICAL
# =========================
if over_sla_count > 0:
    st.markdown(f"""
    <div style="
        background-color:#d90429;
        padding:20px;
        border-radius:12px;
        color:white;
        font-size:18px;
        font-weight:bold;
        margin-bottom:15px;
    ">
    🚨 มี Ticket เกิน SLA จำนวน {over_sla_count} รายการ
    </div>
    """, unsafe_allow_html=True)

# =========================
# ⚠️ 2. WARNING
# =========================
if total_tickets > 0 and high_count > total_tickets * 0.3:
    st.markdown(f"""
    <div style="
        background-color:#ffba08;
        padding:15px;
        border-radius:10px;
        margin-bottom:10px;
    ">
    ⚠️ Ticket ระดับ High มีจำนวนสูง ({high_count} รายการ)
    </div>
    """, unsafe_allow_html=True)

# =========================
# 📊 3. INFO (2 COLUMN)
# =========================
col1, col2 = st.columns(2)

with col1:
    st.markdown(f"""
    <div style="
        background-color:#ffffff;
        padding:15px;
        border-radius:10px;
        border:1px solid #eee;
        margin-bottom:10px;
    ">
    📊 จำนวน Ticket ทั้งหมด: {total_tickets}
    </div>
    """, unsafe_allow_html=True)

    if top_issue:
        st.markdown(f"""
        <div style="
            background-color:#ffffff;
            padding:15px;
            border-radius:10px;
            border:1px solid #eee;
        ">
        🔎 ปัญหาที่พบบ่อย: {top_issue} ({top_issue_count})
        </div>
        """, unsafe_allow_html=True)

with col2:
    if 'created_date' in df.columns:
        df_valid = df.dropna(subset=['created_date']).copy()
        if not df_valid.empty:
            df_valid['hour'] = df_valid['created_date'].dt.hour
            peak_hour = df_valid['hour'].value_counts().idxmax()

            st.markdown(f"""
            <div style="
                background-color:#ffffff;
                padding:15px;
                border-radius:10px;
                border:1px solid #eee;
                margin-bottom:10px;
            ">
            ⏰ ช่วงเวลาที่มี Ticket มากที่สุด: {int(peak_hour)}:00 น.
            </div>
            """, unsafe_allow_html=True)

# =========================
# 💡 4. RECOMMENDATION
# =========================
if high_count > 5:
    st.markdown("""
    <div style="
        background-color:#2a9d8f;
        padding:15px;
        border-radius:10px;
        color:white;
        margin-top:10px;
    ">
    💡 แนะนำ: ควรเพิ่มเจ้าหน้าที่หรือจัดลำดับงานสำหรับ Ticket ระดับ High
    </div>
    """, unsafe_allow_html=True)
       
# 👇 
if 'priority' not in df.columns or 'status' not in df.columns:
    st.error("❌ CSV missing required columns: priority / status")
    st.stop()

# ===== แปลง datetime ===== ใช้ errors='coerce' → แปลงไม่ได้จะกลายเป็น NaT
df['created_date'] = pd.to_datetime(df['created_date'], errors='coerce')
df['resolved_date'] = pd.to_datetime(df['resolved_date'], errors='coerce')

# ===== METRICS =====
st.subheader("📊 Overview")

col1, col2 = st.columns(2)

with col1:
    st.metric("Total Tickets", len(df))

with col2:
    if 'hour' in df.columns:
        peak_hour = df.groupby('hour').size().idxmax()
        st.metric("Peak Hour", f"{peak_hour}:00")

# ===== FILTER =====
col1, col2 = st.columns(2)

with col1:
    priorities = df['priority'].unique().tolist()
    selected_priority = st.multiselect("Select Priority", priorities, default=priorities)

with col2:
    statuses = df['status'].unique().tolist()
    selected_status = st.multiselect("Select Status", statuses, default=statuses)

filtered_df = df[
    (df['priority'].isin(selected_priority)) &
    (df['status'].isin(selected_status))
]

st.write(f"Showing {len(filtered_df)} tickets after filter")
filtered_df.index = filtered_df.index + 1  # เพิ่ม 1 ให้เริ่มจาก 1
st.dataframe(filtered_df)


# ===== TICKET TREND =====
st.subheader("📈 Ticket Trend Over Time")
filtered_df['month'] = filtered_df['created_date'].dt.to_period('M')
trend = filtered_df.groupby('month').size().reset_index(name='ticket_count')
trend['month'] = trend['month'].astype(str)

st.bar_chart(trend.set_index('month')['ticket_count'])

# ===== RECURRING ISSUES =====
st.subheader("🔁 Top Issues")

text_col = None
for col in df.columns:
    if "issue" in col or "description" in col or "summary" in col:
        text_col = col

if text_col:
    st.write(df[text_col].value_counts().head(5))
else:
    st.warning("No issue column found")


# ===== SPIKE DETECTION =====
st.subheader("⚠️ Spike Detection")

# แปลง created_date เป็น datetime
df['created_date'] = pd.to_datetime(df['created_date'], errors='coerce')
df = df.dropna(subset=['created_date'])

# สร้าง column 'hour' จาก created_date
df['hour'] = df['created_date'].dt.hour

# นับ ticket ต่อวัน
daily = df.groupby(df['created_date'].dt.date).size()
avg = daily.mean()
spikes = daily[daily > avg * 1.5]
st.write(spikes)

# ===== SLA RISK / AUTO INSIGHT =====
st.subheader("⏱ SLA Risk / Auto Insight")

# แปลง datetime 
filtered_df['created_date'] = pd.to_datetime(filtered_df['created_date'], errors='coerce')
filtered_df['resolved_date'] = pd.to_datetime(filtered_df['resolved_date'], errors='coerce')

# กรอง row ที่ datetime valid
valid_tickets = filtered_df.dropna(subset=['created_date','resolved_date'])

# คำนวณ resolution_hours
valid_tickets['resolution_hours'] = (valid_tickets['resolved_date'] - valid_tickets['created_date']).dt.total_seconds()/3600

# SLA threshold
sla_hours = 48
sla_risk = valid_tickets[valid_tickets['resolution_hours'] > sla_hours]
sla_count = len(sla_risk)

st.markdown(f"**<span style='color:red'>{sla_count} tickets over SLA ({sla_hours} hours)</span>**", unsafe_allow_html=True)
# แก้ table SLA Risk ให้ index เริ่มจาก 1
sla_table = sla_risk[['ticket_id','priority','status','resolution_hours']].reset_index(drop=True)
sla_table.index = sla_table.index + 1  # เพิ่ม 1 ให้เริ่มจาก 1
st.dataframe(sla_table)

# ===== PROXY IMPACT =====
impact_map = {'High': 5, 'Medium': 3, 'Low': 1}
sla_risk['impact_score'] = sla_risk['priority'].map(impact_map)
total_score = sla_risk['impact_score'].sum()

# ===== IMPACT BAR CHART =====
impact_summary = sla_risk.groupby('priority').agg(
    tickets_delayed=('ticket_id','count'),
    total_impact=('impact_score','sum')
).reset_index()
