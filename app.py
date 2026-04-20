import streamlit as st
import pandas as pd
import io

# --- CONFIG UI ---
st.set_page_config(page_title="BNN | Meat & Pork Specialist", layout="wide")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Kanit:wght@300;400;500;600&display=swap');
    html, body, [class*="css"], .main { background-color: #0A0C10; color: #FFFFFF !important; font-family: 'Kanit', sans-serif; }
    div.stButton > button { background: linear-gradient(45deg, #FFD60A, #FFA000); color: black !important; border: none; border-radius: 12px; font-weight: bold; width: 100%; }
    </style>
    """, unsafe_allow_html=True)

st.title("🥩 ระบบแยกชีท: เน้นเนื้อและหมู (Custom Layout)")

file = st.file_uploader("📥 อัปโหลดไฟล์ Raw Data", type="xlsx")

if file:
    if st.button("🚀 ประมวลผลแบบแยกสีตามรูปเป๊ะ"):
        try:
            # 1. อ่านและเตรียมข้อมูล
            raw_excel = pd.read_excel(file, header=None)
            header_idx = next((i for i, r in raw_excel.iterrows() if r.astype(str).str.contains('Description', case=False, na=False).any()), None)
            
            if header_idx is not None:
                df = pd.read_excel(file, skiprows=header_idx)
                df.columns = [str(c).strip() for c in df.columns]
                
                static_cols = ['#', 'Item No.', 'Description', 'UNIT']
                store_cols = [c for c in df.columns if c not in static_cols and 'Unnamed' not in c]
                
                trip_map = {s: df[s].iloc[0] for s in store_cols}
                name_map = {s: (df[s].iloc[1] if len(df) > 1 else s) for s in store_cols}

                # 2. เก็บข้อมูลเข้าระบบ
                all_rows = []
                for _, row in df.iterrows():
                    item = str(row.get('Description', ''))
                    unit = str(row.get('UNIT', '')).strip()
                    if item in ['', 'nan', '0', '0.0']: continue
                    
                    for store in store_cols:
                        qty = row[store]
                        if pd.notna(qty) and isinstance(qty, (int, float)) and qty > 0:
                            all_rows.append({
                                'STORE ID': store, 'STORE NAME': name_map.get(store),
                                'TRIP': trip_map.get(store), 'Product': item, 'Qty': qty, 'Unit': unit
                            })
                
                if all_rows:
                    full_df = pd.DataFrame(all_rows)
                    
                    # --- Logic กรองสินค้าสำหรับชีท "น้ำหนัก" (เอาแค่ เนื้อ และ หมู) ---
                    meat_pork_df = full_df[full_df['Product'].str.contains('เนื้อ|หมู', na=False)]
                    
                    # --- Logic กรองสำหรับชีท "จัดกล่อง" (ที่เหลือทั้งหมดที่ไม่ใช่เนื้อ/หมู) ---
                    box_items_df = full_df[~full_df['Product'].str.contains('เนื้อ|หมู', na=False)]

                    # ฟังก์ชันสร้าง Matrix พร้อมคอลัมน์เสริม "จ่ายจริง/ตะกร้า/กล่อง"
                    def build_styled_matrix(src_df, is_weight_sheet=False):
                        if src_df.empty: return pd.DataFrame()
                        
                        # Pivot ข้อมูล
                        mx = src_df.pivot_table(index=['TRIP', 'STORE NAME', 'STORE ID'], 
                                               columns='Product', values='Qty', aggfunc='sum').fillna(0).reset_index()
                        
                        # แทรกคอลัมน์ "จ่ายจริง" ต่อท้ายทุกสินค้า
                        final_cols = ['TRIP', 'STORE NAME']
                        product_cols = [c for c in mx.columns if c not in ['TRIP', 'STORE NAME', 'STORE ID']]
                        
                        styled_data = mx[['TRIP', 'STORE NAME']].copy()
                        for p_col in product_cols:
                            styled_data[p_col] = mx[p_col]
                            styled_data[f'จ่ายจริง_{p_col}'] = "" # ช่องว่างสำหรับเขียนมือ/เติมทีหลัง
                        
                        # เพิ่มคอลัมน์ปิดท้าย
                        styled_data['ตะกร้า'] = ""
                        styled_data['กล่อง'] = ""
                        styled_data.insert(0, 'No.', range(1, len(styled_data) + 1))
                        return styled_data

                    sheet_weight = build_styled_matrix(meat_pork_df, True)
                    sheet_box = build_styled_matrix(box_items_df)
                    sheet_order = build_styled_matrix(full_df)

                    # 3. สร้างไฟล์และละเลงสี
                    output = io.BytesIO()
                    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                        for s_name, s_df in [('น้ำหนัก', sheet_weight), ('จัดกล่อง', sheet_box), ('Order', sheet_order)]:
                            if s_df.empty: continue
                            s_df.to_excel(writer, sheet_name=s_name, index=False)
                            
                            workbook = writer.book
                            worksheet = writer.sheets[s_name]
                            
                            # Formats
                            header_fmt = workbook.add_format({'bold': True, 'bg_color': '#FFFF00', 'border': 1, 'align': 'center', 'valign': 'vcenter', 'text_wrap': True})
                            trip_fmt = workbook.add_format({'bg_color': '#FDFD96', 'border': 1, 'align': 'center'})
                            name_fmt = workbook.add_format({'bg_color': '#E2EFDA', 'border': 1})
                            qty_fmt = workbook.add_format({'border': 1, 'align': 'center', 'font_size': 12, 'bold': True})
                            
                            # พ่นสีหัวตาราง
                            for col_num, value in enumerate(s_df.columns.values):
                                display_name = value.replace('จ่ายจริง_', 'จ่ายจริง\n')
                                worksheet.write(0, col_num, display_name, header_fmt)
                            
                            # พ่นสีเนื้อหา
                            for row_num in range(1, len(s_df) + 1):
                                worksheet.write(row_num, 1, s_df.iloc[row_num-1, 1], trip_fmt) # TRIP
                                worksheet.write(row_num, 2, s_df.iloc[row_num-1, 2], name_fmt) # STORE NAME
                            
                            worksheet.set_column('A:A', 5)
                            worksheet.set_column('B:C', 30)
                            worksheet.set_column('D:ZZ', 12)
                            worksheet.set_row(0, 45) # ปรับความสูงหัวตารางรองรับ Text Wrap

                    st.success("✅ จัดเรียงสีและแยกกลุ่ม เนื้อ/หมู เรียบร้อยแล้ว!")
                    st.download_button("📥 ดาวน์โหลดไฟล์ (สีเป๊ะตามรูป)", output.getvalue(), "BNN_Final_Report.xlsx")
            else:
                st.error("ไม่พบคอลัมน์ Description")
        except Exception as e:
            st.error(f"Error: {e}")