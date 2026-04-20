import streamlit as st
import pandas as pd
import io

# --- UI CONFIG ---
st.set_page_config(page_title="BNN | System v3.0", layout="wide")
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Kanit:wght@300;400;500;600&display=swap');
    html, body, [class*="css"], .main { background-color: #0A0C10; color: #FFFFFF !important; font-family: 'Kanit', sans-serif; }
    div.stButton > button { background: #FFD60A; color: black; border-radius: 8px; font-weight: bold; width: 100%; border: none; height: 50px; }
    </style>
    """, unsafe_allow_html=True)

st.title("🥩 ระบบจัดการใบเบิก v3.0 (น้ำหนัก / จัดกล่อง / Order-Input)")

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
                                    'TRIP': str(trip_codes_row[c_idx]).strip(),
                                    'STORE NAME': col,
                                    'Product': product,
                                    'Qty': qty
                                })
                        except: continue

                if all_rows:
                    full_df = pd.DataFrame(all_rows)
                    meat_kw = ['เนื้อ', 'หมู', 'Meat', 'Pork']
                    
                    # เตรียมข้อมูล 3 แบบ
                    m_weight = full_df[full_df['Product'].str.contains('|'.join(meat_kw), na=False)].pivot_table(index=['TRIP', 'STORE NAME'], columns='Product', values='Qty', aggfunc='sum').fillna(0).reset_index()
                    m_box = full_df[~full_df['Product'].str.contains('|'.join(meat_kw), na=False)].pivot_table(index=['TRIP', 'STORE NAME'], columns='Product', values='Qty', aggfunc='sum').fillna(0).reset_index()
                    
                    # ชีท Order แบบ Input (แนวตั้ง)
                    order_input = full_df[['TRIP', 'STORE NAME', 'Product', 'Qty']].copy()

                    # --- UI: Preview ---
                    t1, t2, t3 = st.tabs(["📋 น้ำหนัก (มีจ่ายจริง)", "📦 จัดกล่อง (รวมผลรวม)", "📑 Order (แบบ Input)"])
                    with t1: st.dataframe(m_weight)
                    with t2: st.dataframe(m_box)
                    with t3: st.dataframe(order_input)

                    # --- 3. สร้าง Excel ---
                    output = io.BytesIO()
                    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                        wb = writer.book
                        h_fmt = wb.add_format({'bold': True, 'align': 'center', 'valign': 'vcenter', 'bg_color': '#FFFF00', 'border': 1})
                        d_fmt = wb.add_format({'border': 1, 'align': 'center'})
                        sum_fmt = wb.add_format({'bold': True, 'bg_color': '#E2EFDA', 'border': 1})

                        # --- ชีท 1: น้ำหนัก (หัว 2 แถว + จ่ายจริง) ---
                        if not m_weight.empty:
                            ws1 = wb.add_worksheet("น้ำหนัก")
                            ws1.merge_range(0,0,1,0,"No.",h_fmt); ws1.merge_range(0,1,1,1,"TRIP",h_fmt); ws1.merge_range(0,2,1,2,"STORE NAME",h_fmt)
                            prods = [p for p in m_weight.columns if p not in ['TRIP', 'STORE NAME']]
                            c_ptr = 3
                            for p in prods:
                                ws1.write(0, c_ptr, "จำนวนสั่ง", h_fmt); ws1.write(1, c_ptr, p, h_fmt)
                                ws1.merge_range(0, c_ptr+1, 1, c_ptr+1, "จ่ายจริง", h_fmt); c_ptr += 2
                            for i, row in m_weight.iterrows():
                                r = i+2; ws1.write(r,0,i+1,d_fmt); ws1.write(r,1,row['TRIP'],d_fmt); ws1.write(r,2,row['STORE NAME'],d_fmt)
                                d_ptr = 3
                                for p in prods:
                                    ws1.write(r, d_ptr, row[p], d_fmt); ws1.write(r, d_ptr+1, "", d_fmt); d_ptr += 2

                        # --- ชีท 2: จัดกล่อง (แถวเดียว + รวมแนวนอน) ---
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

                        # --- ชีท 3: Order (แบบ Input แนวตั้ง) ---
                        ws3 = wb.add_worksheet("Order")
                        headers = ["TRIP", "STORE NAME", "Product", "Qty"]
                        for c, h in enumerate(headers): ws3.write(0, c, h, h_fmt)
                        for i, row in order_input.iterrows():
                            for c, col_name in enumerate(headers):
                                ws3.write(i+1, c, row[col_name], d_fmt)

                        ws1.set_column('C:C', 35); ws2.set_column('C:C', 35); ws3.set_column('B:C', 30)

                    st.success("✅ ปรับปรุงชีท Order เป็นแบบ Input เรียบร้อยแล้ว!")
                    st.download_button("📥 ดาวน์โหลดไฟล์ v3.0", output.getvalue(), "BNN_Final_v3.xlsx")
        except Exception as e:
            st.error(f"Error: {e}")