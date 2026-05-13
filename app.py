import streamlit as st
import pandas as pd
import io
from datetime import datetime
from streamlit_sortables import sort_items

# --- UI CONFIGURATION ---
st.set_page_config(page_title="Mobile Logistics Co., Ltd.", layout="wide")

def local_css(main_color, font_family):
    st.markdown(f"""
        <style>
        @import url('https://fonts.googleapis.com/css2?family={font_family.replace(" ", "+")}:wght@300;400;600&display=swap');
        html, body, [class*="css"], .main {{ background-color: #0F1117; color: #E0E0E0 !important; font-family: '{font_family}', sans-serif; }}
        h1 {{ 
            background: linear-gradient(90deg, {main_color}, #FFFFFF);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            text-align: center; font-size: 3rem; font-weight: 800; padding: 1rem 0;
        }}
        div.stButton > button {{
            background: linear-gradient(135deg, {main_color} 0%, #FF85A1 100%);
            color: white !important; border-radius: 12px; font-weight: bold; height: 60px; width: 100%;
        }}
        </style>
    """, unsafe_allow_html=True)

theme_color = st.sidebar.color_picker("ธีมสีเว็บ", "#FF4B8B")
font_choice = st.sidebar.selectbox("เลือกฟอนต์", ["Kanit", "Mitr", "Sarabun"])
local_css(theme_color, font_choice)

st.markdown("<h1>Mobile Logistics Co., Ltd.</h1>", unsafe_allow_html=True)

# --- SESSION STATE ---
if 'order_box' not in st.session_state: st.session_state.order_box = []
if 'order_total' not in st.session_state: st.session_state.order_total = []

tab_upload, tab_setting, tab_process = st.tabs(["📥 อัปโหลดไฟล์", "↕️ ลำดับสินค้า", "🚀 ประมวลผล"])

if file := st.file_uploader("อัปโหลด Excel", type=["xlsx"]):
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
            
            # 🔥 เรียงลำดับสินค้าตามรูปภาพ
            fixed_top = ["ปูอัด", "ปูอัดชีส", "หอยเชลล์โฮตาเตะญี่ปุ่น(NW100%)", "ปลาดอลลี่ NW 70% (200-400)", "ชีสมอสซาเรลล่า", "คิมมาริ", "น้ำจิ้มพอนสึ ยูสุ (ถุง 2 ก.ก.)", "น้ำจิ้มสุกี้"]
            
            if not st.session_state.order_box: 
                box_items = [p for p in original_order if not any(kw in p for kw in meat_kw)]
                sorted_box = [p for p in fixed_top if p in box_items] + [p for p in box_items if p not in fixed_top]
                st.session_state.order_box = sorted_box
            if not st.session_state.order_total: st.session_state.order_total = original_order

            with tab_setting:
                c1, c2 = st.columns(2)
                with c1: 
                    st.markdown("📦 **ลำดับป้ายกล่อง (เรียงตามรูป)**")
                    st.session_state.order_box = sort_items(st.session_state.order_box, key="box")
                with c2: 
                    st.markdown("📋 **ลำดับรายงานสรุป**")
                    st.session_state.order_total = sort_items(st.session_state.order_total, key="total")

            with tab_process:
                if st.button("🚀 ประมวลผลสร้างไฟล์"):
                    m_weight = full_df[full_df['Product'].str.contains('|'.join(meat_kw), na=False)].pivot_table(index=['TRIP', 'STORE NAME'], columns='Product', values='Qty', aggfunc='sum').fillna(0).reset_index()
                    m_box = full_df[~full_df['Product'].str.contains('|'.join(meat_kw), na=False)].pivot_table(index=['TRIP', 'STORE NAME'], columns='Product', values='Qty', aggfunc='sum').fillna(0).reset_index()
                    m_order = full_df.pivot_table(index=['TRIP', 'STORE NAME'], columns='Product', values='Qty', aggfunc='sum').fillna(0).reset_index()
                    
                    prods_box_list = [p for p in st.session_state.order_box if p in m_box.columns]
                    m_box = m_box[['TRIP', 'STORE NAME'] + prods_box_list].sort_values(['TRIP', 'STORE NAME'])
                    m_box['รวมจำนวน'] = m_box[prods_box_list].sum(axis=1)

                    output = io.BytesIO()
                    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                        wb = writer.book
                        header_bg = '#F2F2F2'
                        label_title = "BNN (สุกี้ตี๋น้อย)"
                        h_f = wb.add_format({'bold':True, 'align':'center', 'valign':'vcenter', 'bg_color':header_bg, 'border':1, 'text_wrap':True})
                        d_f = wb.add_format({'border':1, 'align':'center'})
                        s_f = wb.add_format({'bold':True, 'bg_color':'#E9E9E9', 'border':1, 'num_format':'#,##0'})

                        # --- 1. ป้ายน้ำหนัก --- (เหมือนเดิม)
                        ws1 = wb.add_worksheet("ป้ายน้ำหนัก")
                        ws1.set_landscape(); ws1.set_margins(0.2, 0.2, 0.2, 0.2)
                        f_bnn = wb.add_format({'bold':True, 'size':36, 'border':2, 'align':'center', 'valign':'vcenter', 'bg_color':header_bg})
                        f_trip_v = wb.add_format({'bold':True, 'size':40, 'border':2, 'align':'center', 'valign':'vcenter'})
                        f_unit_v = wb.add_format({'bold':True, 'size':22, 'border':1, 'align':'center', 'valign':'vcenter'})
                        f_prod_v = wb.add_format({'bold':True, 'size':28, 'border':1, 'valign':'vcenter', 'indent':1})
                        ws1.set_column('A:A', 38); ws1.set_column('B:E', 18)
                        fixed_meat_list = ["เนื้อสันคอ", "เนื้อออส", "หมูสันคอ", "หมูสามชั้น", "หมูสันนอก", "หมูคูโรบุตะ"]
                        row_idx = 0; breaks_w = []
                        for _, row_s in m_weight[['TRIP', 'STORE NAME']].iterrows():
                            ws1.merge_range(row_idx, 0, row_idx, 2, label_title, f_bnn)
                            ws1.merge_range(row_idx, 3, row_idx, 4, row_s['TRIP'], f_trip_v)
                            ws1.set_row(row_idx, 80)
                            ws1.write(row_idx + 1, 0, "STORE:", f_unit_v)
                            ws1.merge_range(row_idx + 1, 1, row_idx + 1, 4, row_s['STORE NAME'], wb.add_format({'bold':True, 'size':28, 'border':1, 'align':'center', 'valign':'vcenter'}))
                            ws1.set_row(row_idx + 1, 70)
                            for i, item in enumerate(fixed_meat_list):
                                r = row_idx + 2 + i
                                ws1.write(r, 0, item, f_prod_v); ws1.write(r, 1, "", f_unit_v); ws1.write(r, 2, "KG.", f_unit_v)
                                ws1.write(r, 3, "", f_unit_v); ws1.write(r, 4, "ตะกร้า", f_unit_v); ws1.set_row(r, 75)
                            row_idx += 9; breaks_w.append(row_idx)
                        ws1.set_h_pagebreaks(breaks_w)

                        # --- 2. ป้ายกล่อง --- (เหมือนเดิม)
                        ws2 = wb.add_worksheet("ป้ายกล่อง")
                        ws2.set_landscape(); ws2.set_margins(0.2, 0.2, 0.2, 0.2)
                        f_label_big = wb.add_format({'bold':True, 'size':40, 'border':1, 'align':'center', 'valign':'vcenter'})
                        f_qty_big = wb.add_format({'bold':True, 'size':80, 'border':1, 'align':'center', 'valign':'vcenter'})
                        ws2.set_column('A:A', 50); ws2.set_column('B:B', 60)
                        b_row = 0; breaks_b = []
                        for _, row_b in m_box.iterrows():
                            ws2.merge_range(b_row, 0, b_row, 1, label_title, wb.add_format({'bold':True, 'size':60, 'border':2, 'align':'center', 'valign':'vcenter', 'bg_color':header_bg}))
                            ws2.write(b_row+1, 0, "STORE NAME", f_label_big); ws2.write(b_row+1, 1, row_b['STORE NAME'], wb.add_format({'bold':True, 'size':35, 'border':1, 'align':'center', 'valign':'vcenter', 'text_wrap':True}))
                            ws2.write(b_row+2, 0, "จำนวนกล่อง", f_label_big); ws2.write(b_row+2, 1, row_b['รวมจำนวน'], f_qty_big)
                            ws2.write(b_row+3, 0, "TRIP NO.", f_label_big); ws2.write(b_row+3, 1, row_b['TRIP'], wb.add_format({'bold':True, 'size':70, 'border':1, 'align':'center', 'valign':'vcenter'}))
                            ws2.set_row(b_row, 120); ws2.set_row(b_row+1, 100); ws2.set_row(b_row+2, 130); ws2.set_row(b_row+3, 120)
                            b_row += 4; breaks_b.append(b_row)
                        ws2.set_h_pagebreaks(breaks_b)

                        # --- 3. น้ำหนัก (Fix ข้อมูล + Mapping + ยอดรวม TOTAL) ---
                        ws3 = wb.add_worksheet("น้ำหนัก")
                        ws3.merge_range(0,0,1,0,"No.",h_f); ws3.merge_range(0,1,1,1,"TRIP",h_f); ws3.merge_range(0,2,1,2,"STORE NAME",h_f)
                        meat_mapping = {"หมูสามชั้นคูโรบูตะ": "หมูคูโรบุตะ"}
                        c_idx = 3
                        for p in fixed_meat_list:
                            ws3.write(0, c_idx, "จำนวนสั่ง", h_f); ws3.write(1, c_idx, p, h_f); ws3.merge_range(0, c_idx+1, 1, c_idx+1, "จ่ายจริง", h_f); c_idx += 2
                        ws3.merge_range(0, c_idx, 1, c_idx, "ตะกร้า", h_f); ws3.merge_range(0, c_idx+1, 1, c_idx+1, "กล่อง", h_f)
                        
                        m_weight_reset = m_weight.reset_index(drop=True)
                        for i, r_val in m_weight_reset.iterrows():
                            row_n = i+2; ws3.write(row_n,0,i+1,d_f); ws3.write(row_n,1,r_val['TRIP'],d_f); ws3.write(row_n,2,r_val['STORE NAME'],d_f)
                            d_idx = 3
                            for p in fixed_meat_list:
                                val = r_val.get(p, 0)
                                if val == 0:
                                    raw_name = next((k for k, v in meat_mapping.items() if v == p), None)
                                    if raw_name: val = r_val.get(raw_name, 0)
                                ws3.write(row_n, d_idx, val, d_f); ws3.write(row_n, d_idx+1, "", d_f); d_idx += 2
                            ws3.write(row_n, d_idx, "", d_f); ws3.write(row_n, d_idx+1, "", d_f)

                        # 🔥 ส่วนยอดรวมท้ายตาราง (TOTAL) ของชีทน้ำหนัก
                        total_row_idx = len(m_weight_reset) + 2
                        ws3.write(total_row_idx, 2, "TOTAL", s_f)
                        d_idx = 3
                        for p in fixed_meat_list:
                            # รวมยอดสั่ง (Column จ่ายจริง เว้นว่างไว้)
                            val = m_weight[p].sum() if p in m_weight.columns else 0
                            if val == 0:
                                raw_name = next((k for k, v in meat_mapping.items() if v == p), None)
                                if raw_name: val = m_weight[raw_name].sum()
                            ws3.write(total_row_idx, d_idx, val, s_f)
                            ws3.write(total_row_idx, d_idx+1, "", s_f)
                            d_idx += 2
                        # ช่อง TOTAL ของ ตะกร้า และ กล่อง
                        ws3.write(total_row_idx, d_idx, "", s_f); ws3.write(total_row_idx, d_idx+1, "", s_f)
                        ws3.set_column('B:C', 25); ws3.set_column('D:ZZ', 12)

                        # --- 4. จัดกล่อง --- (เหมือนเดิม)
                        ws4 = wb.add_worksheet("จัดกล่อง")
                        cols_box = list(m_box.columns)
                        ws4.write(0, 0, "No.", h_f)
                        for idx, col in enumerate(cols_box): ws4.write(0, idx + 1, col, h_f)
                        for i, r_val in m_box.reset_index(drop=True).iterrows():
                            ws4.write(i + 1, 0, i + 1, d_f)
                            for idx, val in enumerate(r_val):
                                ws4.write(i + 1, idx + 1, val, s_f if cols_box[idx] == 'รวมจำนวน' else d_f)
                        l_row = len(m_box) + 1
                        ws4.write(l_row, 2, "TOTAL", s_f)
                        for idx, col in enumerate(cols_box):
                            if col not in ['TRIP', 'STORE NAME']: ws4.write(l_row, idx + 1, m_box[col].sum(), s_f)
                        ws4.set_column('A:A', 5); ws4.set_column('B:C', 25); ws4.set_column('D:ZZ', 12)

                        # --- 5. Order --- (เหมือนเดิม)
                        ws5 = wb.add_worksheet("Order")
                        ws5.write(0, 0, "No.", h_f)
                        for idx, col in enumerate(m_order.columns): ws5.write(0, idx + 1, col, h_f)
                        for i, r_val in m_order.reset_index(drop=True).iterrows():
                            ws5.write(i+1, 0, i+1, d_f)
                            for idx, val in enumerate(r_val): ws5.write(i+1, idx+1, val, d_f)
                        ws5.set_column('B:C', 25); ws5.set_column('D:ZZ', 12)

                    st.download_button(label="📥 ดาวน์โหลดไฟล์", data=output.getvalue(), file_name=f"Report_{datetime.now().strftime('%Y-%m-%d')}.xlsx")
    except Exception as e:
        st.error(f"⚠️ Error: {e}")