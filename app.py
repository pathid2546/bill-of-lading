import streamlit as st
import pandas as pd
import io

# --- UI CONFIG ---
st.set_page_config(page_title="BNN | Weight Sheet v2.5", layout="wide")
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Kanit:wght@300;400;500;600&display=swap');
    html, body, [class*="css"], .main { background-color: #0A0C10; color: #FFFFFF !important; font-family: 'Kanit', sans-serif; }
    div.stButton > button { background: #FFD60A; color: black; border-radius: 8px; font-weight: bold; width: 100%; border: none; height: 50px; }
    </style>
    """, unsafe_allow_html=True)

st.title("🥩 ระบบใบน้ำหนัก (Optimized for Test.xlsx)")

file = st.file_uploader("📥 อัปโหลดไฟล์ Test.xlsx หรือไฟล์ใบเบิก", type=["xlsx", "csv"])

if file:
    if st.button("🔍 ประมวลผลและแสดง Preview"):
        try:
            # 1. อ่านข้อมูล (รองรับทั้ง CSV จาก Test Data และ XLSX จริง)
            if file.name.endswith('.csv'):
                raw_df = pd.read_csv(file, header=None)
            else:
                raw_df = pd.read_excel(file, header=None)
            
            # ค้นหาแถวที่มีคำว่า 'Description' (ใน Test.xlsx คือแถวที่ 4)
            header_row_idx = next((i for i, r in raw_df.iterrows() if r.astype(str).str.contains('Description', na=False).any()), None)
            
            if header_row_idx is not None:
                # ตั้งค่าหัวตารางจริง
                df_clean = raw_df.iloc[header_row_idx:].copy()
                df_clean.columns = df_clean.iloc[0]
                df_clean = df_clean.iloc[1:].reset_index(drop=True)
                
                # ล้างชื่อคอลัมน์
                df_clean.columns = [str(c).strip() for c in df_clean.columns]
                
                # คอลัมน์สาขาเริ่มจาก Index 4 (คอลัมน์ E) เป็นต้นไป
                store_cols = [c for c in df_clean.columns[4:] if "Unnamed" not in c]
                
                # แถว TRIP (ช่องแดง) คือแถวถัดจาก Description ในไฟล์จริง 
                # แต่ใน Test.xlsx แถวนี้อาจจะเป็นข้อมูลสินค้าเลย ผมจะดึงรหัสจาก Header แทนถ้าหาช่องแดงไม่เจอ
                trip_row = raw_df.iloc[header_row_idx + 1]

                all_rows = []
                for idx, row in df_clean.iterrows():
                    product = str(row.get('Description', '')).strip()
                    # กรองเฉพาะ เนื้อ และ หมู
                    if any(keyword in product for keyword in ['เนื้อ', 'หมู', 'Meat', 'Pork']):
                        for col in store_cols:
                            qty = row[col]
                            # แปลงเป็นตัวเลขและเช็คว่า > 0
                            try:
                                qty_num = float(qty)
                                if qty_num > 0:
                                    all_rows.append({
                                        'TRIP': str(trip_row[df_clean.columns.get_loc(col)]).strip() if pd.notna(trip_row[df_clean.columns.get_loc(col)]) else "-",
                                        'STORE NAME': col,
                                        'Product': product,
                                        'Qty': qty_num
                                    })
                            except:
                                continue

                if all_rows:
                    final_df = pd.DataFrame(all_rows)
                    # สร้าง Pivot Matrix
                    matrix = final_df.pivot_table(index=['TRIP', 'STORE NAME'], columns='Product', values='Qty', aggfunc='sum').fillna(0).reset_index()
                    
                    st.success(f"🔍 พบข้อมูลสินค้ากลุ่มเนื้อ/หมู {len(final_df)} รายการ")
                    st.dataframe(matrix, use_container_width=True)

                    # --- สร้างไฟล์ Excel (v2.2 Logic หัวตาราง 2 แถว) ---
                    output = io.BytesIO()
                    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                        workbook = writer.book
                        worksheet = workbook.add_worksheet('น้ำหนัก')
                        
                        header_fmt = workbook.add_format({'bold': True, 'align': 'center', 'valign': 'vcenter', 'bg_color': '#FFFF00', 'border': 1, 'text_wrap': True})
                        data_fmt = workbook.add_format({'border': 1, 'align': 'center'})
                        total_fmt = workbook.add_format({'bold': True, 'bg_color': '#E2EFDA', 'border': 1})

                        # เขียน Header
                        worksheet.merge_range(0, 0, 1, 0, "No.", header_fmt)
                        worksheet.merge_range(0, 1, 1, 1, "TRIP", header_fmt)
                        worksheet.merge_range(0, 2, 1, 2, "STORE NAME", header_fmt)

                        prods = [p for p in matrix.columns if p not in ['TRIP', 'STORE NAME']]
                        c_idx = 3
                        for p in prods:
                            worksheet.write(0, c_idx, "จำนวนสั่ง", header_fmt)
                            worksheet.write(1, c_idx, p, header_fmt)
                            worksheet.merge_range(0, c_idx+1, 1, c_idx+1, "จ่ายจริง", header_fmt)
                            c_idx += 2
                        
                        worksheet.merge_range(0, c_idx, 1, c_idx, "ตะกร้า", header_fmt)
                        worksheet.merge_range(0, c_idx+1, 1, c_idx+1, "กล่อง", header_fmt)

                        # เขียน Data
                        for i, r_data in matrix.iterrows():
                            curr_r = i + 2
                            worksheet.write(curr_r, 0, i+1, data_fmt)
                            worksheet.write(curr_r, 1, r_data['TRIP'], data_fmt)
                            worksheet.write(curr_r, 2, r_data['STORE NAME'], data_fmt)
                            d_idx = 3
                            for p in prods:
                                worksheet.write(curr_r, d_idx, r_data[p], data_fmt)
                                worksheet.write(curr_r, d_idx+1, "", data_fmt)
                                d_idx += 2
                        
                        # แถว TOTAL
                        last_r = len(matrix) + 2
                        worksheet.merge_range(last_r, 0, last_r, 2, "TOTAL", total_fmt)
                        t_idx = 3
                        for p in prods:
                            worksheet.write(last_r, t_idx, matrix[p].sum(), total_fmt)
                            worksheet.write(last_r, t_idx+1, "", total_fmt)
                            t_idx += 2

                        worksheet.set_column('C:C', 35)

                    st.divider()
                    st.download_button("📥 ดาวน์โหลดไฟล์ใบน้ำหนัก", output.getvalue(), "BNN_WeightSheet_v2.5.xlsx")
                else:
                    st.error("❌ ไม่พบข้อมูลการสั่งซื้อที่มีจำนวน > 0 ในกลุ่มเนื้อ/หมู")
                    st.info("ตรวจสอบว่าในคอลัมน์ E เป็นต้นไป มีการใส่ตัวเลขในแถวที่เป็นสินค้าเนื้อหรือหมูหรือไม่")
            else:
                st.error("❌ ไม่พบคอลัมน์ 'Description' ในไฟล์")
        except Exception as e:
            st.error(f"เกิดข้อผิดพลาด: {e}")