import streamlit as st
import pandas as pd
import io

# --- UI CONFIG ---
st.set_page_config(page_title="BNN | 3-Sheet Fix v2.7", layout="wide")
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Kanit:wght@300;400;500;600&display=swap');
    html, body, [class*="css"], .main { background-color: #0A0C10; color: #FFFFFF !important; font-family: 'Kanit', sans-serif; }
    div.stButton > button { background: #FFD60A; color: black; border-radius: 8px; font-weight: bold; width: 100%; border: none; height: 50px; }
    </style>
    """, unsafe_allow_html=True)

st.title("🥩 ระบบจัดการใบเบิก (แก้ไขชีท 2 และ 3 ให้เหมือนชีทแรก)")

file = st.file_uploader("📥 อัปโหลดไฟล์ใบเบิกสินค้า (Raw Data)", type=["xlsx", "csv"])

if file:
    if st.button("🔍 ประมวลผลและสร้าง Preview"):
        try:
            # 1. การอ่านข้อมูล
            if file.name.endswith('.csv'):
                raw_df = pd.read_csv(file, header=None)
            else:
                raw_df = pd.read_excel(file, header=None)
            
            header_row_idx = next((i for i, r in raw_df.iterrows() if r.astype(str).str.contains('Description', na=False).any()), None)
            
            if header_row_idx is not None:
                thai_names_row = raw_df.iloc[header_row_idx]
                trip_codes_row = raw_df.iloc[header_row_idx + 1] # แถบสีแดง
                df_clean = raw_df.iloc[header_row_idx:].copy()
                df_clean.columns = df_clean.iloc[0]
                df_clean = df_clean.iloc[1:].reset_index(drop=True)
                df_clean.columns = [str(c).strip() for c in df_clean.columns]
                
                store_cols = [c for c in df_clean.columns[4:] if "Unnamed" not in c]

                # 2. เตรียม Data รายบรรทัด
                all_data = []
                for idx, row in df_clean.iterrows():
                    product = str(row.get('Description', '')).strip()
                    if product in ['', 'nan', '0', '0.0'] or 'Description' in product: continue
                    
                    for col in store_cols:
                        qty = row[col]
                        try:
                            qty_num = float(qty)
                            if qty_num > 0:
                                col_idx = df_clean.columns.get_loc(col)
                                all_data.append({
                                    'TRIP': str(trip_codes_row[col_idx]).strip() if pd.notna(trip_codes_row[col_idx]) else "-",
                                    'STORE NAME': col,
                                    'Product': product,
                                    'Qty': qty_num
                                })
                        except: continue

                if all_data:
                    full_df = pd.DataFrame(all_data)
                    meat_keywords = ['เนื้อ', 'หมู', 'Meat', 'Pork']
                    
                    # แบ่งกลุ่มข้อมูล 3 ชีท
                    d_weight = full_df[full_df['Product'].str.contains('|'.join(meat_keywords), na=False)]
                    d_box = full_df[~full_df['Product'].str.contains('|'.join(meat_keywords), na=False)]
                    d_order = full_df

                    def get_matrix(df_src):
                        if df_src.empty: return pd.DataFrame()
                        return df_src.pivot_table(index=['TRIP', 'STORE NAME'], columns='Product', values='Qty', aggfunc='sum').fillna(0).reset_index()

                    m_weight = get_matrix(d_weight)
                    m_box = get_matrix(d_box)
                    m_order = get_matrix(d_order)

                    # --- UI: Preview ---
                    tab1, tab2, tab3 = st.tabs(["📋 น้ำหนัก", "📦 จัดกล่อง", "📑 Order ทั้งหมด"])
                    with tab1: st.dataframe(m_weight, use_container_width=True)
                    with tab2: st.dataframe(m_box, use_container_width=True)
                    with tab3: st.dataframe(m_order, use_container_width=True)

                    # --- 3. สร้าง Excel (ล็อค Format เดียวกันทุกชีท) ---
                    output = io.BytesIO()
                    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                        workbook = writer.book
                        header_fmt = workbook.add_format({'bold': True, 'align': 'center', 'valign': 'vcenter', 'bg_color': '#FFFF00', 'border': 1, 'text_wrap': True})
                        data_fmt = workbook.add_format({'border': 1, 'align': 'center'})
                        total_fmt = workbook.add_format({'bold': True, 'bg_color': '#E2EFDA', 'border': 1})

                        for s_name, m_data in [("น้ำหนัก", m_weight), ("จัดกล่อง", m_box), ("Order", m_order)]:
                            if m_data.empty: continue
                            ws = workbook.add_worksheet(s_name)
                            
                            # หัวตารางหลัก
                            ws.merge_range(0, 0, 1, 0, "No.", header_fmt)
                            ws.merge_range(0, 1, 1, 1, "TRIP", header_fmt)
                            ws.merge_range(0, 2, 1, 2, "STORE NAME", header_fmt)

                            prods = [p for p in m_data.columns if p not in ['TRIP', 'STORE NAME']]
                            c_ptr = 3
                            for p in prods:
                                # หัวตารางย่อย จำนวนสั่ง/ชื่อสินค้า + จ่ายจริง
                                ws.write(0, c_ptr, "จำนวนสั่ง", header_fmt)
                                ws.write(1, c_ptr, p, header_fmt)
                                ws.merge_range(0, c_ptr+1, 1, c_ptr+1, "จ่ายจริง", header_fmt)
                                c_ptr += 2
                            
                            ws.merge_range(0, c_ptr, 1, c_ptr, "ตะกร้า", header_fmt)
                            ws.merge_range(0, c_ptr+1, 1, c_ptr+1, "กล่อง", header_fmt)

                            # เขียนข้อมูล
                            for i, row in m_data.iterrows():
                                curr_r = i + 2
                                ws.write(curr_r, 0, i+1, data_fmt)
                                ws.write(curr_r, 1, row['TRIP'], data_fmt)
                                ws.write(curr_r, 2, row['STORE NAME'], data_fmt)
                                d_ptr = 3
                                for p in prods:
                                    ws.write(curr_r, d_ptr, row[p], data_fmt)
                                    ws.write(curr_r, d_ptr+1, "", data_fmt) # จ่ายจริง
                                    d_ptr += 2
                            
                            # แถว TOTAL
                            last_r = len(m_data) + 2
                            ws.merge_range(last_r, 0, last_r, 2, "TOTAL", total_fmt)
                            t_ptr = 3
                            for p in prods:
                                ws.write(last_r, t_ptr, m_data[p].sum(), total_fmt)
                                ws.write(last_r, t_ptr+1, "", total_fmt)
                                t_ptr += 2
                            ws.set_column('C:C', 35)

                    st.divider()
                    st.success("✅ แก้ไขชีทจัดกล่อง และ Order ให้มีหัวตาราง 2 แถวและช่องจ่ายจริงเรียบร้อยแล้ว!")
                    st.download_button("📥 ดาวน์โหลดไฟล์ Excel (แก้ไขครบ 3 ชีท)", output.getvalue(), "BNN_Final_3Sheets.xlsx")
        except Exception as e:
            st.error(f"เกิดข้อผิดพลาด: {e}")