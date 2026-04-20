import streamlit as st
import pandas as pd
import io

st.set_page_config(page_title="BNN | Meat Order v2.2", layout="wide")
st.title("🥩 ระบบใบน้ำหนัก (ดึงรหัส TRIP จากแถบสีแดง)")

file = st.file_uploader("📥 อัปโหลดไฟล์ใบเบิกสินค้า (Raw Data)", type="xlsx")

if file:
    if st.button("🚀 ประมวลผลไฟล์"):
        try:
            # 1. อ่านข้อมูลดิบเพื่อหาตำแหน่ง Header
            raw_df = pd.read_excel(file, header=None)
            
            # หาแถวที่มี 'Description'
            desc_row_idx = next((i for i, r in raw_df.iterrows() if r.astype(str).str.contains('Description', na=False).any()), None)
            
            if desc_row_idx is not None:
                # ชื่อภาษาไทยจะอยู่ที่ Row ของ Description (Header หลัก)
                thai_names_row = raw_df.iloc[desc_row_idx]
                
                # รหัสภาษาอังกฤษ (TRIP) อยู่ในแถบสีแดง ซึ่งคือแถวถัดจาก Description
                trip_codes_row = raw_df.iloc[desc_row_idx + 1]
                
                # อ่านข้อมูลสินค้า (เริ่มหลังจากแถวแถบสีแดง)
                df_data = pd.read_excel(file, skiprows=desc_row_idx + 1)
                
                # คอลัมน์สาขาเริ่มที่ Index 4 (คอลัมน์ E เป็นต้นไป)
                store_indices = range(4, len(thai_names_row))
                
                # สร้าง Mapping สำหรับ TRIP และชื่อสาขา
                trip_map = {}
                name_map = {}
                for idx in store_indices:
                    col_name = df_data.columns[idx]
                    trip_map[col_name] = str(trip_codes_row[idx]).strip() if pd.notna(trip_codes_row[idx]) else "-"
                    name_map[col_name] = str(thai_names_row[idx]).strip() if pd.notna(thai_names_row[idx]) else "ไม่ระบุชื่อ"

                # 2. แปลงข้อมูลเป็นรายการ
                all_rows = []
                for _, row in df_data.iterrows():
                    product = str(row.get('Description', '')).strip()
                    if product in ['', 'nan', '0', '0.0'] or 'Description' in product: continue
                    
                    for idx in store_indices:
                        col_name = df_data.columns[idx]
                        qty = row[col_name]
                        if pd.notna(qty) and isinstance(qty, (int, float)) and qty > 0:
                            all_rows.append({
                                'TRIP': trip_map.get(col_name),   # ดึงจากแถบสีแดง
                                'STORE NAME': name_map.get(col_name), # ดึงจากหัวตารางเอียง
                                'Product': product,
                                'Qty': qty
                            })

                if all_rows:
                    full_df = pd.DataFrame(all_rows)
                    weight_df = full_df[full_df['Product'].str.contains('เนื้อ|หมู', na=False)] #
                    
                    matrix = weight_df.pivot_table(index=['TRIP', 'STORE NAME'], columns='Product', values='Qty', aggfunc='sum').fillna(0).reset_index()
                    products = [p for p in matrix.columns if p not in ['TRIP', 'STORE NAME']]
                    
                    # 3. สร้าง Excel (Header 2 แถว)
                    output = io.BytesIO()
                    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                        workbook = writer.book
                        worksheet = workbook.add_worksheet('น้ำหนัก')
                        
                        header_fmt = workbook.add_format({'bold': True, 'align': 'center', 'valign': 'vcenter', 'bg_color': '#FFFF00', 'border': 1, 'text_wrap': True})
                        data_fmt = workbook.add_format({'border': 1, 'align': 'center'})
                        total_fmt = workbook.add_format({'bold': True, 'bg_color': '#E2EFDA', 'border': 1, 'num_format': '#,##0'})

                        # เขียนหัวตารางคงที่
                        worksheet.merge_range(0, 0, 1, 0, "No.", header_fmt)
                        worksheet.merge_range(0, 1, 1, 1, "TRIP", header_fmt)
                        worksheet.merge_range(0, 2, 1, 2, "STORE NAME", header_fmt)

                        col_ptr = 3
                        for p in products:
                            worksheet.write(0, col_ptr, "จำนวนสั่ง", header_fmt) #
                            worksheet.write(1, col_ptr, p, header_fmt)
                            worksheet.merge_range(0, col_ptr + 1, 1, col_ptr + 1, "จ่ายจริง", header_fmt)
                            col_ptr += 2
                        
                        worksheet.merge_range(0, col_ptr, 1, col_ptr, "ตะกร้า", header_fmt)
                        worksheet.merge_range(0, col_ptr + 1, 1, col_ptr + 1, "กล่อง", header_fmt)

                        # เขียนข้อมูล
                        row_ptr = 2
                        for i, row_data in matrix.iterrows():
                            worksheet.write(row_ptr, 0, i + 1, data_fmt)
                            worksheet.write(row_ptr, 1, row_data['TRIP'], data_fmt) # ใส่รหัสจากแถบสีแดง
                            worksheet.write(row_ptr, 2, row_data['STORE NAME'], data_fmt)
                            
                            d_col = 3
                            for p in products:
                                worksheet.write(row_ptr, d_col, row_data[p], data_fmt)
                                worksheet.write(row_ptr, d_col + 1, "", data_fmt)
                                d_col += 2
                            row_ptr += 1

                        # เพิ่ม TOTAL ท้ายตาราง
                        worksheet.merge_range(row_ptr, 0, row_ptr, 1, "TOTAL", total_fmt)
                        t_col = 3
                        for p in products:
                            worksheet.write(row_ptr, t_col, matrix[p].sum(), total_fmt)
                            worksheet.write(row_ptr, t_col + 1, "", total_fmt)
                            t_col += 2

                        worksheet.set_column('C:C', 35) # ขยายความกว้างชื่อสาขา
                        worksheet.set_row(0, 25)
                        worksheet.set_row(1, 25)

                    st.success("✅ แก้ไขให้ดึงรหัส TRIP จากแถบสีแดงเรียบร้อย!")
                    st.download_button("📥 ดาวน์โหลดไฟล์ v2.2", output.getvalue(), "Weight_Sheet_TripFixed.xlsx")
        except Exception as e:
            st.error(f"Error: {e}")