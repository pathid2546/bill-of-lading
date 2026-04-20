import streamlit as st
import pandas as pd
import io

# --- UI CONFIG ---
st.set_page_config(page_title="BNN | Meat Order Preview System", layout="wide")
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Kanit:wght@300;400;500;600&display=swap');
    html, body, [class*="css"], .main { background-color: #0A0C10; color: #FFFFFF !important; font-family: 'Kanit', sans-serif; }
    .stTable { background-color: #161B22; border-radius: 10px; }
    div.stButton > button { background: #FFD60A; color: black; border-radius: 8px; font-weight: bold; width: 100%; border: none; height: 50px; }
    .preview-header { color: #FFD60A; font-size: 20px; font-weight: bold; margin-top: 20px; margin-bottom: 10px; }
    </style>
    """, unsafe_allow_html=True)

st.title("🥩 ระบบใบน้ำหนัก (แสดง Preview ก่อนดาวน์โหลด)")

file = st.file_uploader("📥 อัปโหลดไฟล์ใบเบิกสินค้า (Raw Data)", type="xlsx")

if file:
    if st.button("🔍 ตรวจสอบและแสดงตัวอย่าง (Preview)"):
        try:
            # 1. อ่านข้อมูล
            raw_df = pd.read_excel(file, header=None)
            desc_row_idx = next((i for i, r in raw_df.iterrows() if r.astype(str).str.contains('Description', na=False).any()), None)
            
            if desc_row_idx is not None:
                thai_names_row = raw_df.iloc[desc_row_idx]
                trip_codes_row = raw_df.iloc[desc_row_idx + 1] # แถบสีแดง
                df_data = pd.read_excel(file, skiprows=desc_row_idx + 1)
                
                store_indices = range(4, len(thai_names_row))
                trip_map = {df_data.columns[i]: str(trip_codes_row[i]).strip() for i in store_indices if pd.notna(trip_codes_row[i])}
                name_map = {df_data.columns[i]: str(thai_names_row[i]).strip() for i in store_indices if pd.notna(thai_names_row[i])}

                # 2. กรองเฉพาะ เนื้อ/หมู
                all_rows = []
                for _, row in df_data.iterrows():
                    product = str(row.get('Description', '')).strip()
                    if product in ['', 'nan', '0', '0.0'] or 'Description' in product: continue
                    
                    for idx in store_indices:
                        col_name = df_data.columns[idx]
                        qty = row[col_name]
                        if pd.notna(qty) and isinstance(qty, (int, float)) and qty > 0:
                            all_rows.append({
                                'TRIP': trip_map.get(col_name, "-"),
                                'STORE NAME': name_map.get(col_name, "ไม่ระบุ"),
                                'Product': product,
                                'Qty': qty
                            })

                if all_rows:
                    full_df = pd.DataFrame(all_rows)
                    weight_df = full_df[full_df['Product'].str.contains('เนื้อ|หมู', na=False)]
                    
                    # สร้าง Matrix สำหรับ Preview
                    matrix = weight_df.pivot_table(index=['TRIP', 'STORE NAME'], columns='Product', values='Qty', aggfunc='sum').fillna(0).reset_index()
                    
                    # --- ส่วนของ PREVIEW บนหน้าจอ ---
                    st.markdown('<p class="preview-header">📋 ตัวอย่างข้อมูลที่จะพิมพ์ (Preview)</p>', unsafe_allow_html=True)
                    st.dataframe(matrix.style.format(precision=2), use_container_width=True)
                    
                    # --- ส่วนการสร้างไฟล์ Excel (v2.2 Logic) ---
                    output = io.BytesIO()
                    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                        workbook = writer.book
                        worksheet = workbook.add_worksheet('น้ำหนัก')
                        
                        # Formats
                        header_fmt = workbook.add_format({'bold': True, 'align': 'center', 'valign': 'vcenter', 'bg_color': '#FFFF00', 'border': 1, 'text_wrap': True})
                        data_fmt = workbook.add_format({'border': 1, 'align': 'center'})
                        
                        # เขียนหัวตาราง 2 แถว
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

                        # เขียน Data
                        for i, row_data in matrix.iterrows():
                            r = i + 2
                            worksheet.write(r, 0, i+1, data_fmt)
                            worksheet.write(r, 1, row_data['TRIP'], data_fmt)
                            worksheet.write(r, 2, row_data['STORE NAME'], data_fmt)
                            d_col = 3
                            for p in products:
                                worksheet.write(r, d_col, row_data[p], data_fmt)
                                worksheet.write(r, d_col+1, "", data_fmt)
                                d_col += 2
                        
                        worksheet.set_column('C:C', 30)

                    # --- ปุ่มดาวน์โหลดจะปรากฏเมื่อ Preview เสร็จสิ้น ---
                    st.divider()
                    st.success("✅ ตรวจสอบข้อมูลเรียบร้อย หากถูกต้องกดดาวน์โหลดได้เลยครับ")
                    st.download_button(
                        label="📥 ดาวน์โหลดไฟล์ Excel (v2.3)",
                        data=output.getvalue(),
                        file_name="Weight_Sheet_Ready.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                    )
                else:
                    st.warning("⚠️ ไม่พบข้อมูลกลุ่ม เนื้อ/หมู ในไฟล์ที่อัปโหลด")
            else:
                st.error("❌ ไม่พบคอลัมน์ Description ในไฟล์")
        except Exception as e:
            st.error(f"❌ เกิดข้อผิดพลาด: {e}")