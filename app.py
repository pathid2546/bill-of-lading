import streamlit as st
import pandas as pd
import io

# --- UI CONFIG ---
st.set_page_config(page_title="BNN | System v3.1", layout="wide")
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Kanit:wght@300;400;500;600&display=swap');
    html, body, [class*="css"], .main { background-color: #0A0C10; color: #FFFFFF !important; font-family: 'Kanit', sans-serif; }
    div.stButton > button { background: #FFD60A; color: black; border-radius: 8px; font-weight: bold; width: 100%; border: none; height: 50px; }
    </style>
    """, unsafe_allow_html=True)

st.title("🥩 ระบบจัดการใบเบิก v3.1 (แก้ไข Order & เพิ่ม Total จัดกล่อง)")

file = st.file_uploader("📥 อัปโหลดไฟล์ใบเบิกสินค้า (Raw Data)", type=["xlsx", "csv"])

if file:
    if st.button("🚀 ประมวลผลและสร้าง Preview"):
        try:
            # 1. อ่านข้อมูล
            raw_df = pd.read_csv(file, header=None) if file.name.endswith('.csv') else pd.read_excel(file, header=None)
            header_row_idx = next((i for i, r in raw_df.iterrows() if r.astype(str).str.contains('Description', na=False).any()), None)
            
            if header_row_idx is not None:
                trip_codes_row = raw_df.iloc[header_row_idx + 1]
                df_clean = raw_df.iloc[header_row_idx:].copy()
                df_clean.columns = df_clean.iloc[0]; df_clean = df_clean.iloc[1:].reset_index(drop=True)
                df_clean.columns = [str(c).strip() for c in df_clean.columns]
                store_cols = [c for c in df_clean.columns[4:] if "Unnamed" not in c]

                # 2. จัดการ Data
                all_rows = []
                for _, row in df_clean.iterrows():
                    product = str(row.get('Description', '')).strip()
                    if product in ['', 'nan', '0', '0.0'] or 'Description' in product: continue
                    for col in store_cols:
                        try:
                            qty = float(row[col])
                            if qty > 0:
                                c_idx = df_clean.columns.get_loc(col)
                                all_rows.append({
                                    'TRIP': str(trip_codes_row[c_idx]).strip() if pd.notna(trip_codes_row[c_idx]) else "-",
                                    'STORE NAME': col,
                                    'Product': product,
                                    'Qty': qty
                                })
                        except: continue

                if all_rows:
                    full_df = pd.DataFrame(all_rows)
                    meat_kw = ['เนื้อ', 'หมู', 'Meat', 'Pork']
                    
                    # เตรียม Matrix
                    m_weight = full_df[full_df['Product'].str.contains('|'.join(meat_kw), na=False)].pivot_table(index=['TRIP', 'STORE NAME'], columns='Product', values='Qty', aggfunc='sum').fillna(0).reset_index()
                    m_box = full_df[~full_df['Product'].str.contains('|'.join(meat_kw), na=False)].pivot_table(index=['TRIP', 'STORE NAME'], columns='Product', values='Qty', aggfunc='sum').fillna(0).reset_index()
                    m_order = full_df.pivot_table(index=['TRIP', 'STORE NAME'], columns='Product', values='Qty', aggfunc='sum').fillna(0).reset_index()

                    # --- 3. สร้าง Excel ---
                    output = io.BytesIO()
                    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                        wb = writer.book
                        h_fmt = wb.add_format({'bold': True, 'align': 'center', 'valign': 'vcenter', 'bg_color': '#FFFF00', 'border': 1, 'text_wrap': True})
                        d_fmt = wb.add_format({'border': 1, 'align': 'center'})
                        sum_fmt = wb.add_format({'bold': True, 'bg_color': '#E2EFDA', 'border': 1, 'num_format': '#,##0'})

                        # ฟังก์ชันสร้างชีทแบบมี "จ่ายจริง" (สำหรับ น้ำหนัก และ Order)
                        def write_sheet_with_pay(sheet_name, data_matrix):
                            ws = wb.add_worksheet(sheet_name)
                            ws.merge_range(0,0,1,0,"No.",h_fmt); ws.merge_range(0,1,1,1,"TRIP",h_fmt); ws.merge_range(0,2,1,2,"STORE NAME",h_fmt)
                            prods = [p for p in data_matrix.columns if p not in ['TRIP', 'STORE NAME']]
                            c_ptr = 3
                            for p in prods:
                                ws.write(0, c_ptr, "จำนวนสั่ง", h_fmt); ws.write(1, c_ptr, p, h_fmt)
                                ws.merge_range(0, c_ptr+1, 1, c_ptr+1, "จ่ายจริง", h_fmt); c_ptr += 2
                            ws.merge_range(0, c_ptr, 1, c_ptr, "ตะกร้า", h_fmt); ws.merge_range(0, c_ptr+1, 1, c_ptr+1, "กล่อง", h_fmt)
                            for i, row in data_matrix.iterrows():
                                r = i+2; ws.write(r,0,i+1,d_fmt); ws.write(r,1,row['TRIP'],d_fmt); ws.write(r,2,row['STORE NAME'],d_fmt)
                                d_ptr = 3
                                for p in prods:
                                    ws.write(r, d_ptr, row[p], d_fmt); ws.write(r, d_ptr+1, "", d_fmt); d_ptr += 2
                            # ผลรวมท้ายตาราง
                            last_r = len(data_matrix)+2
                            ws.merge_range(last_r, 0, last_r, 2, "TOTAL", sum_fmt)
                            t_ptr = 3
                            for p in prods:
                                ws.write(last_r, t_ptr, data_matrix[p].sum(), sum_fmt); ws.write(last_r, t_ptr+1, "", sum_fmt); t_ptr += 2
                            ws.set_column('C:C', 35)

                        # เขียนชีท 1 และ 3 (โครงสร้างเหมือนกัน)
                        write_sheet_with_pay("น้ำหนัก", m_weight)
                        write_sheet_with_pay("Order", m_order)

                        # --- ชีท 2: จัดกล่อง (แถวเดียว + รวมท้ายตารางแนวตั้ง) ---
                        if not m_box.empty:
                            ws2 = wb.add_worksheet("จัดกล่อง")
                            ws2.write(0,0,"No.",h_fmt); ws2.write(0,1,"TRIP",h_fmt); ws2.write(0,2,"STORE NAME",h_fmt)
                            prods_box = [p for p in m_box.columns if p not in ['TRIP', 'STORE NAME']]
                            for idx, p in enumerate(prods_box): ws2.write(0, idx+3, p, h_fmt)
                            sum_col = len(prods_box)+3; ws2.write(0, sum_col, "รวมจำนวน", h_fmt)
                            for i, row in m_box.iterrows():
                                r = i+1; ws2.write(r,0,i+1,d_fmt); ws2.write(r,1,row['TRIP'],d_fmt); ws2.write(r,2,row['STORE NAME'],d_fmt)
                                r_sum = 0
                                for idx, p in enumerate(prods_box):
                                    ws2.write(r, idx+3, row[p], d_fmt); r_sum += row[p]
                                ws2.write(r, sum_col, r_sum, sum_fmt)
                            # เพิ่มแถว TOTAL แนวตั้ง
                            last_r_box = len(m_box)+1
                            ws2.write(last_r_box, 2, "TOTAL", sum_fmt)
                            for idx, p in enumerate(prods_box):
                                ws2.write(last_r_box, idx+3, m_box[p].sum(), sum_fmt)
                            ws2.write(last_r_box, sum_col, m_box[prods_box].sum().sum(), sum_fmt)
                            ws2.set_column('C:C', 35)

                    st.success("✅ แก้ไขชีท Order ให้มี 'จ่ายจริง' และเพิ่ม 'Total' ในชีทจัดกล่องเรียบร้อย!")
                    st.download_button("📥 ดาวน์โหลดไฟล์ v3.1", output.getvalue(), "BNN_Correct_Format.xlsx")
        except Exception as e:
            st.error(f"Error: {e}")