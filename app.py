import streamlit as st
import pandas as pd
import os
import shutil
from datetime import datetime

st.set_page_config(page_title="Ticket Dashboard", layout="wide")


# ===== LOAD DATA =====
@st.cache_data
def load_data():
    df = pd.read_csv(
        "data/tickets.csv",
        sep=None,
        engine='python',
        on_bad_lines='skip',
        encoding_errors='ignore'
    )

    df.columns = df.columns.str.strip().str.lower().str.replace(" ", "_")

    # detect created column
    created_col = None
    for col in df.columns:
        if "create" in col or "open" in col:
            created_col = col

    if created_col:
        df[created_col] = pd.to_datetime(df[created_col], errors='coerce')
        df['hour'] = df[created_col].dt.hour
        df = df.dropna(subset=['hour'])
        df['hour'] = df['hour'].astype(int)

    return df


df = load_data()

st.title("🔥 Ticket Trend Dashboard")

# ให้ทีมอัปโหลดไฟล์ใหม่เอง
uploaded_file = st.file_uploader("Upload new ticket CSV", type=["csv"])
if uploaded_file:
    df = pd.read_csv(uploaded_file)

    # ===== Save backup only ตอน upload =====
    archive_dir = "data/archive/"
    os.makedirs(archive_dir, exist_ok=True)
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    backup_file = os.path.join(archive_dir, f"tickets_{timestamp}.csv")
    with open(backup_file, "wb") as f:
        f.write(uploaded_file.getbuffer())
    st.success(f"✅ CSV uploaded: {backup_file}")

else:
    df = pd.read_csv("data/tickets.csv")

# ===== Column mapping =====
df.columns = df.columns.str.strip().str.lower()
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

# ===== Example Selectbox =====
priority_filter = st.selectbox("Select Priority", options=["All"] + df['priority'].dropna().unique().tolist())
status_filter = st.selectbox("Select Status", options=["All"] + df['status'].dropna().unique().tolist())

st.write("Priority selected:", priority_filter)
st.write("Status selected:", status_filter)

# ===== แปลง datetime ===== ใช้ errors='coerce' → แปลงไม่ได้จะกลายเป็น NaT
df['created_date'] = pd.to_datetime(df['created_date'], errors='coerce')
df['resolved_date'] = pd.to_datetime(df['resolved_date'], errors='coerce')


if uploaded_file:
    # เก็บไฟล์ backup
    archive_dir = "data/archive/"
    os.makedirs(archive_dir, exist_ok=True)
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    backup_file = os.path.join(archive_dir, f"tickets_{timestamp}.csv")
    with open(backup_file, "wb") as f:
        f.write(uploaded_file.getbuffer())


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