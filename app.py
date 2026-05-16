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
        </style>
    """, unsafe_allow_html=True)

sassy_css()
st.markdown("<h1>Queen Logistics Center 💅</h1>", unsafe_allow_html=True)

if 'order_box' not in st.session_state: st.session_state.order_box = []
if 'order_total' not in st.session_state: st.session_state.order_total = []

tab_upload, tab_setting, tab_process = st.tabs(["💅 อัปโหลดไฟล์", "↕️ ลำดับสินค้า", "🚀 ประมวลผล"])

with tab_upload:
    file = st.file_uploader("ส่งไฟล์ Excel มาเลยค่ะคุณเดียร์ ปรับปรุงชื่อเนื้อออสเป็นเนื้อวัวออสเตรเลียเรียบร้อย!", type=["xlsx"])

if file:
    try:
        route_df = pd.read_excel(file, sheet_name='Route', header=None)
        route_lookup = {str(r[0]).strip(): str(r[2]).strip() for _, r in route_df.iterrows() if pd.notna(r[0])}
        short_name_lookup = {str(r[0]).strip(): str(r[0]).strip() for _, r in route_df.iterrows() if pd.notna(r[0])}
        
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
                            short_code = short_name_lookup.get(current_store_code, "")
                            display_name = f"{col_name} ( {short_code} )" if short_code else col_name
                            
                            all_rows.append({
                                'TRIP': route_lookup.get(current_store_code, "ไม่พบรหัส"), 
                                'STORE NAME': display_name, 
                                'Product': product, 
                                'Qty': qty
                            })
                    except: continue

            full_df = pd.DataFrame(all_rows)
            
            # 🔥 แก้ไขตรงนี้: เปลี่ยนจาก "เนื้อออส" เป็น "เนื้อวัวออสเตรเลีย" ให้ตรงกับไฟล์ดิบ
            meat_items = ["เนื้อสันคอ", "เนื้อวัวออสเตรเลีย", "สันคอหมู", "หมูสามชั้น", "หมูสันนอก", "หมูคูโรบุตะ"]
            fixed_top = ["ปูอัด", "ปูอัดชีส", "หอยเชลล์โฮตาเตะญี่ปุ่น(NW100%)", "ปลาดอลลี่ NW 70% (200-400)", "ชีสมอสซาเรลล่า", "คิมมาริ", "น้ำจิ้มพอนสึ ยูสุ (ถุง 2 ก.ก.)", "น้ำจิ้มสุกี้"]
            
            # --- ระบบเรียงลำดับสินค้า (หน้าจัดกล่อง และหน้า Order) ---
            if not st.session_state.order_box: 
                # ดึงรายการที่ไม่ใช่กลุ่ม meat_items (ทำให้ "เนื้อวัวออสเตรเลีย" ไม่ไปโผล่ในหน้าจัดกล่องแน่นอน)
                box_items = [p for p in original_order if p not in meat_items]
                st.session_state.order_box = [p for p in fixed_top if p in box_items] + [p for p in box_items if p not in fixed_top]
            if not st.session_state.order_total: st.session_state.order_total = original_order

            with tab_setting:
                c1, c2 = st.columns(2)
                with c1: st.markdown("✨ **จัดลำดับหน้าจัดกล่อง**"); st.session_state.order_box = sort_items(st.session_state.order_box, key="box")
                with c2: st.markdown("📋 **จัดลำดับหน้า Order**"); st.session_state.order_total = sort_items(st.session_state.order_total, key="total")

            with tab_process:
                if st.button("🚀 ประมวลผลระบบครบจบ (แก้ไขชื่อเนื้อออสเรียบร้อย)"):
                    # 1. ข้อมูลหน้าน้ำหนัก
                    m_weight = full_df[full_df['Product'].isin(meat_items)].pivot_table(index=['TRIP', 'STORE NAME'], columns='Product', values='Qty', aggfunc='sum').fillna(0).reset_index()
                    # ตรวจสอบว่าคอลัมน์มาครบตามที่กำหนดใน meat_items ไหม ถ้าไม่มีให้สร้างคอลัมน์ว่างรอไว้
                    for col in meat_items:
                        if col not in m_weight.columns:
                            m_weight[col] = 0.0
                    
                    # 2. ข้อมูลหน้าจัดกล่อง (ใช้ลำดับจาก session_state ซึ่งคัดเนื้อออกไปแล้ว)
                    m_box = full_df[~full_df['Product'].isin(meat_items)].pivot_table(index=['TRIP', 'STORE NAME'], columns='Product', values='Qty', aggfunc='sum').fillna(0).reset_index()
                    prods_box_list = [p for p in st.session_state.order_box if p in m_box.columns]
                    m_box = m_box[['TRIP', 'STORE NAME'] + prods_box_list].sort_values(['TRIP', 'STORE NAME'])
                    m_box['รวมจำนวน'] = m_box[prods_box_list].sum(axis=1)
                    
                    # 3. ข้อมูลหน้า Order (ใช้ลำดับจาก session_state)
                    m_order = full_df.pivot_table(index=['TRIP', 'STORE NAME'], columns='Product', values='Qty', aggfunc='sum').fillna(0).reset_index()
                    prods_order_list = [p for p in st.session_state.order_total if p in m_order.columns]
                    m_order = m_order[['TRIP', 'STORE NAME'] + prods_order_list].sort_values(['TRIP', 'STORE NAME'])

                    output = io.BytesIO()
                    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                        wb = writer.book
                        # --- Formats ---
                        h_f = wb.add_format({'bold':True, 'align':'center', 'valign':'vcenter', 'bg_color':'#F2F2F2', 'border':1, 'text_wrap':True})
                        d_f_15 = wb.add_format({'border':1, 'align':'center', 'valign':'vcenter', 'font_size': 15})
                        d_f_15_left = wb.add_format({'border':1, 'align':'left', 'valign':'vcenter', 'font_size': 15, 'indent': 1})
                        d_f_21 = wb.add_format({'border':1, 'align':'center', 'valign':'vcenter', 'font_size': 21, 'bold': True})
                        s_f_21 = wb.add_format({'bold':True, 'bg_color':'#E9E9E9', 'border':1, 'num_format':'#,##0', 'valign':'vcenter', 'align':'center', 'font_size': 21})
                        s_f_21_left = wb.add_format({'bold':True, 'bg_color':'#E9E9E9', 'border':1, 'valign':'vcenter', 'align':'left', 'font_size': 21, 'indent': 1})

                        # [1. ป้ายน้ำหนัก]
                        ws1 = wb.add_worksheet("ป้ายน้ำหนัก")
                        ws1.set_landscape(); ws1.set_margins(0.2, 0.2, 0.2, 0.2); ws1.set_paper(9)
                        f_bnn = wb.add_format({'bold':True, 'size':30, 'border':2, 'align':'center', 'valign':'vcenter', 'bg_color':'#F2F2F2'})
                        f_trip_v = wb.add_format({'bold':True, 'size':32, 'border':2, 'align':'center', 'valign':'vcenter'})
                        f_unit_v = wb.add_format({'bold':True, 'size':18, 'border':1, 'align':'center', 'valign':'vcenter'})
                        f_prod_v = wb.add_format({'bold':True, 'size':22, 'border':1, 'valign':'vcenter', 'indent':1})
                        f_st_v_l = wb.add_format({'bold':True, 'size':24, 'border':1, 'align':'left', 'valign':'vcenter', 'indent': 1})
                        ws1.set_column('A:A', 38); ws1.set_column('B:E', 16)
                        row_idx = 0; breaks_w = []
                        for _, row_s in m_weight.iterrows():
                            ws1.merge_range(row_idx, 0, row_idx, 2, "BNN (สุกี้ตี๋น้อย)", f_bnn)
                            ws1.merge_range(row_idx, 3, row_idx, 4, row_s['TRIP'], f_trip_v)
                            ws1.set_row(row_idx, 65); ws1.write(row_idx + 1, 0, "STORE:", f_unit_v)
                            ws1.merge_range(row_idx + 1, 1, row_idx + 1, 4, row_s['STORE NAME'], f_st_v_l)
                            ws1.set_row(row_idx + 1, 55)
                            for i, item in enumerate(meat_items):
                                r = row_idx + 2 + i
                                # เปลี่ยนการแสดงผลป้ายน้ำหนักให้แสดงเป็นคำสั้นหรือตามต้องการ (ในที่นี้แสดงตาม meat_items)
                                display_item = "เนื้อออส" if item == "เนื้อวัวออสเตรเลีย" else item
                                ws1.write(r, 0, display_item, f_prod_v); ws1.write(r, 1, "", f_unit_v)
                                ws1.write(r, 2, "KG.", f_unit_v); ws1.write(r, 3, "", f_unit_v)
                                ws1.write(r, 4, "กล่อง" if "ออส" in item or "คูโร" in item else "ตะกร้า", f_unit_v)
                                ws1.set_row(r, 62)
                            row_idx += 9; breaks_w.append(row_idx)
                        ws1.set_h_pagebreaks(breaks_w)

                        # [2. ป้ายกล่อง]
                        ws2 = wb.add_worksheet("ป้ายกล่อง")
                        ws2.set_landscape(); ws2.set_margins(0.2, 0.2, 0.2, 0.2); ws2.set_paper(9)
                        f_l_big = wb.add_format({'bold':True, 'size':40, 'border':2, 'align':'center', 'valign':'vcenter'})
                        f_q_big = wb.add_format({'bold':True, 'size':80, 'border':2, 'align':'center', 'valign':'vcenter'})
                        f_st_big_l = wb.add_format({'bold':True, 'size':35, 'border':2, 'align':'left', 'valign':'vcenter', 'text_wrap':True, 'indent': 1})
                        ws2.set_column('A:A', 50); ws2.set_column('B:B', 60); b_row = 0; breaks_b = []
                        for _, row_b in m_box.iterrows():
                            ws2.merge_range(b_row, 0, b_row, 1, "BNN (สุกี้ตี๋น้อย)", wb.add_format({'bold':True, 'size':60, 'border':2, 'align':'center', 'valign':'vcenter', 'bg_color':'#F2F2F2'}))
                            ws2.write(b_row+1, 0, "STORE NAME", f_l_big); ws2.write(b_row+1, 1, row_b['STORE NAME'], f_st_big_l)
                            ws2.write(b_row+2, 0, "จำนวนกล่อง", f_l_big); ws2.write(b_row+2, 1, row_b['รวมจำนวน'] if row_b['รวมจำนวน'] != 0 else "-", f_q_big)
                            ws2.write(b_row+3, 0, "TRIP NO.", f_l_big); ws2.write(b_row+3, 1, row_b['TRIP'], wb.add_format({'bold':True, 'size':70, 'border':2, 'align':'center', 'valign':'vcenter'}))
                            ws2.set_row(b_row, 120); ws2.set_row(b_row+1, 100); ws2.set_row(b_row+2, 130); ws2.set_row(b_row+3, 120)
                            b_row += 4; breaks_b.append(b_row)
                        ws2.set_h_pagebreaks(breaks_b)

                        # --- 3. หน้าน้ำหนัก (เปลี่ยนหัวข้อเป็น เนื้อวัวออสเตรเลีย + Row 80) ---
                        ws3 = wb.add_worksheet("น้ำหนัก")
                        ws3.set_portrait(); ws3.set_paper(9); ws3.set_margins(0.2, 0.2, 0.2, 0.2); ws3.fit_to_pages(1, 0); ws3.repeat_rows(0, 1)
                        ws3.merge_range(0,0,1,0,"No.",h_f); ws3.merge_range(0,1,1,1,"TRIP",h_f); ws3.merge_range(0,2,1,2,"STORE NAME",h_f)
                        c_idx = 3
                        for p in meat_items:
                            ws3.write(0, c_idx, "จำนวนสั่ง", h_f); ws3.write(1, c_idx, p, h_f); ws3.merge_range(0, c_idx+1, 1, c_idx+1, "จ่ายจริง", h_f); c_idx += 2
                        ws3.merge_range(0, c_idx, 1, c_idx, "ตะกร้า", h_f); ws3.merge_range(0, c_idx+1, 1, c_idx+1, "กล่อง", h_f)
                        
                        for i, r_val in m_weight.iterrows():
                            rn = i+2; ws3.set_row(rn, 80) # Row Height 80
                            ws3.write(rn, 0, i+1, d_f_15); ws3.write(rn, 1, r_val['TRIP'], d_f_15); ws3.write(rn, 2, r_val['STORE NAME'], d_f_15_left)
                            d_idx = 3
                            for p in meat_items:
                                val = r_val[p] if p in r_val else 0
                                ws3.write(rn, d_idx, val if val != 0 else "-", d_f_21); ws3.write(rn, d_idx+1, "", d_f_15); d_idx += 2
                            ws3.write(rn, d_idx, "", d_f_15); ws3.write(rn, d_idx+1, "", d_f_15)
                        
                        # แถว TOTAL (สีเทาลากยันขวา)
                        t_row = len(m_weight) + 2; ws3.set_row(t_row, 80)
                        ws3.write(t_row, 0, "", s_f_21); ws3.write(t_row, 1, "", s_f_21); ws3.write(t_row, 2, "TOTAL", s_f_21_left)
                        d_idx = 3
                        for p in meat_items:
                            total = m_weight[p].sum() if p in m_weight.columns else 0
                            ws3.write(t_row, d_idx, total if total != 0 else "-", s_f_21)
                            ws3.write(t_row, d_idx+1, "", s_f_21); d_idx += 2
                        ws3.write(t_row, d_idx, "", s_f_21); ws3.write(t_row, d_idx+1, "", s_f_21)
                        ws3.set_column('A:A', 6); ws3.set_column('B:B', 10); ws3.set_column('C:C', 35); ws3.set_column('D:ZZ', 10)

                        # --- 4. หน้าจัดกล่อง (ไม่มี เนื้อวัวออสเตรเลีย แน่นอน) ---
                        ws4 = wb.add_worksheet("จัดกล่อง")
                        ws4.set_landscape(); ws4.set_paper(9); ws4.set_margins(0.2, 0.2, 0.2, 0.2); ws4.fit_to_pages(1, 0)
                        cols_b = list(m_box.columns); ws4.write(0, 0, "No.", h_f)
                        for idx, col in enumerate(cols_b): ws4.write(0, idx + 1, col, h_f)
                        for i, r_val in m_box.reset_index(drop=True).iterrows():
                            rn = i+1; ws4.set_row(rn, 35); ws4.write(rn, 0, i+1, d_f_15)
                            for idx, col in enumerate(cols_b):
                                val = r_val[col]
                                if col == 'TRIP': ws4.write(rn, idx+1, val, d_f_15)
                                elif col == 'STORE NAME': ws4.write(rn, idx+1, val, d_f_15_left)
                                else: ws4.write(rn, idx+1, (val if val != 0 else "-"), s_f_21 if col == 'รวมจำนวน' else d_f_21)
                        # TOTAL หน้าจัดกล่อง
                        l_row_b = len(m_box) + 1; ws4.set_row(l_row_b, 35); ws4.write(l_row_b, 0, "", s_f_21); ws4.write(l_row_b, 1, "", s_f_21); ws4.write(l_row_b, 2, "TOTAL", s_f_21_left)
                        for idx, col in enumerate(cols_b):
                            if col not in ['TRIP', 'STORE NAME']:
                                total = m_box[col].sum(); ws4.write(l_row_b, idx + 1, total if total != 0 else "-", s_f_21)
                        ws4.set_column('B:B', 10); ws4.set_column('C:C', 35); ws4.set_column('D:ZZ', 12)

                        # --- 5. หน้า Order ---
                        ws5 = wb.add_worksheet("Order")
                        ws5.set_landscape(); ws5.set_paper(9); ws5.fit_to_pages(1, 0)
                        cols_o = ['TRIP', 'STORE NAME'] + prods_order_list; ws5.write(0, 0, "No.", h_f)
                        for idx, col in enumerate(cols_o): ws5.write(0, idx + 1, col, h_f)
                        for i, r_val in m_order.reset_index(drop=True).iterrows():
                            ws5.write(i+1, 0, i+1, d_f_15)
                            for idx, col in enumerate(cols_o):
                                val = r_val[col]
                                if col == 'STORE NAME': ws5.write(i+1, idx+1, val, d_f_15_left)
                                else: ws5.write(i+1, idx+1, (val if val != 0 else "-"), d_f_15)
                        ws5.set_column('B:B', 10); ws5.set_column('C:C', 35); ws5.set_column('D:ZZ', 10)

                    st.balloons()
                    st.download_button(label="💖 โหลดไฟล์แก้ชื่อเนื้อออส + ลบออกจากหน้าจัดกล่องแล้วค่ะเดียร์! 💖", 
                                     data=output.getvalue(), 
                                     file_name=f"Queen_Logistics_Fixed_Ostrich_{datetime.now().strftime('%H%M')}.xlsx")
    except Exception as e: st.error(f"อุ๊ย! ขอโทษทีค่ะเดียร์ มีจุดผิด: {e}")
