import streamlit as st
import pandas as pd
import io
from datetime import datetime
from streamlit_sortables import sort_items

# --- 💖 THE ULTIMATE SASSY UI CONFIGURATION 💖 ---
st.set_page_config(page_title="Mobile Logistics | ตัวแม่จะแคร์เพื่อ", layout="wide")

def sassy_css():
    st.markdown("""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Kanit:wght@300;400;600&family=Mitr:wght@300;500&display=swap');
        .main { background: linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%); color: #ffffff !important; font-family: 'Kanit', sans-serif; }
        h1 { background: linear-gradient(90deg, #FF007A, #FF85A1, #FFFFFF, #FF85A1, #FF007A); background-size: 200% auto; -webkit-background-clip: text; -webkit-text-fill-color: transparent; animation: shine 3s linear infinite; text-align: center; font-size: 4rem !important; font-weight: 800 !important; padding: 2rem 0; text-transform: uppercase; letter-spacing: 5px; }
        @keyframes shine { to { background-position: 200% center; } }
        div.stButton > button { background: linear-gradient(135deg, #FF007A 0%, #9000FF 100%) !important; color: white !important; border: none !important; border-radius: 50px !important; font-weight: bold !important; font-size: 1.2rem !important; height: 70px !important; width: 100% !important; transition: 0.4s all ease-in-out !important; box-shadow: 0 10px 20px rgba(255, 0, 122, 0.4) !important; text-transform: uppercase; }
        .stTabs [data-baseweb="tab-list"] { gap: 10px; background-color: rgba(255, 255, 255, 0.05); padding: 10px; border-radius: 20px; }
        .stTabs [data-baseweb="tab"] { height: 50px; color: #FF85A1 !important; font-weight: 600; }
        .stTabs [aria-selected="true"] { background: linear-gradient(90deg, #FF007A, #9000FF) !important; color: white !important; }
        </style>
    """, unsafe_allow_html=True)

sassy_css()
st.markdown("<h1>Queen Logistics Center 💅</h1>", unsafe_allow_html=True)

if 'order_box' not in st.session_state: st.session_state.order_box = []
if 'order_total' not in st.session_state: st.session_state.order_total = []

tab_upload, tab_setting, tab_process = st.tabs(["💅 อัปโหลดไฟล์", "↕️ ลำดับสินค้า", "🚀 ประมวลผล"])

with tab_upload:
    file = st.file_uploader("โยนไฟล์ Excel มาให้ไวเลยค่ะคุณเดียร์", type=["xlsx"])

if file:
    try:
        # อ่าน Route และทำ Lookup (ดึงทั้งรหัสสาขาและชื่อสาย)
        route_df = pd.read_excel(file, sheet_name='Route', header=None)
        route_lookup = {str(r[0]).strip(): str(r[2]).strip() for _, r in route_df.iterrows() if pd.notna(r[0])}
        # เพิ่ม Lookup สำหรับตัวย่อสาขา
        short_name_lookup = {str(r[0]).strip(): str(r[0]).strip() for _, r in route_df.iterrows() if pd.notna(r[0])}
        
        xls = pd.ExcelFile(file); main_sheet = xls.sheet_names[0]
        raw_df = pd.read_excel(file, sheet_name=main_sheet, header=None)
        header_idx = next((i for i, r in raw_df.iterrows() if r.astype(str).str.contains('Description', na=False).any()), None)
        
        if header_idx is not None:
            store_codes_row = raw_df.iloc[header_idx + 1]
            df_clean = raw_df.iloc[header_idx:].copy()
            df_clean.columns = df_clean.iloc[0]; df_clean = df_clean.iloc[1:].reset_index(drop=True)
            store_columns = [c for c in df_clean.columns[4:] if "Unnamed" not in str(c)]
            
            all_rows = []; original_order = [] 

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
                            
                            # ✨ สร้างชื่อร้านแบบมีตัวย่อต่อท้าย (สาขา)
                            short_code = short_name_lookup.get(current_store_code, "")
                            display_store_name = f"{col_name} ( {short_code} )" if short_code else col_name
                            
                            all_rows.append({
                                'TRIP': route_lookup.get(current_store_code, "ไม่พบรหัส"), 
                                'STORE NAME': display_store_name, 
                                'Product': product, 
                                'Qty': qty
                            })
                    except: continue

            full_df = pd.DataFrame(all_rows)
            meat_kw = ['เนื้อ', 'หมู', 'Meat', 'Pork']
            fixed_top = ["ปูอัด", "ปูอัดชีส", "หอยเชลล์โฮตาเตะญี่ปุ่น(NW100%)", "ปลาดอลลี่ NW 70% (200-400)", "ชีสมอสซาเรลล่า", "คิมมาริ", "น้ำจิ้มพอนสึ ยูสุ (ถุง 2 ก.ก.)", "น้ำจิ้มสุกี้"]
            
            if not st.session_state.order_box: 
                box_items = [p for p in original_order if not any(kw in p for kw in meat_kw)]
                st.session_state.order_box = [p for p in fixed_top if p in box_items] + [p for p in box_items if p not in fixed_top]
            if not st.session_state.order_total: st.session_state.order_total = original_order

            with tab_setting:
                c1, c2 = st.columns(2)
                with c1: st.markdown("✨ **ป้ายกล่อง**"); st.session_state.order_box = sort_items(st.session_state.order_box, key="box")
                with c2: st.markdown("📋 **รายงานสรุป**"); st.session_state.order_total = sort_items(st.session_state.order_total, key="total")

            with tab_process:
                if st.button("🌟 เสกไฟล์เดี๋ยวนี้!"):
                    m_weight = full_df[full_df['Product'].str.contains('|'.join(meat_kw), na=False)].pivot_table(index=['TRIP', 'STORE NAME'], columns='Product', values='Qty', aggfunc='sum').fillna(0).reset_index()
                    m_box = full_df[~full_df['Product'].str.contains('|'.join(meat_kw), na=False)].pivot_table(index=['TRIP', 'STORE NAME'], columns='Product', values='Qty', aggfunc='sum').fillna(0).reset_index()
                    m_order = full_df.pivot_table(index=['TRIP', 'STORE NAME'], columns='Product', values='Qty', aggfunc='sum').fillna(0).reset_index()
                    
                    prods_box_list = [p for p in st.session_state.order_box if p in m_box.columns]
                    m_box = m_box[['TRIP', 'STORE NAME'] + prods_box_list].sort_values(['TRIP', 'STORE NAME'])
                    m_box['รวมจำนวน'] = m_box[prods_box_list].sum(axis=1)

                    output = io.BytesIO()
                    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                        wb = writer.book; header_bg = '#F2F2F2'
                        h_f = wb.add_format({'bold':True, 'align':'center', 'valign':'vcenter', 'bg_color':header_bg, 'border':1, 'text_wrap':True})
                        d_f_15 = wb.add_format({'border':1, 'align':'center', 'valign':'vcenter', 'font_size': 15})
                        d_f_21 = wb.add_format({'border':1, 'align':'center', 'valign':'vcenter', 'font_size': 21, 'bold': True})
                        s_f_21 = wb.add_format({'bold':True, 'bg_color':'#E9E9E9', 'border':1, 'num_format':'#,##0', 'valign':'vcenter', 'align':'center', 'font_size': 21})
                        
                        fixed_meat_list = ["เนื้อสันคอ", "เนื้อออส", "หมูสันคอ", "หมูสามชั้น", "หมูสันนอก", "หมูคูโรบุตะ"]

                        def get_val_by_kw(row, target_name):
                            if target_name in row: return row[target_name]
                            if target_name == "หมูสันคอ":
                                for col in row.index:
                                    if "สันคอ" in str(col) and "หมู" in str(col): return row[col]
                            if target_name == "หมูคูโรบุตะ":
                                kuro_kws = ["คุโร", "คูโร", "บูตะ", "บุตะ", "Kuro"]
                                for col in row.index:
                                    if all(k in str(col) for k in ["หมู", "สามชั้น"]) and any(k in str(col) for k in kuro_kws): return row[col]
                            if target_name == "เนื้อออส":
                                aus_kws = ["ออส", "Aus"]
                                for col in row.index:
                                    if any(k in str(col) for k in aus_kws): return row[col]
                            for col in row.index:
                                if str(target_name).replace(" ","") == str(col).replace(" ",""): return row[col]
                            return 0

                        # --- Sheets (ป้ายต่างๆ) ---
                        # (เหมือนเดิมเพื่อความเสถียรค่ะ)
                        ws1 = wb.add_worksheet("ป้ายน้ำหนัก")
                        ws1.set_landscape(); ws1.set_margins(0.2, 0.2, 0.2, 0.2); ws1.set_paper(9)
                        f_bnn = wb.add_format({'bold':True, 'size':30, 'border':2, 'align':'center', 'valign':'vcenter', 'bg_color':header_bg})
                        f_trip_v = wb.add_format({'bold':True, 'size':32, 'border':2, 'align':'center', 'valign':'vcenter'})
                        f_unit_v = wb.add_format({'bold':True, 'size':18, 'border':1, 'align':'center', 'valign':'vcenter'})
                        f_prod_v = wb.add_format({'bold':True, 'size':22, 'border':1, 'valign':'vcenter', 'indent':1})
                        f_store_v = wb.add_format({'bold':True, 'size':24, 'border':1, 'align':'center', 'valign':'vcenter'})
                        ws1.set_column('A:A', 38); ws1.set_column('B:E', 16)
                        row_idx = 0; breaks_w = []
                        for _, row_s in m_weight.iterrows():
                            ws1.merge_range(row_idx, 0, row_idx, 2, "BNN (สุกี้ตี๋น้อย)", f_bnn)
                            ws1.merge_range(row_idx, 3, row_idx, 4, row_s['TRIP'], f_trip_v)
                            ws1.set_row(row_idx, 65); ws1.write(row_idx + 1, 0, "STORE:", f_unit_v)
                            ws1.merge_range(row_idx + 1, 1, row_idx + 1, 4, row_s['STORE NAME'], f_store_v)
                            ws1.set_row(row_idx + 1, 55)
                            for i, item in enumerate(fixed_meat_list):
                                r = row_idx + 2 + i
                                ws1.write(r, 0, item, f_prod_v); ws1.write(r, 1, "", f_unit_v)
                                ws1.write(r, 2, "KG.", f_unit_v); ws1.write(r, 3, "", f_unit_v)
                                ws1.write(r, 4, "กล่อง" if item in ["เนื้อออส", "หมูคูโรบุตะ"] else "ตะกร้า", f_unit_v)
                                ws1.set_row(r, 62)
                            row_idx += 9; breaks_w.append(row_idx)
                        ws1.set_h_pagebreaks(breaks_w)

                        ws2 = wb.add_worksheet("ป้ายกล่อง")
                        ws2.set_landscape(); ws2.set_margins(0.2, 0.2, 0.2, 0.2); ws2.set_paper(9)
                        f_label_big = wb.add_format({'bold':True, 'size':40, 'border':1, 'align':'center', 'valign':'vcenter'})
                        f_qty_big = wb.add_format({'bold':True, 'size':80, 'border':1, 'align':'center', 'valign':'vcenter'})
                        ws2.set_column('A:A', 50); ws2.set_column('B:B', 60); b_row = 0; breaks_b = []
                        for _, row_b in m_box.iterrows():
                            ws2.merge_range(b_row, 0, b_row, 1, "BNN (สุกี้ตี๋น้อย)", wb.add_format({'bold':True, 'size':60, 'border':2, 'align':'center', 'valign':'vcenter', 'bg_color':header_bg}))
                            ws2.write(b_row+1, 0, "STORE NAME", f_label_big); ws2.write(b_row+1, 1, row_b['STORE NAME'], wb.add_format({'bold':True, 'size':35, 'border':1, 'align':'center', 'valign':'vcenter', 'text_wrap':True}))
                            ws2.write(b_row+2, 0, "จำนวนกล่อง", f_label_big); ws2.write(b_row+2, 1, row_b['รวมจำนวน'] if row_b['รวมจำนวน'] != 0 else "-", f_qty_big)
                            ws2.write(b_row+3, 0, "TRIP NO.", f_label_big); ws2.write(b_row+3, 1, row_b['TRIP'], wb.add_format({'bold':True, 'size':70, 'border':1, 'align':'center', 'valign':'vcenter'}))
                            ws2.set_row(b_row, 120); ws2.set_row(b_row+1, 100); ws2.set_row(b_row+2, 130); ws2.set_row(b_row+3, 120)
                            b_row += 4; breaks_b.append(b_row)
                        ws2.set_h_pagebreaks(breaks_b)

                        # --- 3. หน้าน้ำหนัก ---
                        ws3 = wb.add_worksheet("น้ำหนัก")
                        ws3.set_portrait(); ws3.set_paper(9); ws3.set_margins(0.2, 0.2, 0.2, 0.2); ws3.fit_to_pages(1, 0); ws3.repeat_rows(0, 1)
                        ws3.merge_range(0,0,1,0,"No.",h_f); ws3.merge_range(0,1,1,1,"TRIP",h_f); ws3.merge_range(0,2,1,2,"STORE NAME",h_f)
                        c_idx = 3
                        for p in fixed_meat_list:
                            ws3.write(0, c_idx, "จำนวนสั่ง", h_f); ws3.write(1, c_idx, p, h_f); ws3.merge_range(0, c_idx+1, 1, c_idx+1, "จ่ายจริง", h_f); c_idx += 2
                        ws3.merge_range(0, c_idx, 1, c_idx, "ตะกร้า", h_f); ws3.merge_range(0, c_idx+1, 1, c_idx+1, "กล่อง", h_f)
                        for i, r_val in m_weight.reset_index(drop=True).iterrows():
                            row_n = i+2; ws3.set_row(row_n, 35) 
                            ws3.write(row_n, 0, i+1, d_f_15); ws3.write(row_n, 1, r_val['TRIP'], d_f_15); ws3.write(row_n, 2, r_val['STORE NAME'], d_f_15)
                            d_idx = 3
                            for p in fixed_meat_list:
                                val = get_val_by_kw(r_val, p)
                                ws3.write(row_n, d_idx, val if val != 0 else "-", d_f_21); ws3.write(row_n, d_idx+1, "", d_f_15); d_idx += 2
                        t_row = len(m_weight) + 2; ws3.set_row(t_row, 35); ws3.write(t_row, 2, "TOTAL", s_f_21)
                        d_idx = 3
                        for p in fixed_meat_list:
                            total_sum = m_weight.apply(lambda r: get_val_by_kw(r, p), axis=1).sum()
                            ws3.write(t_row, d_idx, total_sum if total_sum != 0 else "-", s_f_21); ws3.write(t_row, d_idx+1, "", s_f_21); d_idx += 2
                        ws3.set_column('A:A', 6); ws3.set_column('B:B', 10); ws3.set_column('C:C', 30); ws3.set_column('D:ZZ', 10)

                        # --- 4. หน้าจัดกล่อง ---
                        ws4 = wb.add_worksheet("จัดกล่อง")
                        ws4.set_landscape(); ws4.set_paper(9); ws4.set_margins(0.2, 0.2, 0.2, 0.2); ws4.fit_to_pages(1, 0); ws4.repeat_rows(0, 0)
                        cols_box = list(m_box.columns); ws4.write(0, 0, "No.", h_f)
                        for idx, col in enumerate(cols_box): ws4.write(0, idx + 1, col, h_f)
                        for i, r_val in m_box.reset_index(drop=True).iterrows():
                            row_n = i+1; ws4.set_row(row_n, 35)
                            ws4.write(row_n, 0, i+1, d_f_15)
                            for idx, val in enumerate(r_val):
                                col_name = cols_box[idx]
                                if col_name in ['TRIP', 'STORE NAME']: ws4.write(row_n, idx+1, val, d_f_15)
                                else:
                                    display_val = val if val != 0 else "-"
                                    ws4.write(row_n, idx+1, display_val, s_f_21 if col_name == 'รวมจำนวน' else d_f_21)
                        l_row = len(m_box) + 1; ws4.set_row(l_row, 35); ws4.write(l_row, 2, "TOTAL", s_f_21)
                        for idx, col in enumerate(cols_box):
                            if col not in ['TRIP', 'STORE NAME']:
                                total_val = m_box[col].sum(); ws4.write(l_row, idx + 1, total_val if total_val != 0 else "-", s_f_21)
                        ws4.set_column('B:B', 10); ws4.set_column('C:C', 30); ws4.set_column('D:ZZ', 11)

                        # --- 5. หน้า Order ---
                        ws5 = wb.add_worksheet("Order")
                        ws5.set_portrait(); ws5.set_paper(9); ws5.fit_to_pages(1, 0); ws5.repeat_rows(0, 0)
                        order_cols = list(m_order.columns); ws5.write(0, 0, "No.", h_f)
                        for idx, col in enumerate(order_cols): ws5.write(0, idx + 1, col, h_f)
                        for i, r_val in m_order.reset_index(drop=True).iterrows():
                            ws5.write(i+1, 0, i+1, d_f_15)
                            for idx, val in enumerate(r_val):
                                display_val = val if val != 0 else "-" if order_cols[idx] not in ['TRIP', 'STORE NAME'] else val
                                ws5.write(i+1, idx+1, display_val, d_f_15)
                        ws5.set_column('B:B', 10); ws5.set_column('C:C', 30); ws5.set_column('D:ZZ', 9)

                    st.balloons()
                    st.download_button(label="💖 ดาวน์โหลดไฟล์ (มีตัวย่อสาขาแล้วค่ะคุณเดียร์!) 💖", data=output.getvalue(), file_name=f"Queen_Fixed_StoreCode_{datetime.now().strftime('%Y-%m-%d')}.xlsx")
    except Exception as e: st.error(f"อุ๊ย! ผิดพลาดค่ะ: {e}")