import streamlit as st
import pandas as pd
import io
from streamlit_sortables import sort_items

# --- UI CONFIGURATION ---
st.set_page_config(page_title="Project น้องเดียร์ v16.0", layout="wide")

def local_css(main_color, font_family):
    st.markdown(f"""
        <style>
        @import url('https://fonts.googleapis.com/css2?family={font_family.replace(" ", "+")}:wght@300;400;600&display=swap');
        html, body, [class*="css"], .main {{ background-color: #0F1117; color: #E0E0E0 !important; font-family: '{font_family}', sans-serif; }}
        h1 {{ color: {main_color} !important; text-align: center; text-shadow: 2px 2px 10px {main_color}44; }}
        div.stButton > button {{
            background: linear-gradient(135deg, {main_color} 0%, #FF85A1 100%);
            color: white !important; border-radius: 12px; font-weight: bold; height: 60px; width: 100%;
        }}
        </style>
    """, unsafe_allow_html=True)

theme_color = st.sidebar.color_picker("ธีมสีหลัก", "#FF4B8B")
font_choice = st.sidebar.selectbox("เลือกฟอนต์", ["Kanit", "Mitr", "Sarabun"])
local_css(theme_color, font_choice)

st.title(f"💖 Project น้องเดียร์แปลงบิล v16.0")

if 'order_box' not in st.session_state: st.session_state.order_box = []
if 'order_total' not in st.session_state: st.session_state.order_total = []

tab_upload, tab_setting, tab_process = st.tabs(["📥 1. อัปโหลดไฟล์", "↕️ 2. ลากวางลำดับสินค้า", "🚀 3. ประมวลผล"])

with tab_upload:
    file = st.file_uploader("อัปโหลดไฟล์ Excel (ที่มีชีท Route)", type=["xlsx"])

if file:
    try:
        # 1. อ่านชีท Route
        route_df = pd.read_excel(file, sheet_name='Route', header=None)
        route_lookup = {str(r[0]).strip(): str(r[2]).strip() for _, r in route_df.iterrows() if pd.notna(r[0])}

        # 2. อ่านหน้าหลัก
        xls = pd.ExcelFile(file)
        main_sheet = xls.sheet_names[0]
        raw_df = pd.read_excel(file, sheet_name=main_sheet, header=None)

        header_idx = next((i for i, r in raw_df.iterrows() if r.astype(str).str.contains('Description', na=False).any()), None)
        
        if header_idx is not None:
            store_codes_row = raw_df.iloc[header_idx + 1]
            df_clean = raw_df.iloc[header_idx:].copy()
            df_clean.columns = df_clean.iloc[0]
            df_clean = df_clean.iloc[1:].reset_index(drop=True)
            store_columns = [c for c in df_clean.columns[4:] if "Unnamed" not in str(c)]

            all_rows = []
            original_order = [] 

            for _, row in df_clean.iterrows():
                product = str(row.get('Description', '')).strip()
                if product in ['', 'nan', '0', '0.0'] or 'Description' in product: continue
                if product not in original_order: original_order.append(product)

                for col_name in store_columns:
                    try:
                        qty = float(row[col_name])
                        if qty > 0:
                            col_idx = list(df_clean.columns).index(col_name)
                            current_store_code = str(store_codes_row[col_idx]).strip()
                            final_trip = route_lookup.get(current_store_code, "ไม่พบรหัส")
                            all_rows.append({'TRIP': final_trip, 'STORE NAME': col_name, 'Product': product, 'Qty': qty})
                    except: continue

            full_df = pd.DataFrame(all_rows)
            meat_kw = ['เนื้อ', 'หมู', 'Meat', 'Pork']
            
            init_box = [p for p in original_order if not any(kw in p for kw in meat_kw)]
            init_total = original_order

            if not st.session_state.order_box: st.session_state.order_box = init_box
            if not st.session_state.order_total: st.session_state.order_total = init_total

            with tab_setting:
                st.subheader("↕️ ลากวางสลับลำดับสินค้า")
                c1, c2 = st.columns(2)
                with c1: st.session_state.order_box = sort_items(st.session_state.order_box, key="box")
                with c2: st.session_state.order_total = sort_items(st.session_state.order_total, key="total")

            with tab_process:
                if st.button("🚀 ประมวลผลสร้างไฟล์ Excel"):
                    m_weight = full_df[full_df['Product'].str.contains('|'.join(meat_kw), na=False)].pivot_table(index=['TRIP', 'STORE NAME'], columns='Product', values='Qty', aggfunc='sum').fillna(0).reset_index()
                    m_box = full_df[~full_df['Product'].str.contains('|'.join(meat_kw), na=False)].pivot_table(index=['TRIP', 'STORE NAME'], columns='Product', values='Qty', aggfunc='sum').fillna(0).reset_index()
                    m_order = full_df.pivot_table(index=['TRIP', 'STORE NAME'], columns='Product', values='Qty', aggfunc='sum').fillna(0).reset_index()

                    output = io.BytesIO()
                    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                        wb = writer.book
                        
                        # --- ป้ายน้ำหนัก FORMATS (ขยายใหญ่มาก) ---
                        tag_bnn = wb.add_format({'bold': True, 'size': 40, 'border': 2, 'align': 'center', 'valign': 'vcenter'})
                        tag_trip_val = wb.add_format({'bold': True, 'size': 40, 'border': 2, 'align': 'center', 'valign': 'vcenter'})
                        tag_label = wb.add_format({'bold': True, 'size': 20, 'border': 1, 'align': 'center', 'valign': 'vcenter', 'shrink': True})
                        tag_store = wb.add_format({'bold': True, 'size': 28, 'border': 1, 'align': 'center', 'valign': 'vcenter'})
                        tag_prod = wb.add_format({'bold': True, 'size': 30, 'border': 1, 'valign': 'vcenter', 'indent': 1})
                        tag_unit = wb.add_format({'bold': True, 'size': 24, 'border': 1, 'align': 'center', 'valign': 'vcenter'})
                        border_fmt = wb.add_format({'border': 1})

                        # --- SHEET: ป้ายน้ำหนัก (LANDSCAPE + FULL A4) ---
                        ws_tag = wb.add_worksheet("ป้ายน้ำหนัก")
                        ws_tag.set_landscape() # แนวนอน
                        ws_tag.set_paper(9)      # A4
                        ws_tag.set_margins(0.2, 0.2, 0.2, 0.2)
                        
                        fixed_items = ["เนื้อสันคอ", "เนื้อออส", "หมูสันคอ", "หมูสามชั้น", "หมูสันนอก"]
                        curr_r = 0
                        
                        unique_stores = full_df[['TRIP', 'STORE NAME']].drop_duplicates().sort_values(['TRIP', 'STORE NAME'])
                        
                        for idx, row_s in unique_stores.iterrows():
                            t_val = row_s['TRIP']
                            s_val = row_s['STORE NAME']
                            
                            # Row 1: BNN | TRIP
                            ws_tag.merge_range(curr_r, 0, curr_r, 3, "BNN (สุกี้ตี๋น้อย)", tag_bnn)
                            ws_tag.merge_range(curr_r, 4, curr_r, 5, t_val, tag_trip_val)
                            ws_tag.set_row(curr_r, 85) # สูงมาก
                            
                            # Row 2: STORE NAME | ชื่อร้าน
                            ws_tag.write(curr_r + 1, 0, "STORE NAME", tag_label)
                            ws_tag.merge_range(curr_r + 1, 1, curr_r + 1, 5, s_val, tag_store)
                            ws_tag.set_row(curr_r + 1, 65)
                            
                            curr_r += 2
                            # Row 3-7: Fixed 5 Items
                            for item in fixed_items:
                                ws_tag.merge_range(curr_r, 0, curr_r, 1, item, tag_prod) # สินค้า
                                ws_tag.write(curr_r, 2, "", border_fmt)                 # ช่องว่างเขียน
                                ws_tag.write(curr_r, 3, "KG.", tag_unit)               # KG
                                ws_tag.write(curr_r, 4, "", border_fmt)                 # ช่องว่าง
                                ws_tag.write(curr_r, 5, "ตะกร้า", tag_unit)             # ตะกร้า
                                ws_tag.set_row(curr_r, 80) # ความสูงให้เต็มหน้า
                                curr_r += 1
                            
                            # บังคับขึ้นหน้าใหม่
                            ws_tag.set_h_pagebreaks([curr_r])
                            curr_r += 1

                        # ปรับความกว้าง Column ให้เต็มแนวนอน
                        ws_tag.set_column('A:B', 25)
                        ws_tag.set_column('C:F', 18)
                        ws_tag.fit_to_pages(1, 1) # บีบให้พอดี 1x1 หน้า

                        # --- ชีทอื่นๆ คงเดิม ---
                        h_fmt = wb.add_format({'bold': True, 'align': 'center', 'valign': 'vcenter', 'bg_color': theme_color, 'font_color': 'white', 'border': 1, 'text_wrap': True})
                        d_fmt = wb.add_format({'border': 1, 'align': 'center'})
                        sum_fmt = wb.add_format({'bold': True, 'bg_color': '#D9EAD3', 'border': 1, 'num_format': '#,##0'})

                        # (ส่วนเขียนชีท น้ำหนัก, จัดกล่อง, Order เหมือน v15 ครับ)
                        # ... [ย่อไว้เพื่อให้ Code ไม่ยาวเกินไป แต่ในไฟล์จริงผมใส่ให้ครบครับ]
                        ws1 = wb.add_worksheet("น้ำหนัก")
                        ws1.merge_range(0,0,1,0,"No.",h_fmt); ws1.merge_range(0,1,1,1,"TRIP",h_fmt); ws1.merge_range(0,2,1,2,"STORE NAME",h_fmt)
                        prods_w = [p for p in original_order if p in m_weight.columns and p not in ['TRIP', 'STORE NAME']]
                        c_ptr = 3
                        for p in prods_w:
                            ws1.write(0, c_ptr, "จำนวนสั่ง", h_fmt); ws1.write(1, c_ptr, p, h_fmt)
                            ws1.merge_range(0, c_ptr+1, 1, c_ptr+1, "จ่ายจริง", h_fmt); c_ptr += 2
                        for i, (idx, row) in enumerate(m_weight.iterrows()):
                            r = i+2; ws1.write(r,0,i+1,d_fmt); ws1.write(r,1,row['TRIP'],d_fmt); ws1.write(r,2,row['STORE NAME'],d_fmt)
                            d_ptr = 3
                            for p in prods_w: ws1.write(r, d_ptr, row[p], d_fmt); ws1.write(r, d_ptr+1, "", d_fmt); d_ptr += 2

                        ws2 = wb.add_worksheet("จัดกล่อง")
                        m_box = m_box[['TRIP', 'STORE NAME'] + [p for p in st.session_state.order_box if p in m_box.columns]].sort_values('TRIP')
                        ws2.write(0,0,"No.",h_fmt); ws2.write(0,1,"TRIP",h_fmt); ws2.write(0,2,"STORE NAME",h_fmt)
                        prods_b = [p for p in m_box.columns if p not in ['TRIP', 'STORE NAME']]
                        for idx, p in enumerate(prods_b): ws2.write(0, idx+3, p, h_fmt)
                        s_col = len(prods_b)+3; ws2.write(0, s_col, "รวมจำนวน", h_fmt)
                        for i, (idx, row) in enumerate(m_box.iterrows()):
                            r = i+1; ws2.write(r,0,i+1,d_fmt); ws2.write(r,1,row['TRIP'],d_fmt); ws2.write(r,2,row['STORE NAME'],d_fmt)
                            for c_idx, p in enumerate(prods_b): ws2.write(r, c_idx+3, row[p], d_fmt)
                            ws2.write(r, s_col, sum(row[p] for p in prods_b), sum_fmt)

                        ws3 = wb.add_worksheet("Order")
                        m_order = m_order[['TRIP', 'STORE NAME'] + [p for p in st.session_state.order_total if p in m_order.columns]].sort_values('TRIP')
                        ws3.write(0, 0, "No.", h_fmt); ws3.write(0, 1, "TRIP", h_fmt); ws3.write(0, 2, "STORE NAME", h_fmt)
                        for idx, p in enumerate([p for p in m_order.columns if p not in ['TRIP', 'STORE NAME']]): ws3.write(0, idx+3, p, h_fmt)
                        for i, (idx, row) in enumerate(m_order.iterrows()):
                            r = i+1; ws3.write(r,0,i+1,d_fmt); ws3.write(r,1,row['TRIP'],d_fmt); ws3.write(r,2,row['STORE NAME'],d_fmt)
                            for c_idx, p in enumerate([p for p in m_order.columns if p not in ['TRIP', 'STORE NAME']]): ws3.write(r, c_idx+3, row[p], d_fmt)

                        for ws in [ws1, ws2, ws3]: ws.set_column('C:C', 35); ws.set_column('D:ZZ', 12)

                    st.balloons()
                    st.download_button("📥 ดาวน์โหลดไฟล์ Final BNN แนวนอน", output.getvalue(), "BNN_Landscape_V16.xlsx")

    except Exception as e:
        st.error(f"❌ พบข้อผิดพลาด: {e}")