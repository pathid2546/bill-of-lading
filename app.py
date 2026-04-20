import streamlit as st
import pandas as pd
import io

st.set_page_config(page_title="BNN | Meat Order v2.1", layout="wide")
st.title("🥩 ระบบใบน้ำหนัก (แก้ไขหัวตาราง 'จำนวนสั่ง/สินค้า' วางซ้อนกัน)")

file = st.file_uploader("📥 อัปโหลดไฟล์ใบเบิกสินค้า (Raw Data)", type="xlsx")

if file:
    if st.button("🚀 ประมวลผลไฟล์ตามรูปแบบเป๊ะๆ"):
        try:
            # 1. อ่านและเตรียมข้อมูล
            raw_df = pd.read_excel(file, header=None)
            desc_row_idx = next((i for i, r in raw_df.iterrows() if r.astype(str).str.contains('Description', na=False).any()), None)
            
            df = pd.read_excel(file, skiprows=desc_row_idx)
            store_columns = df.columns[4:] # เริ่มจากคอลัมน์ E
            
            all_rows = []
            for _, row in df.iterrows():
                product = str(row.get('Description', '')).strip()
                if product in ['', 'nan', '0', '0.0'] or 'Description' in product: continue
                
                for store_col in store_columns:
                    qty = row[store_col]
                    if pd.notna(qty) and isinstance(qty, (int, float)) and qty > 0:
                        all_rows.append({
                            'STORE NAME': str(store_col).strip(),
                            'Product': product,
                            'Qty': qty
                        })

            if all_rows:
                full_df = pd.DataFrame(all_rows)
                # กรองเฉพาะ เนื้อ/หมู
                weight_df = full_df[full_df['Product'].str.contains('เนื้อ|หมู', na=False)]
                
                matrix = weight_df.pivot_table(index='STORE NAME', columns='Product', values='Qty', aggfunc='sum').fillna(0).reset_index()
                products = [p for p in matrix.columns if p != 'STORE NAME']
                
                # --- สร้างไฟล์ Excel ด้วย XlsxWriter ---
                output = io.BytesIO()
                with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                    workbook = writer.book
                    worksheet = workbook.add_worksheet('น้ำหนัก')
                    
                    # Formats
                    header_fmt = workbook.add_format({'bold': True, 'align': 'center', 'valign': 'vcenter', 'bg_color': '#FFFF00', 'border': 1, 'text_wrap': True})
                    data_fmt = workbook.add_format({'border': 1, 'align': 'center'})
                    total_fmt = workbook.add_format({'bold': True, 'bg_color': '#E2EFDA', 'border': 1, 'num_format': '#,##0'})

                    # 2. เขียน Header 2 แถว
                    static_headers = ['No.', 'TRIP', 'STORE NAME']
                    for i, h in enumerate(static_headers):
                        worksheet.merge_range(0, i, 1, i, h, header_fmt)

                    col_idx = 3
                    for p in products:
                        # แถว 0: 'จำนวนสั่ง'
                        worksheet.write(0, col_idx, "จำนวนสั่ง", header_fmt)
                        # แถว 1: 'ชื่อสินค้า'
                        worksheet.write(1, col_idx, p, header_fmt)
                        # คอลัมน์ข้างๆ: 'จ่ายจริง' (Merge แถว 0-1 เข้าด้วยกัน)
                        worksheet.merge_range(0, col_idx + 1, 1, col_idx + 1, "จ่ายจริง", header_fmt)
                        col_idx += 2
                    
                    # เพิ่ม ตะกร้า/กล่อง ท้ายตาราง (สูง 2 แถว)
                    worksheet.merge_range(0, col_idx, 1, col_idx, "ตะกร้า", header_fmt)
                    worksheet.merge_range(0, col_idx + 1, 1, col_idx + 1, "กล่อง", header_fmt)

                    # 3. เขียนข้อมูล
                    current_row = 2
                    for i, row_data in matrix.iterrows():
                        worksheet.write(current_row, 0, i + 1, data_fmt) # No.
                        worksheet.write(current_row, 1, "-", data_fmt)    # Trip
                        worksheet.write(current_row, 2, row_data['STORE NAME'], data_fmt)
                        
                        data_col_idx = 3
                        for p in products:
                            worksheet.write(current_row, data_col_idx, row_data[p], data_fmt)
                            worksheet.write(current_row, data_col_idx + 1, "", data_fmt) # จ่ายจริง
                            data_col_idx += 2
                        
                        worksheet.write(current_row, data_col_idx, "", data_fmt) # ตะกร้า
                        worksheet.write(current_row, data_col_idx + 1, "", data_fmt) # กล่อง
                        current_row += 1

                    # 4. เพิ่มแถว TOTAL
                    worksheet.write(current_row, 2, "TOTAL", total_fmt)
                    total_col_idx = 3
                    for p in products:
                        total_val = matrix[p].sum()
                        worksheet.write(current_row, total_col_idx, total_val, total_fmt)
                        worksheet.write(current_row, total_col_idx + 1, "", total_fmt)
                        total_col_idx += 2

                    # ปรับความกว้างและความสูง
                    worksheet.set_column('C:C', 35) # Store Name
                    worksheet.set_column(3, total_col_idx, 12) # Product cols
                    worksheet.set_row(0, 30) # ปรับความสูงแถวหัวตาราง
                    worksheet.set_row(1, 30)

                st.success("✅ แก้ไขหัวตาราง 'จำนวนสั่ง' และ 'จ่ายจริง' เรียบร้อยครับ!")
                st.download_button("📥 ดาวน์โหลดชีทน้ำหนัก (v2.1)", output.getvalue(), "Weight_Sheet_Corrected.xlsx")
            else:
                st.warning("ไม่พบข้อมูลสินค้า")
        except Exception as e:
            st.error(f"เกิดข้อผิดพลาด: {e}")