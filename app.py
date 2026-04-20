import streamlit as st
import pandas as pd
import io

# --- CONFIG & MODERN DARK THEME ---
st.set_page_config(page_title="BNN | Perfect Reverse", layout="wide")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Kanit:wght@300;400;500;600&display=swap');
    html, body, [class*="css"], .main { background-color: #0A0C10; color: #FFFFFF !important; font-family: 'Kanit', sans-serif; }
    .hero-text { background: linear-gradient(90deg, #00F2FF, #006AFF); -webkit-background-clip: text; -webkit-text-fill-color: transparent; font-size: 2.5rem; font-weight: 700; text-align: center; }
    div[data-testid="metric-container"] { background: #161B22; border: 1px solid #30363D; padding: 20px; border-radius: 20px; border-top: 4px solid #00F2FF; }
    [data-testid="stMetricValue"] { color: #00F2FF !important; }
    div.stButton > button { background: linear-gradient(45deg, #FF0080, #FF6700); color: white !important; border: none; border-radius: 12px; padding: 12px 24px; font-weight: 600; width: 100%; box-shadow: 0 4px 15px rgba(255, 0, 128, 0.3); }
    </style>
    """, unsafe_allow_html=True)

st.markdown('<p class="hero-text">REVERSE TO RAW DATA FORMAT</p>', unsafe_allow_html=True)

uploaded_file = st.file_uploader("📤 อัปโหลดไฟล์ใบเบิก (Output) เพื่อแปลงกลับเป็น Raw Data", type="xlsx")

if uploaded_file:
    if st.button("🚀 START REVERSE PROCESSING"):
        try:
            # 1. ค้นหาหัวตาราง (เหมือนเวอร์ชันก่อนหน้า)
            raw_excel = pd.read_excel(uploaded_file, header=None)
            header_row_index = None
            for idx, row in raw_excel.iterrows():
                if row.astype(str).str.contains('Description|รายการ', case=False, na=False).any():
                    header_row_index = idx
                    break
            
            if header_row_index is not None:
                # 2. อ่านข้อมูลและทำความสะอาด
                df = pd.read_excel(uploaded_file, skiprows=header_row_index)
                df.columns = [str(c).strip() for c in df.columns]
                
                # เก็บ Trip Code (แถวแรกหลังจากหัวตารางในบาง Format)
                static_cols = ['#', 'Item No.', 'Description', 'UNIT']
                store_cols = [c for c in df.columns if c not in static_cols and 'Unnamed' not in c]
                
                # 3. สร้างรายการข้อมูลแบบ Long Format ชั่วคราว
                temp_list = []
                for _, row in df.iterrows():
                    desc = row.get('Description')
                    if pd.isna(desc) or str(desc).strip() in ['', '0', '0.0']: continue
                    
                    for store in store_cols:
                        qty = row[store]
                        if pd.notna(qty) and isinstance(qty, (int, float)) and qty > 0:
                            temp_list.append({
                                'STORE NAME': store,
                                'Product': desc,
                                'Qty': qty
                            })
                
                if temp_list:
                    # 4. แปลงกลับเป็น Matrix (Pivot) ให้เหมือนรูปแรก
                    long_df = pd.DataFrame(temp_list)
                    
                    # ใช้ pivot_table เพื่อสร้างตารางที่มี Store เป็นแถว และ Product เป็นคอลัมน์
                    final_df = long_df.pivot_table(
                        index='STORE NAME', 
                        columns='Product', 
                        values='Qty', 
                        aggfunc='sum'
                    ).fillna(0).reset_index()
                    
                    # ตกแต่งหัวตารางให้ดูง่าย
                    final_df.columns.name = None 
                    
                    # แสดงผล Metrics และ Preview
                    st.success("✅ แปลงข้อมูลกลับเป็นรูปแบบ Raw Data สำเร็จ!")
                    m1, m2 = st.columns(2)
                    m1.metric("จำนวนสาขาที่พบ", len(final_df))
                    m2.metric("จำนวนสินค้าทั้งหมด", len(final_df.columns) - 1)
                    
                    st.dataframe(final_df, use_container_width=True)
                    
                    # 5. สร้างไฟล์ Excel
                    output = io.BytesIO()
                    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                        final_df.to_excel(writer, index=False, sheet_name='RawData_Format')
                        
                        # ปรับแต่งความกว้างคอลัมน์อัตโนมัติ
                        workbook = writer.book
                        worksheet = writer.sheets['RawData_Format']
                        for i, col in enumerate(final_df.columns):
                            worksheet.set_column(i, i, max(len(str(col)), 10))

                    st.download_button(
                        "📥 ดาวน์โหลดไฟล์รูปแบบ Raw Data (เหมือนรูปแรก)",
                        output.getvalue(),
                        "BNN_RawData_Restored.xlsx"
                    )
                else:
                    st.warning("ไม่พบข้อมูลที่มีจำนวนสั่งซื้อ > 0")
            else:
                st.error("ไม่พบคอลัมน์ 'Description' ในไฟล์")
        except Exception as e:
            st.error(f"เกิดข้อผิดพลาด: {e}")