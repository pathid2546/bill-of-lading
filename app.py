import streamlit as st
import pandas as pd
import io

# --- UI Setup ---
st.set_page_config(page_title="BNN | Full Name Meat Order", layout="wide")
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Kanit:wght@300;400;500;600&display=swap');
    html, body, [class*="css"], .main { background-color: #0A0C10; color: #FFFFFF !important; font-family: 'Kanit', sans-serif; }
    div.stButton > button { background: #FFD60A; color: black; border-radius: 8px; font-weight: bold; width: 100%; border: none; }
    </style>
    """, unsafe_allow_html=True)

st.title("🥩 ระบบแยกชีท (น้ำหนัก: เนื้อ/หมู + ชื่อสาขาภาษาไทย)")

file = st.file_uploader("📥 อัปโหลดไฟล์ใบเบิกสินค้า", type="xlsx")

if file:
    if st.button("🚀 ประมวลผลและจัดรูปแบบ (ชื่อสาขาภาษาไทย)"):
        try:
            # 1. อ่านข้อมูลต้นทาง
            raw_excel = pd.read_excel(file, header=None)
            header_idx = next((i for i, r in raw_excel.iterrows() if r.astype(str).str.contains('Description', case=False, na=False).any()), None)
            
            if header_idx is not None:
                df = pd.read_excel(file, skiprows=header_idx)
                df.columns = [str(c).strip() for c in df.columns]
                
                static_cols = ['#', 'Item No.', 'Description', 'UNIT']
                store_cols = [c for c in df.columns if c not in static_cols and 'Unnamed' not in c]
                
                # Mapping ข้อมูล Trip และ ชื่อสาขา (ภาษาไทย)
                trip_map = {s: df[s].iloc[0] for s in store_cols}
                name_map = {s: (df[s].iloc[1] if len(df) > 1 else s) for s in store_cols}

                # 2. เตรียมข้อมูลรายบรรทัด
                all_rows = []
                for _, row in df.iterrows():
                    item = str(row.get('Description', ''))
                    unit = str(row.get('UNIT', '')).strip()
                    if item in ['', 'nan', '0', '0.0']: continue
                    
                    for store in store_cols:
                        qty = row[store]
                        if pd.notna(qty) and isinstance(qty, (int, float)) and qty > 0:
                            all_rows.append({
                                'TRIP': trip_map.get(store),
                                'STORE NAME': name_map.get(store), # ใช้ชื่อสาขาภาษาไทย
                                'Product': item,
                                'Qty': qty,
                                'Unit': unit
                            })
                
                if all_rows:
                    full_df = pd.DataFrame(all_rows)
                    # กรองเฉพาะ เนื้อ และ หมู สำหรับชีทน้ำหนัก
                    meat_pork_df = full_df[full_df['Product'].str.contains('เนื้อ|หมู', na=False)]
                    box_items_df = full_df[~full_df['Product'].str.contains('เนื้อ|หมู', na=False)]

                    # ฟังก์ชันสร้างตาราง Matrix พร้อมคอลัมน์เสริม
                    def build_final_matrix(src_df):
                        if src_df.empty: return pd.DataFrame()
                        mx = src_df.pivot_table(index=['TRIP', 'STORE NAME'], 
                                               columns='Product', values='Qty', aggfunc='sum').fillna(0).reset_index()
                        
                        final_styled = mx[['TRIP', 'STORE NAME']].copy()
                        for p_col in [c for c in mx.columns if c not in ['TRIP', 'STORE NAME']]:
                            final_styled[p_col] = mx[p_col]
                            final_styled[f'จ่ายจริง_{p_col}'] = "" # ช่องจ่ายจริงขนาบข้าง
                        
                        final_styled['ตะกร้า'] = "" #
                        final_styled['กล่อง'] = ""
                        final_styled.insert(0, 'No.', range(1, len(final_styled) + 1))
                        return final_styled

                    sheet_weight = build_final_matrix(meat_pork_df)
                    sheet_box = build_final_matrix(box_items_df)
                    sheet_order = build_final_matrix(full_df)

                    # 3. สร้าง Excel และละเลงสี
                    output = io.BytesIO()
                    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                        for s_name, s_df in [('น้ำหนัก', sheet_weight), ('จัดกล่อง', sheet_box), ('Order', sheet_order)]:
                            if s_df.empty: continue
                            s_df.to_excel(writer, sheet_name=s_name, index=False)
                            
                            workbook = writer.book
                            worksheet = writer.sheets[s_name]
                            
                            # Formats
                            header_fmt = workbook.add_format({'bold': True, 'bg_color': '#FFFF00', 'border': 1, 'align': 'center', 'valign': 'vcenter', 'text_wrap': True})
                            trip_fmt = workbook.add_format({'bg_color': '#FFFFCC', 'border': 1, 'align': 'center'})
                            name_fmt = workbook.add_format({'bg_color': '#E2EFDA', 'border': 1})
                            cell_fmt = workbook.add_format({'border': 1, 'align': 'center'})

                            # เขียนหัวตารางพร้อมสีเหลือง
                            for col_num, value in enumerate(s_df.columns.values):
                                clean_name = value.replace('จ่ายจริง_', 'จ่ายจริง\n')
                                worksheet.write(0, col_num, clean_name, header_fmt)
                            
                            # เขียนเนื้อหาพร้อมสี Trip และ Store Name
                            for row_num in range(1, len(s_df) + 1):
                                worksheet.write(row_num, 0, s_df.iloc[row_num-1, 0], cell_fmt) # No.
                                worksheet.write(row_num, 1, s_df.iloc[row_num-1, 1], trip_fmt) # TRIP
                                worksheet.write(row_num, 2, s_df.iloc[row_num-1, 2], name_fmt) # STORE NAME (Thai)

                            # ปรับความกว้าง
                            worksheet.set_column('A:A', 5)
                            worksheet.set_column('B:B', 12)
                            worksheet.set_column('C:C', 35) # เผื่อชื่อสาขายาว
                            worksheet.set_column('D:ZZ', 12)
                            worksheet.set_row(0, 45)

                    st.success("✨ แก้ไขเรียบร้อย! ชื่อสาขาเป็นภาษาไทยแล้วครับ")
                    st.download_button("📥 ดาวน์โหลดไฟล์ (สีสวย-ชื่อไทย)", output.getvalue(), "BNN_ThaiName_Report.xlsx")
                else:
                    st.warning("ไม่พบข้อมูลการสั่งซื้อ")
            else:
                st.error("ไม่พบคอลัมน์ Description")
        except Exception as e:
            st.error(f"เกิดข้อผิดพลาด: {e}")