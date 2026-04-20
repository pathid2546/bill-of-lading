import streamlit as st
import pandas as pd
import io

# --- UI CONFIG ---
st.set_page_config(page_title="BNN | Meat Order Debugger", layout="wide")
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Kanit:wght@300;400;500;600&display=swap');
    html, body, [class*="css"], .main { background-color: #0A0C10; color: #FFFFFF !important; font-family: 'Kanit', sans-serif; }
    div.stButton > button { background: #FFD60A; color: black; border-radius: 8px; font-weight: bold; width: 100%; border: none; height: 50px; }
    .debug-box { background-color: #1c1c1c; padding: 15px; border-radius: 10px; border: 1px solid #333; }
    </style>
    """, unsafe_allow_html=True)

st.title("🥩 ระบบใบน้ำหนัก (v2.4 - ตรวจสอบและดาวน์โหลด)")

file = st.file_uploader("📥 อัปโหลดไฟล์ใบเบิกสินค้า (Raw Data)", type="xlsx")

if file:
    if st.button("🔍 1. ตรวจสอบข้อมูลในไฟล์ (Preview)"):
        try:
            # 1. อ่านไฟล์ดิบ
            raw_df = pd.read_excel(file, header=None)
            
            # ค้นหาแถว Description
            desc_row_idx = next((i for i, r in raw_df.iterrows() if r.astype(str).str.contains('Description', na=False).any()), None)
            
            if desc_row_idx is not None:
                # ดึงชื่อภาษาไทย (Header) และ TRIP (แถบแดง)
                thai_names_row = raw_df.iloc[desc_row_idx]
                trip_codes_row = raw_df.iloc[desc_row_idx + 1]
                
                # ข้อมูลสินค้าเริ่มหลังจากแถบสีแดง
                df_data = pd.read_excel(file, skiprows=desc_row_idx + 1)
                store_indices = range(4, len(thai_names_row))

                all_rows = []
                for _, row in df_data.iterrows():
                    # ล้างช่องว่างเผื่อมี space ปนมา
                    product = str(row.get('Description', '')).strip()
                    if product in ['', 'nan', '0', '0.0'] or 'Description' in product: continue
                    
                    for idx in store_indices:
                        col_name = df_data.columns[idx]
                        qty = row[col_name]
                        if pd.notna(qty) and isinstance(qty, (int, float)) and qty > 0:
                            all_rows.append({
                                'TRIP': str(trip_codes_row[idx]).strip() if pd.notna(trip_codes_row[idx]) else "-",
                                'STORE NAME': str(thai_names_row[idx]).strip() if pd.notna(thai_names_row[idx]) else "ไม่ระบุ",
                                'Product': product,
                                'Qty': qty
                            })

                if all_rows:
                    full_df = pd.DataFrame(all_rows)
                    
                    # กรองข้อมูล (เพิ่ม .lower() และเช็คคำที่กว้างขึ้น)
                    weight_df = full_df[full_df['Product'].str.contains('เนื้อ|หมู|PORK|BEEF', case=False, na=False)]
                    
                    if not weight_df.empty:
                        # สร้าง Matrix
                        matrix = weight_df.pivot_table(index=['TRIP', 'STORE NAME'], columns='Product', values='Qty', aggfunc='sum').fillna(0).reset_index()
                        
                        st.success(f"✅ ตรวจพบสินค้ากลุ่มเนื้อ/หมู ทั้งหมด {len(weight_df)} รายการ")
                        st.markdown("**📋 ตัวอย่างตารางก่อนพิมพ์:**")
                        st.dataframe(matrix, use_container_width=True)

                        # --- สร้างไฟล์ Excel ---
                        output = io.BytesIO()
                        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                            workbook = writer.book
                            worksheet = workbook.add_worksheet('น้ำหนัก')
                            
                            # Formats
                            header_fmt = workbook.add_format({'bold': True, 'align': 'center', 'valign': 'vcenter', 'bg_color': '#FFFF00', 'border': 1, 'text_wrap': True})
                            data_fmt = workbook.add_format({'border': 1, 'align': 'center'})
                            total_fmt = workbook.add_format({'bold': True, 'bg_color': '#E2EFDA', 'border': 1})

                            # หัวตาราง
                            worksheet.merge_range(0, 0, 1, 0, "No.", header_fmt)
                            worksheet.merge_range(0, 1, 1, 1, "TRIP", header_fmt)
                            worksheet.merge_range(0, 2, 1, 2, "STORE NAME", header_fmt)

                            products = [p for p in matrix.columns if p not in ['TRIP', 'STORE NAME']]
                            c_ptr = 3
                            for p in products:
                                worksheet.write(0, c_ptr, "จำนวนสั่ง", header_fmt)
                                worksheet.write(1, c_ptr, p, header_fmt)
                                worksheet.merge_range(0, c_ptr+1, 1, c_ptr+1, "จ่ายจริง", header_fmt)
                                c_ptr += 2
                            
                            worksheet.merge_range(0, c_ptr, 1, c_ptr, "ตะกร้า", header_fmt)
                            worksheet.merge_range(0, c_ptr+1, 1, c_ptr+1, "กล่อง", header_fmt)

                            # เขียนข้อมูล
                            for i, row_data in matrix.iterrows():
                                r = i + 2
                                worksheet.write(r, 0, i+1, data_fmt)
                                worksheet.write(r, 1, row_data['TRIP'], data_fmt)
                                worksheet.write(r, 2, row_data['STORE NAME'], data_fmt)
                                d_ptr = 3
                                for p in products:
                                    worksheet.write(r, d_ptr, row_data[p], data_fmt)
                                    worksheet.write(r, d_ptr+1, "", data_fmt)
                                    d_ptr += 2
                                    
                            # แถว TOTAL
                            last_row = len(matrix) + 2
                            worksheet.merge_range(last_row, 0, last_row, 2, "TOTAL", total_fmt)
                            t_ptr = 3
                            for p in products:
                                worksheet.write(last_row, t_ptr, matrix[p].sum(), total_fmt)
                                worksheet.write(last_row, t_ptr+1, "", total_fmt)
                                t_ptr += 2

                            worksheet.set_column('C:C', 30)

                        st.divider()
                        st.download_button("📥 2. ดาวน์โหลดไฟล์ Excel", output.getvalue(), "BNN_Weight_Sheet.xlsx")
                    else:
                        st.error("❌ ไม่พบคำว่า 'เนื้อ' หรือ 'หมู' ในคอลัมน์ Description")
                        with st.expander("🔍 คลิกเพื่อดูรายการสินค้าทั้งหมดที่ระบบเห็น"):
                            st.write(full_df['Product'].unique())
                else:
                    st.warning("⚠️ ไม่พบข้อมูลการสั่งซื้อ (จำนวน > 0) ในคอลัมน์ E เป็นต้นไป")
            else:
                st.error("❌ หาคำว่า 'Description' ไม่เจอ กรุณาตรวจสอบหัวตาราง")
        except Exception as e:
            st.error(f"เกิดข้อผิดพลาด: {e}")