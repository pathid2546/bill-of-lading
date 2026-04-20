import streamlit as st
import pandas as pd
import io

# --- CONFIG & CYBER-CUTE THEME ---
st.set_page_config(page_title="BNN | Reverse Sync", layout="wide")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Kanit:wght@300;400;500;600&display=swap');
    
    html, body, [class*="css"], .main {
        background-color: #0D1117;
        color: #FFFFFF !important;
        font-family: 'Kanit', sans-serif;
    }

    /* Gradient Title */
    .cyber-title {
        background: linear-gradient(135deg, #FF007A 0%, #00D4FF 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-size: 3.5rem;
        font-weight: 800;
        text-align: center;
        margin-bottom: 2rem;
        filter: drop-shadow(0 0 10px rgba(255, 0, 122, 0.3));
    }

    /* Soft Glow Cards */
    div[data-testid="metric-container"] {
        background: #161B22;
        border: 1px solid #30363D;
        padding: 20px;
        border-radius: 25px;
        box-shadow: 0 10px 30px rgba(0,0,0,0.5);
        border-left: 5px solid #FFD60A; /* เส้นข้างสีเหลืองสดใส */
    }

    [data-testid="stMetricValue"] { color: #00D4FF !important; font-size: 3rem !important; }
    [data-testid="stMetricLabel"] { color: #FF007A !important; font-weight: 600 !important; }

    /* Button Neon Style */
    div.stButton > button {
        background: linear-gradient(45deg, #FF007A, #FF7676);
        color: white !important;
        border: none;
        border-radius: 18px;
        padding: 15px 40px;
        font-size: 1.2rem;
        font-weight: 600;
        width: 100%;
        box-shadow: 0 0 15px rgba(255, 0, 122, 0.4);
        transition: 0.3s;
    }
    div.stButton > button:hover {
        transform: scale(1.02);
        box-shadow: 0 0 25px rgba(255, 0, 122, 0.7);
    }
    </style>
    """, unsafe_allow_html=True)

# --- MAIN UI ---
st.markdown('<h1 class="cyber-title">BNN REVERSE PRO</h1>', unsafe_allow_html=True)

# Tabs สำหรับหน้าจอที่สะอาดตา
tab_main, tab_help = st.tabs(["🔄 แปลงไฟล์ย้อนกลับ", "❓ วิธีใช้งาน"])

with tab_main:
    col_up, col_res = st.columns([1, 1.2])
    
    with col_up:
        st.markdown("### 📥 ใส่ไฟล์ใบเบิกที่นี่")
        file = st.file_uploader("Upload Output.xlsx", type="xlsx", label_visibility="collapsed")
        
    if file:
        if st.button("🚀 UNLOCK RAW DATA"):
            try:
                # 1. อ่านข้อมูลโดยเริ่มจาก Header (Row 6)
                df = pd.read_excel(file, skiprows=5)
                
                # 2. แก้จุด Error: บังคับให้ Column Name เป็น String ก่อนใช้ .startswith
                static_cols = ['#', 'Item No.', 'Description', 'UNIT']
                store_cols = [c for c in df.columns if str(c) not in static_cols and not str(c).startswith('Unnamed')]
                
                raw_rows = []
                for _, row in df.iterrows():
                    desc = row['Description']
                    if pd.isna(desc) or desc == 0: continue
                    
                    for store in store_cols:
                        qty = row[store]
                        # ตรวจสอบว่าเป็นตัวเลขและมากกว่า 0
                        if pd.notna(qty) and isinstance(qty, (int, float)) and qty > 0:
                            raw_rows.append({
                                'Branch': store,
                                'Product': desc,
                                'Order Qty': qty,
                                'Unit Type': row.get('UNIT', '-')
                            })
                
                if raw_rows:
                    res_df = pd.DataFrame(raw_rows)
                    
                    with col_res:
                        st.markdown("### ✨ ข้อมูลที่กู้คืนได้")
                        m1, m2 = st.columns(2)
                        m1.metric("TOTAL ROWS", len(res_df))
                        m2.metric("BRANCHES", len(res_df['Branch'].unique()))
                        
                        st.dataframe(res_df, use_container_width=True, height=300)
                        
                        # สร้างไฟล์ Excel สำหรับ Download
                        buf = io.BytesIO()
                        with pd.ExcelWriter(buf, engine='xlsxwriter') as writer:
                            res_df.to_excel(writer, index=False, sheet_name='RecoveredData')
                        
                        st.download_button(
                            "📥 DOWNLOAD RECOVERED DATA",
                            buf.getvalue(),
                            "Recovered_RawData.xlsx",
                            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                        )
                else:
                    st.warning("ไม่พบข้อมูลการสั่งซื้อในไฟล์นี้")
                    
            except Exception as e:
                # แสดง Error พร้อมวิธีแก้เบื้องต้น
                st.error(f"⚠️ เกิดข้อผิดพลาด: {e}")
                st.info("คำแนะนำ: ตรวจสอบว่าไฟล์ที่อัปโหลดคือ 'ใบเบิก' ที่มีหัวตารางเหมือนเดิมหรือไม่")

with tab_help:
    st.markdown("""
    ### 📖 วิธีการกู้คืนข้อมูล (Reverse)
    1. **อัปโหลดไฟล์ใบเบิก:** ระบบจะอ่านตั้งแต่แถวที่ 6 เป็นต้นไป
    2. **ตรวจสอบหัวตาราง:** ระบบจะมองหาคอลัมน์ 'Description' เป็นหลัก
    3. **การกระจายข้อมูล:** สาขาที่อยู่แนวนอนจะถูกสกัดกลับมาเป็นแนวตั้ง เพื่อให้คุณเอาไปทำ Pivot Table ต่อได้ง่าย ๆ
    """)