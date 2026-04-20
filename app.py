import streamlit as st
import pandas as pd
import io

# --- CONFIG & ULTRA MODERN DARK THEME ---
st.set_page_config(page_title="BNN | Master Reverse", layout="wide")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Kanit:wght@300;400;500;600&display=swap');
    
    html, body, [class*="css"], .main {
        background-color: #0A0C10;
        color: #FFFFFF !important;
        font-family: 'Kanit', sans-serif;
    }

    /* ตกแต่ง Sidebar ให้ดูแพง */
    [data-testid="stSidebar"] {
        background-color: #111418;
        border-right: 2px solid #1F2328;
    }

    /* หัวข้อไล่เฉดสี */
    .hero-text {
        background: linear-gradient(90deg, #00F2FF, #006AFF);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-size: 3rem;
        font-weight: 700;
        text-shadow: 0 0 20px rgba(0, 242, 255, 0.2);
    }

    /* Metric Cards สไตล์ใหม่ (Glow border) */
    div[data-testid="metric-container"] {
        background: #161B22;
        border: 1px solid #30363D;
        padding: 25px;
        border-radius: 20px;
        box-shadow: 0 8px 16px rgba(0,0,0,0.6);
        transition: 0.3s;
    }
    div[data-testid="metric-container"]:hover {
        border-color: #00F2FF;
        transform: scale(1.02);
    }

    /* ปรับแต่งสี Metric ให้มองเห็นชัดเจน */
    [data-testid="stMetricValue"] { color: #00F2FF !important; }
    [data-testid="stMetricLabel"] { color: #8B949E !important; font-size: 1rem !important; }

    /* ปุ่มกด Neon Pink */
    div.stButton > button {
        background: linear-gradient(45deg, #FF0080, #FF6700);
        color: white !important;
        border: none;
        border-radius: 12px;
        padding: 12px 24px;
        font-weight: 600;
        width: 100%;
        box-shadow: 0 4px 15px rgba(255, 0, 128, 0.3);
    }
    </style>
    """, unsafe_allow_html=True)

# --- MAIN PAGE ---
st.markdown('<p class="hero-text">REVERSE ENGINE v1.2</p>', unsafe_allow_html=True)

col_info, col_action = st.columns([1, 1.5])

with col_info:
    st.markdown("### 🛠 วิธีแก้ปัญหา Error")
    st.write("1. อัปโหลดไฟล์ **'ใบเบิกสาขา'** ที่ประมวลผลเสร็จแล้ว")
    st.write("2. ระบบจะเริ่มอ่านข้อมูลจากแถวที่มีคำว่า **'Description'** โดยอัตโนมัติ")
    st.write("3. ถ้ายัง Error ให้เช็คว่าในไฟล์มีคอลัมน์ชื่อนี้หรือไม่")

with col_action:
    uploaded_file = st.file_uploader("ลากไฟล์ใบเบิกวางที่นี่", type="xlsx")

if uploaded_file:
    if st.button("✨ EXTRACT TO RAW DATA"):
        try:
            # อ่านไฟล์แบบยังไม่ข้ามแถว เพื่อหาว่าหัวตารางอยู่ที่ไหน
            raw_excel = pd.read_excel(uploaded_file, header=None)
            
            # ค้นหาแถวที่มีคำว่า 'Description' หรือ 'รายการ'
            header_row_index = None
            for idx, row in raw_excel.iterrows():
                if row.astype(str).str.contains('Description|รายการ', case=False, na=False).any():
                    header_row_index = idx
                    break
            
            if header_row_index is None:
                st.error("❌ ไม่พบคอลัมน์ 'Description' ในไฟล์ของคุณ กรุณาตรวจสอบหัวตาราง")
            else:
                # อ่านไฟล์ใหม่อีกครั้งโดยเริ่มจากแถวที่เจอหัวตาราง
                df = pd.read_excel(uploaded_file, skiprows=header_row_index)
                
                # ทำความสะอาดชื่อคอลัมน์ (ลบช่องว่าง)
                df.columns = [str(c).strip() for c in df.columns]
                
                # แยกคอลัมน์ที่ไม่ใช่ข้อมูลสาขาออก
                static_cols = ['#', 'Item No.', 'Description', 'UNIT']
                store_cols = [c for c in df.columns if c not in static_cols and 'Unnamed' not in c]
                
                extracted_data = []
                for _, row in df.iterrows():
                    # ตรวจสอบ Description ถ้าว่างให้ข้าม
                    desc = row.get('Description')
                    if pd.isna(desc) or str(desc).strip() in ['', '0', '0.0']: continue
                    
                    for store in store_cols:
                        qty = row[store]
                        # เก็บเฉพาะสาขาที่มีจำนวนสั่ง
                        if pd.notna(qty) and isinstance(qty, (int, float)) and qty > 0:
                            extracted_data.append({
                                'Branch Name': store,
                                'Product Name': desc,
                                'Quantity': qty,
                                'Unit': row.get('UNIT', '-')
                            })
                
                if extracted_data:
                    final_df = pd.DataFrame(extracted_data)
                    
                    # แสดงผล Metrics
                    m1, m2 = st.columns(2)
                    m1.metric("TOTAL ORDERS", len(final_df))
                    m2.metric("UNIQUE PRODUCTS", len(final_df['Product Name'].unique()))
                    
                    st.dataframe(final_df, use_container_width=True)
                    
                    # เตรียมไฟล์ให้ดาวน์โหลด
                    output = io.BytesIO()
                    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                        final_df.to_excel(writer, index=False)
                    
                    st.download_button("🎁 DOWNLOAD RAW DATA (.xlsx)", output.getvalue(), "BNN_Recovered_Input.xlsx")
                else:
                    st.warning("⚠️ พบหัวตารางแต่ไม่พบข้อมูลจำนวนการสั่งซื้อ (Qty > 0)")
        
        except Exception as e:
            st.error(f"⚠️ ระบบขัดข้อง: {str(e)}")