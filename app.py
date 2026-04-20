import streamlit as st
import pandas as pd
import io

# --- CONFIG & MODERN DARK THEME UI ---
st.set_page_config(page_title="BNN | Color Master", layout="wide")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Kanit:wght@300;400;500;600&display=swap');
    html, body, [class*="css"], .main { background-color: #0A0C10; color: #FFFFFF !important; font-family: 'Kanit', sans-serif; }
    .stButton > button { background: linear-gradient(45deg, #00F2FF, #7000FF); color: white; border-radius: 12px; padding: 12px; font-weight: 600; width: 100%; border: none; }
    </style>
    """, unsafe_allow_html=True)

st.title("🎨 ระบบกู้คืน Raw Data พร้อมจัดสีตามต้นฉบับ")

uploaded_file = st.file_uploader("📥 อัปโหลดไฟล์ใบเบิกเพื่อแปลงเป็นไฟล์สี (xlsx)", type="xlsx")

if uploaded_file:
    if st.button("🚀 ประมวลผลและใส่สีตาราง"):
        try:
            # 1. อ่านข้อมูลพื้นฐาน
            raw_excel = pd.read_excel(uploaded_file, header=None)
            header_idx = next((i for i, r in raw_excel.iterrows() if r.astype(str).str.contains('Description', case=False, na=False).any()), None)
            
            if header_idx is not None:
                df = pd.read_excel(uploaded_file, skiprows=header_idx)
                df.columns = [str(c).strip() for c in df.columns]
                
                static_cols = ['#', 'Item No.', 'Description', 'UNIT']
                store_cols = [c for c in df.columns if c not in static_cols and 'Unnamed' not in c]
                
                # เก็บ Mapping ทริปและชื่อสาขา
                trip_map = {s: df[s].iloc[0] for s in store_cols}
                name_map = {s: (df[s].iloc[1] if len(df) > 1 else s) for s in store_cols}

                # 2. คัดแยกและเตรียมข้อมูล
                all_data = []
                for _, row in df.iterrows():
                    item = row.get('Description')
                    unit = str(row.get('UNIT', '')).strip()
                    if pd.isna(item) or str(item).strip() in ['', '0', '0.0']: continue
                    
                    for store in store_cols:
                        qty = row[store]
                        if pd.notna(qty) and isinstance(qty, (int, float)) and qty > 0:
                            all_data.append({
                                'STORE ID': store, 'STORE NAME': name_map.get(store),
                                'Trip': trip_map.get(store), 'Product': item, 'Qty': qty, 'Unit': unit
                            })
                
                if all_data:
                    full_df = pd.DataFrame(all_data)
                    
                    # แยกกลุ่มข้อมูลเพื่อทำชีท
                    weight_list = full_df[full_df['Unit'].str.contains('กิโลกรัม|กรัม|kg|g', na=False)]
                    box_list = full_df[~full_df['Unit'].str.contains('กิโลกรัม|กรัม|kg|g', na=False)]

                    def build_matrix(src_df):
                        if src_df.empty: return pd.DataFrame()
                        mx = src_df.pivot_table(index=['STORE ID', 'STORE NAME', 'Trip'], 
                                               columns='Product', values='Qty', aggfunc='sum').fillna(0).reset_index()
                        mx.columns.name = None
                        mx.insert(0, 'No.', range(1, len(mx) + 1))
                        return mx

                    final_weight = build_matrix(weight_list)
                    final_box = build_matrix(box_list)
                    final_order = build_matrix(full_df)

                    # 3. การเขียนไฟล์ Excel พร้อมจัดสี (XlsxWriter)
                    output = io.BytesIO()
                    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                        sheets = {
                            'น้ำหนัก': final_weight,
                            'จัดกล่อง': final_box,
                            'Order': final_order
                        }
                        
                        for sheet_name, data in sheets.items():
                            if data.empty: continue
                            data.to_excel(writer, sheet_name=sheet_name, index=False)
                            
                            workbook = writer.book
                            worksheet = writer.sheets[sheet_name]

                            # --- กำหนดสีต่างๆ (Color Codes) ---
                            header_fmt = workbook.add_format({'bold': True, 'bg_color': '#FFFF00', 'border': 1, 'align': 'center'}) # สีเหลือง
                            store_id_fmt = workbook.add_format({'bg_color': '#92D050', 'border': 1}) # สีเขียว
                            trip_fmt = workbook.add_format({'bg_color': '#FFEB9C', 'border': 1}) # สีเหลืองอ่อน
                            number_fmt = workbook.add_format({'border': 1, 'align': 'center'})

                            # พ่นสีหัวตาราง
                            for col_num, value in enumerate(data.columns.values):
                                worksheet.write(0, col_num, value, header_fmt)
                            
                            # พ่นสีคอลัมน์ข้อมูล (จัดตามกลุ่ม)
                            for row_num in range(1, len(data) + 1):
                                worksheet.write(row_num, 0, data.iloc[row_num-1, 0], number_fmt)     # No.
                                worksheet.write(row_num, 1, data.iloc[row_num-1, 1], store_id_fmt)   # STORE ID
                                worksheet.write(row_num, 3, data.iloc[row_num-1, 3], trip_fmt)       # Trip

                            # ปรับความกว้างอัตโนมัติ
                            worksheet.set_column('A:A', 5)
                            worksheet.set_column('B:D', 25)
                            worksheet.set_column('E:ZZ', 15)

                    st.success("✨ ประมวลผลและจัดสีตามต้นฉบับเสร็จสมบูรณ์!")
                    st.download_button("📥 ดาวน์โหลดไฟล์ (สีสวยตามสั่ง)", output.getvalue(), "BNN_Color_Report.xlsx")
                else:
                    st.warning("ไม่พบยอดการสั่งซื้อ")
            else:
                st.error("ไม่พบคอลัมน์ 'Description'")
        except Exception as e:
            st.error(f"Error: {e}")