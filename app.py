import streamlit as st
import pandas as pd
import io
from streamlit_sortables import sort_items

# --- UI CONFIGURATION ---
st.set_page_config(page_title="Project น้องเดียร์ v26.0 (Perfect Print)", layout="wide")

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

st.title(f"💖 Project น้องเดียร์ v26.0")

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
                    m_box = m_box[['TRIP', 'STORE NAME'] + [p for p in st.session_state.order_box if p in m_box.columns]].sort_values(['TRIP', 'STORE NAME'])
                    m_order = m_order[['TRIP', 'STORE NAME'] + [p for p in st.session_state.order_total if p in m_order.columns]].sort_values(['TRIP', 'STORE NAME'])

                    output = io.BytesIO()
                    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                        wb = writer.book
                        
                        # --- ปรับป้ายน้ำหนัก (ลดขนาดลงเพื่อให้จบในหน้าเดียว) ---
                        ws_tag = wb.add_worksheet("ป้ายน้ำหนัก")
                        ws_tag.set_landscape()
                        ws_tag.set_margins(0.2, 0.2, 0.2, 0.2)
                        ws_tag.fit_to_pages(1, 0) # 1 หน้ากว้าง

                        # Formats (ลดขนาดฟอนต์ลงเล็กน้อย)
                        f_bnn = wb.add_format({'bold':True, 'size':36, 'border':2, 'align':'center', 'valign':'vcenter', 'bg_color':'#EEEEEE'})
                        f_trip = wb.add_format({'bold':True, 'size':40, 'border':2, 'align':'center', 'valign':'vcenter'})
                        f_store = wb.add_format({'bold':True, 'size':28, 'border':1, 'align':'center', 'valign':'vcenter', 'shrink':True})
                        f_prod = wb.add_format({'bold':True, 'size':28, 'border':1, 'valign':'vcenter', 'indent':1})
                        f_unit = wb.add_format({'bold':True, 'size':22, 'border':1, 'align':'center', 'valign':'vcenter'})
                        f_border = wb.add_format({'border':1})

                        ws_tag.set_column('A:A', 38); ws_tag.set_column('B:B', 20); ws_tag.set_column('C:C', 14); ws_tag.set_column('D:D', 20); ws_tag.set_column('E:E', 18)

                        fixed_items = ["เนื้อสันคอ", "เนื้อออส", "หมูสันคอ", "หมูสามชั้น", "หมูสันนอก"]
                        row_idx = 0
                        breaks = []

                        for _, row_s in m_weight[['TRIP', 'STORE NAME']].iterrows():
                            ws_tag.merge_range(row_idx, 0, row_idx, 2, "BNN (สุกี้ตี๋น้อย)", f_bnn)
                            ws_tag.merge_range(row_idx, 3, row_idx, 4, row_s['TRIP'], f_trip)
                            ws_tag.set_row(row_idx, 80) # ลดความสูงหัวข้อ
                            
                            ws_tag.write(row_idx + 1, 0, "STORE:", f_unit)
                            ws_tag.merge_range(row_idx + 1, 1, row_idx + 1, 4, row_s['STORE NAME'], f_store)
                            ws_tag.set_row(row_idx + 1, 70) # ลดความสูงชื่อร้าน
                            
                            item_start = row_idx + 2
                            for i, item in enumerate(fixed_items):
                                current_item_row = item_start + i
                                ws_tag.write(current_item_row, 0, item, f_prod)
                                ws_tag.write(current_item_row, 1, "", f_border)
                                ws_tag.write(current_item_row, 2, "KG.", f_unit)
                                ws_tag.write(current_item_row, 3, "", f_border)
                                ws_tag.write(current_item_row, 4, "ตะกร้า", f_unit)
                                ws_tag.set_row(current_item_row, 75) # ลดความสูงแถวสินค้า

                            row_idx += 8
                            breaks.append(row_idx)

                        ws_tag.set_h_pagebreaks(breaks)

                        # --- ระบบเดิม (น้ำหนัก, จัดกล่อง, Order) ห้ามแก้ ---
                        h_f = wb.add_format({'bold':True, 'align':'center', 'valign':'vcenter', 'bg_color':theme_color, 'font_color':'white', 'border':1, 'text_wrap':True})
                        d_f = wb.add_format({'border':1, 'align':'center'})
                        s_f = wb.add_format({'bold':True, 'bg_color':'#D9EAD3', 'border':1, 'num_format':'#,##0'})

                        # ชีท น้ำหนัก
                        ws1 = wb.add_worksheet("น้ำหนัก")
                        ws1.merge_range(0,0,1,0,"No.",h_f); ws1.merge_range(0,1,1,1,"TRIP",h_f); ws1.merge_range(0,2,1,2,"STORE NAME",h_f)
                        prods_w = [p for p in original_order if p in m_weight.columns and p not in ['TRIP', 'STORE NAME']]
                        c_p = 3
                        for p in prods_w:
                            ws1.write(0, c_p, "จำนวนสั่ง", h_f); ws1.write(1, c_p, p, h_f); ws1.merge_range(0, c_p+1, 1, c_p+1, "จ่ายจริง", h_f); c_p += 2
                        for i, row in m_weight.reset_index(drop=True).iterrows():
                            r = i+2; ws1.write(r,0,i+1,d_f); ws1.write(r,1,row['TRIP'],d_f); ws1.write(r,2,row['STORE NAME'],d_f)
                            d_p = 3
                            for p in prods_w: ws1.write(r, d_p, row[p], d_f); ws1.write(r, d_p+1, "", d_f); d_p += 2

                        # ชีท จัดกล่อง
                        ws2 = wb.add_worksheet("จัดกล่อง")
                        ws2.write(0,0,"No.",h_f); ws2.write(0,1,"TRIP",h_f); ws2.write(0,2,"STORE NAME",h_f)
                        prods_b = [p for p in m_box.columns if p not in ['TRIP', 'STORE NAME']]
                        for idx, p in enumerate(prods_b): ws2.write(0, idx+3, p, h_f)
                        s_c = len(prods_b)+3; ws2.write(0, s_c, "รวมจำนวน", h_f)
                        for i, row in m_box.reset_index(drop=True).iterrows():
                            r = i+1; ws2.write(r,0,i+1,d_f); ws2.write(r,1,row['TRIP'],d_f); ws2.write(r,2,row['STORE NAME'],d_f)
                            for idx, p in enumerate(prods_b): ws2.write(r, idx+3, row[p], d_f)
                            ws2.write(r, s_c, sum(row[p] for p in prods_b), s_f)

                        # ชีท Order
                        ws3 = wb.add_worksheet("Order")
                        ws3.write(0, 0, "No.", h_f); ws3.write(0, 1, "TRIP", h_f); ws3.write(0, 2, "STORE NAME", h_f)
                        prods_o = [p for p in m_order.columns if p not in ['TRIP', 'STORE NAME']]
                        for idx, p in enumerate(prods_o): ws3.write(0, idx+3, p, h_f)
                        for i, row in m_order.reset_index(drop=True).iterrows():
                            r = i+1; ws3.write(r,0,i+1,d_f); ws3.write(r,1,row['TRIP'],d_f); ws3.write(r,2,row['STORE NAME'],d_f)
                            for idx, p in enumerate(prods_o): ws3.write(r, idx+3, row[p], d_f)

                        for ws in [ws1, ws2, ws3]: ws.set_column('C:C', 35); ws.set_column('D:ZZ', 12)

                    st.balloons()
                    st.download_button("📥 ดาวน์โหลด v26 (จบในหน้าเดียวแน่นอน)", output.getvalue(), "BNN_Perfect_V26.xlsx")

    except Exception as e:
        st.error(f"❌ พบข้อผิดพลาด: {e}")