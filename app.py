import streamlit as st
import pandas as pd
import io

# --- UI Setup ---
st.set_page_config(page_title="BNN | Meat Order (Thai Name)", layout="wide")

st.title("🥩 ระบบแยกชีทน้ำหนัก (ดึงชื่อไทยจากคอลัมน์ E เป็นต้นไป)")

file = st.file_uploader("📥 อัปโหลดไฟล์ใบเบิกสินค้า (Raw Data)", type="xlsx")

if file:
    if st.button("🚀 ประมวลผลดึงชื่อภาษาไทย"):
        try:
            # 1. อ่านข้อมูลทั้งหมด
            raw_df = pd.read_excel(file, header=None)
            
            # ค้นหาแถวที่มีคำว่า 'Description' เพื่อหาจุดเริ่มของตาราง
            desc_row_idx = next((i for i, r in raw_df.iterrows() if r.astype(str).str.contains('Description', na=False).any()), None)
            
            if desc_row_idx is not None:
                # ชื่อสาขาภาษาไทยมักจะอยู่ 'เหนือ' แถว Description (Header เอียงๆ)
                # ในรูป image_dc3388.png ชื่อภาษาไทยจะอยู่ที่ row เดียวกับ Description แต่อยู่คนละบรรทัดย่อย
                # หรืออยู่แถวก่อนหน้า 1 แถว
                
                # อ่านข้อมูลจริงโดยข้าม Header ส่วนบน
                df = pd.read_excel(file, skiprows=desc_row_idx)
                
                # กำหนดคอลัมน์เริ่มต้น (คอลัมน์ E คือ index ที่ 4)
                store_columns = df.columns[4:] 
                
                # --- สร้าง Mapping ชื่อสาขา ---
                # จากรูป image_dc3388.png: 
                # - แถวที่ 0 (ของ df) คือรหัสภาษาอังกฤษในแถบสีแดง (ALR, BBK, BCP...)
                # - ชื่อภาษาไทยจะอยู่ที่ Column Header ของไฟล์ต้นฉบับ
                name_map = {}
                for col in store_columns:
                    # พยายามดึงชื่อจากหัวคอลัมน์ที่อ่านมา (ปกติ pandas จะอ่านชื่อไทยมาเป็นหัวตาราง)
                    name_map[col] = str(col).strip() if "Unnamed" not in str(col) else "ไม่ทราบชื่อ"

                # 2. แปลงข้อมูลเป็นรายบรรทัด (Long Format)
                all_rows = []
                for _, row in df.iterrows():
                    product = str(row.get('Description', '')).strip()
                    unit = str(row.get('UNIT', '')).strip()
                    
                    # ข้ามแถวที่ไม่ใช่สินค้า
                    if product in ['', 'nan', '0', '0.0'] or 'Description' in product: continue
                    
                    for store_col in store_columns:
                        qty = row[store_col]
                        if pd.notna(qty) and isinstance(qty, (int, float)) and qty > 0:
                            all_rows.append({
                                'STORE NAME': name_map.get(store_col), # ชื่อภาษาไทยจากหัวตาราง
                                'Product': product,
                                'Qty': qty,
                                'Unit': unit
                            })
                
                if all_rows:
                    full_df = pd.DataFrame(all_rows)
                    # กรองเฉพาะ เนื้อ/หมู สำหรับชีทน้ำหนัก
                    weight_df = full_df[full_df['Product'].str.contains('เนื้อ|หมู', na=False)]
                    
                    # 3. จัดรูปตาราง Matrix (Pivot Table)
                    if not weight_df.empty:
                        matrix = weight_df.pivot_table(index='STORE NAME', columns='Product', values='Qty', aggfunc='sum').fillna(0).reset_index()
                        
                        # เพิ่มคอลัมน์ 'จ่ายจริง' ขนาบข้างตามตัวอย่าง
                        final_cols = ['STORE NAME']
                        for p in matrix.columns:
                            if p != 'STORE NAME':
                                final_cols.append(p)
                                matrix[f'จ่ายจริง_{p}'] = ""
                                final_cols.append(f'จ่ายจริง_{p}')
                        
                        matrix = matrix[final_cols]
                        matrix.insert(0, 'No.', range(1, len(matrix) + 1))

                        # 4. สร้างไฟล์ Excel
                        output = io.BytesIO()
                        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                            matrix.to_excel(writer, sheet_name='น้ำหนัก', index=False)
                            
                            workbook = writer.book
                            worksheet = writer.sheets['น้ำหนัก']
                            header_fmt = workbook.add_format({'bold': True, 'bg_color': '#FFFF00', 'border': 1, 'align': 'center'})
                            
                            # ปรับแต่งหัวตารางสีเหลือง
                            for col_num, value in enumerate(matrix.columns.values):
                                worksheet.write(0, col_num, value.replace('จ่ายจริง_', 'จ่ายจริง\n'), header_fmt)
                            
                            worksheet.set_column('B:B', 30) # ขยายช่องชื่อสาขาไทย

                        st.success("✅ ดึงข้อมูลจากคอลัมน์ E เรียบร้อยแล้ว!")
                        st.download_button("📥 ดาวน์โหลดไฟล์ชีทน้ำหนัก", output.getvalue(), "Weight_Sheet_ThaiName.xlsx")
                else:
                    st.warning("ไม่พบยอดการสั่งซื้อในคอลัมน์ E เป็นต้นไป")
            else:
                st.error("ไม่พบคอลัมน์ Description ในไฟล์")
        except Exception as e:
            st.error(f"Error: {e}")