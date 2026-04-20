import streamlit as st
import pandas as pd
import io

# --- CONFIG & STYLING ---
st.set_page_config(page_title="BNN | Reverse Processor", layout="wide")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Kanit:wght@300;400;500;600&display=swap');
    
    html, body, [class*="css"], .main {
        background-color: #0D1117;
        color: #FFFFFF !important;
        font-family: 'Kanit', sans-serif;
    }

    /* Gradient Header */
    .main-header {
        background: linear-gradient(90deg, #BF5AF2, #FFD60A);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-size: 3rem;
        font-weight: 700;
        margin-bottom: 1rem;
    }

    /* Modern Glass Card */
    div[data-testid="metric-container"] {
        background: rgba(255, 255, 255, 0.05);
        border: 1px solid rgba(255, 255, 255, 0.1);
        backdrop-filter: blur(10px);
        padding: 20px;
        border-radius: 24px;
        box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.8);
        border-top: 2px solid #BF5AF2;
    }

    [data-testid="stMetricValue"] { color: #FFD60A !important; }
    [data-testid="stMetricLabel"] { color: #E0E0E0 !important; }

    /* Button Styling */
    div.stButton > button {
        background: linear-gradient(135deg, #BF5AF2 0%, #5E5CE6 100%);
        color: white !important;
        border: none;
        border-radius: 15px;
        padding: 15px 30px;
        font-weight: 600;
        transition: all 0.3s ease;
    }
    div.stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 10px 20px rgba(191, 90, 242, 0.4);
    }

    /* Sidebar Decor */
    [data-testid="stSidebar"] {
        background-color: #161B22;
        border-right: 1px solid #30363D;
    }
    </style>
    """, unsafe_allow_html=True)

# --- APP LOGIC ---
st.markdown('<h1 class="main-header">Reverse Order Sync</h1>', unsafe_allow_html=True)

with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/2108/2108625.png", width=80)
    st.markdown("### Reverse Logic v1.0")
    st.caption("ระบบย้อนกลับ: จากใบเบิก -> ข้อมูลดิบ")
    st.divider()
    mode = st.radio("ขั้นตอน", ["📤 Upload Output", "⚙️ Data Recovery"])

if mode == "📤 Upload Output":
    st.subheader("ย้อนกลับไฟล์ใบเบิกให้เป็น Raw Data")
    
    col_info, col_up = st.columns([1, 2])
    with col_info:
        st.info("💡 ระบบจะสแกนหา 'Description' และ 'Trip Code' จากใบเบิกที่อัปโหลด แล้วกระจายตัวเลขออกมาเป็นแถวข้อมูล")
    
    with col_up:
        uploaded_file = st.file_uploader("เลือกไฟล์ใบเบิก (Output .xlsx)", type="xlsx")

    if uploaded_file:
        if st.button("🪄 เริ่มการแปลงย้อนกลับ (Reverse)"):
            try:
                # 1. อ่านข้อมูล โดยเริ่มจาก Row ที่เป็น Header ของตาราง (Row 6 ใน Output)
                df = pd.read_excel(uploaded_file, skiprows=5)
                
                # 2. เก็บรายชื่อสาขา (Columns ตั้งแต่ Index 4 เป็นต้นไป)
                static_cols = ['#', 'Item No.', 'Description', 'UNIT']
                store_cols = [c for c in df.columns if c not in static_cols and not c.startswith('Unnamed')]
                
                # 3. สกัด Trip Code (จาก Row ที่ 7 ใน Output ต้นฉบับ)
                # หมายเหตุ: ในโค้ดนี้เราจะดึงจาก Header ที่อัปโหลดมา
                raw_rows = []
                
                for _, row in df.iterrows():
                    desc = row['Description']
                    if pd.isna(desc) or desc == 0: continue
                    
                    for store in store_cols:
                        qty = row[store]
                        if qty > 0: # ดึงเฉพาะรายการที่มีการสั่ง
                            raw_rows.append({
                                'Store Name': store,
                                'Item Description': desc,
                                'Quantity': qty,
                                'Unit': row.get('UNIT', '-')
                            })
                
                res_df = pd.DataFrame(raw_rows)
                
                # Metrics Display
                m1, m2 = st.columns(2)
                m1.metric("TOTAL ORDERS FOUND", len(res_df))
                m2.metric("UNIQUE STORES", len(res_df['Store Name'].unique()) if not res_df.empty else 0)
                
                st.markdown("### 📋 ข้อมูลที่สกัดได้ (Input Preview)")
                st.dataframe(res_df, use_container_width=True)

                # Export back to Excel (Input Style)
                output = io.BytesIO()
                with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                    res_df.to_excel(writer, index=False, sheet_name='RawData_Recovered')
                
                st.session_state.recovered_data = output.getvalue()
                st.success("แปลงข้อมูลย้อนกลับเสร็จสิ้น!")
                
            except Exception as e:
                st.error(f"ไม่สามารถแปลงไฟล์ได้: {e}")

    if 'recovered_data' in st.session_state:
        st.download_button(
            label="📥 ดาวน์โหลดไฟล์ Raw Data (.xlsx)",
            data=st.session_state.recovered_data,
            file_name="Recovered_Input_Data.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

elif mode == "⚙️ Data Recovery":
    st.title("Settings & Mapping")
    st.warning("หน้านี้สำหรับการตั้งค่าการจับคู่คอลัมน์ (Column Mapping) ในกรณีที่โครงสร้าง Output เปลี่ยนไป")
    st.write("Current Mapping Profile: **Standard BNN Output**")