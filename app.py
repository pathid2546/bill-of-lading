import streamlit as st
import pandas as pd
import io

# --- CONFIG & MODERN DARK THEME ---
st.set_page_config(page_title="BNN | Master Reverse", layout="wide")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Kanit:wght@300;400;500;600&display=swap');
    html, body, [class*="css"], .main { background-color: #0A0C10; color: #FFFFFF !important; font-family: 'Kanit', sans-serif; }
    .hero-text { background: linear-gradient(90deg, #00F2FF, #006AFF); -webkit-background-clip: text; -webkit-text-fill-color: transparent; font-size: 2.5rem; font-weight: 700; text-align: center; margin-bottom: 20px; }
    div[data-testid="metric-container"] { background: #161B22; border: 1px solid #30363D; padding: 20px; border-radius: 20px; border-top: 4px solid #FFD60A; }
    [data-testid="stMetricValue"] { color: #FFD60A !important; }
    div.stButton > button { background: linear-gradient(45deg, #FF0080, #FF6700); color: white !important; border: none; border-radius: 12px; padding: 12px 24px; font-weight: 600; width: 100%; box-shadow: 0 4px 15px rgba(255, 0, 128, 0.3); }
    </style>
    """, unsafe_allow_html=True)

st.markdown('<p class="hero-text">REVERSE DATA RECOVERY PRO</p>', unsafe_allow_html=True)

uploaded_file = st.file_uploader("📤 อัปโหลดไฟล์ใบเบิกที่ต้องการแปลงกลับเป็น Raw Data", type="xlsx")

if uploaded_file:
    if st.button("🚀 กู้คืนข้อมูล Raw Data แบบเต็มรูปแบบ"):
        try:
            # 1. ค้นหาแถวหัวตาราง (เหมือนเวอร์ชันก่อนหน้า)
            raw_excel = pd.read_excel(uploaded_file, header=None)
            header_row_index = None
            for idx, row in raw_excel.iterrows():
                if row.astype(str).str.contains('Description|รายการ', case=False, na=False).any():
                    header_row_index = idx
                    break
            
            if header_row_index is not None:
                # 2. อ่านข้อมูลและเตรียม Column Mapping
                df = pd.read_excel(uploaded_file, skiprows=header_row_index)
                df.columns = [str(c).strip() for c in df.columns]
                
                # ตรวจสอบ Trip Code จากแถวที่ 7 (ใน Output ต้นฉบับ)
                # หรือหาจากคอลัมน์ที่อยู่ใต้ Store Name
                static_cols = ['#', 'Item No.', 'Description', 'UNIT']
                store_cols = [c for c in df.columns if c not in static_cols and 'Unnamed' not in c]
                
                # 3. สกัดข้อมูล Trip Code และชื่อเต็มของสาขา
                # ใน Output ของเรา ชื่อสาขาภาษาอังกฤษจะเป็น Header ส่วนภาษาไทยจะอยู่ใน Row ข้อมูล
                # เราจะเก็บ Mapping เหล่านี้ไว้
                temp_list = []
                for _, row in df.iterrows():
                    desc = row.get('Description')
                    if pd.isna(desc) or str(desc).strip() in ['', '0', '0.0']: continue
                    
                    for store in store_cols:
                        qty = row[store]
                        if pd.notna(qty) and isinstance(qty, (int, float)) and qty > 0:
                            temp_list.append({
                                'STORE ID': store,
                                'Product': desc,
                                'Qty': qty
                            })
                
                if temp_list:
                    # 4. แปลงเป็น Matrix Format
                    long_df = pd.DataFrame(temp_list)
                    matrix_df = long_df.pivot_table(
                        index='STORE ID', 
                        columns='Product', 
                        values='Qty', 
                        aggfunc='sum'
                    ).fillna(0).reset_index()
                    
                    # 5. กู้คืนข้อมูลชื่อภาษาไทยและ Trip Code (Mapping)
                    # เราจะใช้เทคนิคดึง Trip จากแถวแรกๆ ของไฟล์ที่อัปโหลดมา
                    # (ปกติ Trip Code จะอยู่ที่ Row Index 0 ของข้อมูลหลัง Skip Header)
                    trip_mapping = {}
                    try:
                        for store in store_cols:
                            trip_mapping[store] = df[store].iloc[0] # แถวแรกของข้อมูลสาขามักเป็น Trip Code
                    except:
                        pass

                    # รวมข้อมูลกลับเข้าด้วยกัน
                    matrix_df['Trip'] = matrix_df['STORE ID'].map(trip_mapping)
                    
                    # จัดเรียงคอลัมน์ใหม่ให้เหมือนต้นฉบับ
                    # No. | STORE ID | STORE NAME (ถ้ามี) | Trip | สินค้า...
                    cols = matrix_df.columns.tolist()
                    # ย้าย Trip มาไว้ด้านหน้า
                    new_order = ['STORE ID', 'Trip'] + [c for c in cols if c not in ['STORE ID', 'Trip']]
                    final_df = matrix_df[new_order]
                    final_df.insert(0, 'No.', range(1, len(final_df) + 1))
                    
                    st.success("✅ กู้คืนข้อมูลพร้อมรหัส Trip สำเร็จ!")
                    st.dataframe(final_df, use_container_width=True)
                    
                    # 6. สร้างไฟล์ Excel สำหรับ Download
                    output = io.BytesIO()
                    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                        final_df.to_excel(writer, index=False, sheet_name='Restored_RawData')
                        
                        # ตกแต่งไฟล์ให้สวยงาม
                        workbook = writer.book
                        worksheet = writer.sheets['Restored_RawData']
                        header_format = workbook.add_format({'bold': True, 'bg_color': '#FFD60A', 'border': 1})
                        
                        for col_num, value in enumerate(final_df.columns.values):
                            worksheet.write(0, col_num, value, header_format)
                            worksheet.set_column(col_num, col_num, 15)

                    st.download_button("📥 ดาวน์โหลดไฟล์ Raw Data (Full Version)", output.getvalue(), "BNN_Full_RawData.xlsx")
                else:
                    st.warning("ไม่พบยอดสั่งซื้อในไฟล์นี้")
            else:
                st.error("ไม่พบคอลัมน์ Description")
        except Exception as e:
            st.error(f"เกิดข้อผิดพลาด: {e}")