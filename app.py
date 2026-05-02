import streamlit as st
import pandas as pd
import io
from streamlit_sortables import sort_items

# --- UI CONFIGURATION ---
st.set_page_config(page_title="Project น้องเดียร์ v27.0 (ป้ายกล่อง)", layout="wide")

def local_css(main_color, font_family):
    st.markdown(f"""
        <style>
        @import url('https://fonts.googleapis.com/css2?family={font_family.replace(" ", "+")}:wght@300;400;600&display=swap');
        html, body, [class*="css"], .main {{ background-color: #0F1117; color: #E0E0E0 !important; font-family: '{font_family}', sans-serif; }}
        h1 {{ color: {main_color} !important; text-align: center; }}
        div.stButton > button {{
            background: linear-gradient(135deg, {main_color} 0%, #FF85A1 100%);
            color: white !important; border-radius: 12px; font-weight: bold; height: 60px; width: 100%;
        }}
        </style>
    """, unsafe_allow_html=True)

theme_color = st.sidebar.color_picker("ธีมสีหลัก", "#FF4B8B")
font_choice = st.sidebar.selectbox("เลือกฟอนต์", ["Kanit", "Mitr", "Sarabun"])
local_css(theme_color, font_choice)

st.title(f"💖 Project น้องเดียร์ v27.0")

if 'order_box' not in st.session_state: st.session_state.order_box = []
if 'order_total' not in st.session_state: st.session_state.order_total = []

tab_upload, tab_setting, tab_process = st.tabs(["📥 1. อัปโหลดไฟล์", "↕️ 2. ลากวางลำดับสินค้า", "🚀 3. ประมวลผล"])

if file := st.file_uploader("อัปโหลดไฟล์ Excel", type=["xlsx"]):
    try:
        route_df = pd.read_excel(file, sheet_name='Route', header=None)
        route_lookup = {str(r[0]).strip(): str(r[2]).strip() for _, r in route_df.iterrows() if pd.notna(r[0])}
        xls = pd.ExcelFile(file); main_sheet = xls.sheet_names[0]
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
                            all_rows.append({'TRIP': route_lookup.get(current_store_code, "ไม่พบรหัส"), 'STORE NAME': col_name, 'Product': product, 'Qty': qty})
                    except: continue

            full_df = pd.DataFrame(all_rows); meat_kw = ['เนื้อ', 'หมู', 'Meat', 'Pork']
            if not st.session_state.order_box: st.session_state.order_box = [p for p in original_order if not any(kw in p for kw in meat_kw)]
            if not st.session_state.order_total: st.session_state.order_total = original_order

            with tab_setting:
                c1, c2 = st.columns(2)
                with c1: st.session_state.order_box = sort_items(st.session_state.order_box, key="box")
                with c2: st.session_state.order_total = sort_items(st.session_state.order_total, key="total")

            with tab_process:
                if st.button("🚀 ประมวลผลสร้างไฟล์"):
                    m_weight = full_df[full_df['Product'].str.contains('|'.join(meat_kw), na=False)].pivot_table(index=['TRIP', 'STORE NAME'], columns='Product', values='Qty', aggfunc='sum').fillna(0).reset_index()
                    m_box = full_df[~full_df['Product'].str.contains('|'.join(meat_kw), na=False)].pivot_table(index=['TRIP', 'STORE NAME'], columns='Product', values='Qty', aggfunc='sum').fillna(0).reset_index()
                    m_order = full_df.pivot_table(index=['TRIP', 'STORE NAME'], columns='Product', values='Qty', aggfunc='sum').fillna(0).reset_index()
                    
                    prods_box_list = [p for p in st.session_state.order_box if p in m_box.columns]
                    m_box = m_box[['TRIP', 'STORE NAME'] + prods_box_list].sort_values(['TRIP', 'STORE NAME'])
                    m_box['รวมจำนวน'] = m_box[prods_box_list].sum(axis=1) # คำนวณยอดรวมกล่องสำหรับทำป้าย

                    output = io.BytesIO()
                    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                        wb = writer.book
                        
                        # --- 1. ป้ายน้ำหนัก (Logic v26 ที่เป๊ะแล้ว) ---
                        ws_tag_w = wb.add_worksheet("ป้ายน้ำหนัก")
                        ws_tag_w.set_landscape(); ws_tag_w.set_margins(0.2, 0.2, 0.2, 0.2); ws_tag_w.fit_to_pages(1, 0)
                        f_bnn = wb.add_format({'bold':True, 'size':36, 'border':2, 'align':'center', 'valign':'vcenter', 'bg_color':'#EEEEEE'})
                        f_trip_v = wb.add_format({'bold':True, 'size':40, 'border':2, 'align':'center', 'valign':'vcenter'})
                        f_store_v = wb.add_format({'bold':True, 'size':28, 'border':1, 'align':'center', 'valign':'vcenter', 'shrink':True})
                        f_prod_v = wb.add_format({'bold':True, 'size':28, 'border':1, 'valign':'vcenter', 'indent':1})
                        f_unit_v = wb.add_format({'bold':True, 'size':22, 'border':1, 'align':'center', 'valign':'vcenter'})
                        
                        ws_tag_w.set_column('A:A', 38); ws_tag_w.set_column('B:E', 18)
                        fixed_items = ["เนื้อสันคอ", "เนื้อออส", "หมูสันคอ", "หมูสามชั้น", "หมูสันนอก"]
                        row_idx = 0; breaks_w = []
                        for _, row_s in m_weight[['TRIP', 'STORE NAME']].iterrows():
                            ws_tag_w.merge_range(row_idx, 0, row_idx, 2, "BNN (สุกี้ตี๋น้อย)", f_bnn)
                            ws_tag_w.merge_range(row_idx, 3, row_idx, 4, row_s['TRIP'], f_trip_v)
                            ws_tag_w.set_row(row_idx, 80)
                            ws_tag_w.write(row_idx + 1, 0, "STORE:", f_unit_v)
                            ws_tag_w.merge_range(row_idx + 1, 1, row_idx + 1, 4, row_s['STORE NAME'], f_store_v)
                            ws_tag_w.set_row(row_idx + 1, 70)
                            for i, item in enumerate(fixed_items):
                                r = row_idx + 2 + i
                                ws_tag_w.write(r, 0, item, f_prod_v); ws_tag_w.write(r, 1, "", f_unit_v); ws_tag_w.write(r, 2, "KG.", f_unit_v)
                                ws_tag_w.write(r, 3, "", f_unit_v); ws_tag_w.write(r, 4, "ตะกร้า", f_unit_v); ws_tag_w.set_row(r, 75)
                            row_idx += 8; breaks_w.append(row_idx)
                        ws_tag_w.set_h_pagebreaks(breaks_w)

                        # --- 2. ป้ายกล่อง (ใหม่!) ---
                        ws_tag_b = wb.add_worksheet("ป้ายกล่อง")
                        ws_tag_b.set_landscape(); ws_tag_b.set_margins(0.2, 0.2, 0.2, 0.2); ws_tag_b.fit_to_pages(1, 0)
                        
                        f_bnn_big = wb.add_format({'bold':True, 'size':60, 'border':2, 'align':'center', 'valign':'vcenter', 'bg_color':'#EEEEEE'})
                        f_store_big = wb.add_format({'bold':True, 'size':35, 'border':1, 'align':'center', 'valign':'vcenter', 'text_wrap':True})
                        f_qty_big = wb.add_format({'bold':True, 'size':80, 'border':1, 'align':'center', 'valign':'vcenter'})
                        f_label_big = wb.add_format({'bold':True, 'size':40, 'border':1, 'align':'center', 'valign':'vcenter'})
                        f_trip_big = wb.add_format({'bold':True, 'size':70, 'border':1, 'align':'center', 'valign':'vcenter'})

                        ws_tag_b.set_column('A:A', 50); ws_tag_b.set_column('B:B', 60)
                        
                        b_row = 0; breaks_b = []
                        for _, row_b in m_box.iterrows():
                            # Row 1: หัวข้อ BNN
                            ws_tag_b.merge_range(b_row, 0, b_row, 1, "BNN (สุกี้ตี๋น้อย)", f_bnn_big)
                            ws_tag_b.set_row(b_row, 120)
                            # Row 2: ชื่อสาขา
                            ws_tag_b.write(b_row+1, 0, "STORE NAME", f_label_big)
                            ws_tag_b.write(b_row+1, 1, row_b['STORE NAME'], f_store_big)
                            ws_tag_b.set_row(b_row+1, 100)
                            # Row 3: จำนวนกล่อง
                            ws_tag_b.write(b_row+2, 0, "จำนวนกล่อง", f_label_big)
                            ws_tag_b.write(b_row+2, 1, row_b['รวมจำนวน'], f_qty_big)
                            ws_tag_b.set_row(b_row+2, 130)
                            # Row 4: TRIP NO.
                            ws_tag_b.write(b_row+3, 0, "TRIP NO.", f_label_big)
                            ws_tag_b.write(b_row+3, 1, row_b['TRIP'], f_trip_big)
                            ws_tag_b.set_row(b_row+3, 120)
                            
                            b_row += 4; breaks_b.append(b_row)
                        ws_tag_b.set_h_pagebreaks(breaks_b)

                        # --- ระบบเดิม (น้ำหนัก, จัดกล่อง, Order) ---
                        h_f = wb.add_format({'bold':True, 'align':'center', 'valign':'vcenter', 'bg_color':theme_color, 'font_color':'white', 'border':1, 'text_wrap':True})
                        d_f = wb.add_format({'border':1, 'align':'center'})
                        s_f = wb.add_format({'bold':True, 'bg_color':'#D9EAD3', 'border':1, 'num_format':'#,##0'})

                        ws_w = wb.add_worksheet("น้ำหนัก")
                        # (Logic เหมือนเดิมเป๊ะ...)
                        ws1_cols = [p for p in original_order if p in m_weight.columns and p not in ['TRIP', 'STORE NAME']]
                        ws_w.merge_range(0,0,1,0,"No.",h_f); ws_w.merge_range(0,1,1,1,"TRIP",h_f); ws_w.merge_range(0,2,1,2,"STORE NAME",h_f)
                        c_idx = 3
                        for p in ws1_cols:
                            ws_w.write(0, c_idx, "จำนวนสั่ง", h_f); ws_w.write(1, c_idx, p, h_f); ws_w.merge_range(0, c_idx+1, 1, c_idx+1, "จ่ายจริง", h_f); c_idx += 2
                        for i, row in m_weight.reset_index(drop=True).iterrows():
                            r = i+2; ws_w.write(r,0,i+1,d_f); ws_w.write(r,1,row['TRIP'],d_f); ws_w.write(r,2,row['STORE NAME'],d_f)
                            d_idx = 3
                            for p in ws1_cols: ws_w.write(r, d_idx, row[p], d_f); ws_w.write(r, d_idx+1, "", d_f); d_idx += 2

                        ws_b = wb.add_worksheet("จัดกล่อง")
                        for idx, col in enumerate(m_box.columns): ws_b.write(0, idx, col, h_f)
                        for i, row in m_box.reset_index(drop=True).iterrows():
                            for idx, val in enumerate(row): ws_b.write(i+1, idx, val, d_f if idx < len(row)-1 else s_f)

                        ws_o = wb.add_worksheet("Order")
                        for idx, col in enumerate(m_order.columns): ws_o.write(0, idx, col, h_f)
                        for i, row in m_order.reset_index(drop=True).iterrows():
                            for idx, val in enumerate(row): ws_o.write(i+1, idx, val, d_f)

                        for ws in [ws_w, ws_b, ws_o]: ws.set_column('B:C', 25); ws.set_column('D:ZZ', 12)

                    st.balloons()
                    st.download_button("📥 ดาวน์โหลด v27 (เพิ่มป้ายกล่อง)", output.getvalue(), "BNN_V27_Full.xlsx")

    except Exception as e:
        st.error(f"❌ พบข้อผิดพลาด: {e}")