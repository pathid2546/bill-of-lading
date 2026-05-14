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
        # 1. เตรียมข้อมูล Route และตัวย่อสาขา
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
            
            # --- ปรับแยกหมวดหมู่สินค้าให้แม่นยำขึ้น ---
            # สินค้าที่จะไปหน้า "น้ำหนัก" (กลุ่มเนื้อสัตว์)
            meat_items = ["เนื้อสันคอ", "เนื้อออส", "หมูสันคอ", "หมูสามชั้น", "หมูสันนอก", "หมูคูโรบุตะ", "สันคอหมู"]
            
            fixed_top = ["ปูอัด", "ปูอัดชีส", "หอยเชลล์โฮตาเตะญี่ปุ่น(NW100%)", "ปลาดอลลี่ NW 70% (200-400)", "ชีสมอสซาเรลล่า", "คิมมาริ", "น้ำจิ้มพอนสึ ยูสุ (ถุง 2 ก.ก.)", "น้ำจิ้มสุกี้"]
            
            if not st.session_state.order_box: 
                box_items = [p for p in original_order if p not in meat_items]
                st.session_state.order_box = [p for p in fixed_top if p in box_items] + [p for p in box_items if p not in fixed_top]
            if not st.session_state.order_total: st.session_state.order_total = original_order

            with tab_setting:
                c1, c2 = st.columns(2)
                with c1: st.markdown("✨ **จัดลำดับสินค้า (หน้าจัดกล่อง)**"); st.session_state.order_box = sort_items(st.session_state.order_box, key="box")
                with c2: st.markdown("📋 **จัดลำดับสินค้า (หน้า Order)**"); st.session_state.order_total = sort_items(st.session_state.order_total, key="total")

            with tab_process:
                if st.button("🌟 เสกไฟล์แบบแยก เนื้อสันคอ vs สันคอหมู ให้เดียร์!"):
                    m_weight = full_df[full_df['Product'].isin(meat_items)].pivot_table(index=['TRIP', 'STORE NAME'], columns='Product', values='Qty', aggfunc='sum').fillna(0).reset_index()
                    m_box = full_df[~full_df['Product'].isin(meat_items)].pivot_table(index=['TRIP', 'STORE NAME'], columns='Product', values='Qty', aggfunc='sum').fillna(0).reset_index()
                    m_order = full_df.pivot_table(index=['TRIP', 'STORE NAME'], columns='Product', values='Qty', aggfunc='sum').fillna(0).reset_index()
                    
                    prods_box_list = [p for p in st.session_state.order_box if p in m_box.columns]
                    m_box = m_box[['TRIP', 'STORE NAME'] + prods_box_list].sort_values(['TRIP', 'STORE NAME'])
                    m_box['รวมจำนวน'] = m_box[prods_box_list].sum(axis=1)

                    output = io.BytesIO()
                    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                        wb = writer.book
                        header_bg = '#F2F2F2'
                        
                        # --- สร้าง Format แบบตีกรอบเข้มชัดเจน ---
                        h_f = wb.add_format({'bold':True, 'align':'center', 'valign':'vcenter', 'bg_color':header_bg, 'border':1, 'text_wrap':True})
                        d_f_15 = wb.add_format({'border':1, 'align':'center', 'valign':'vcenter', 'font_size': 15})
                        d_f_15_left = wb.add_format({'border':1, 'align':'left', 'valign':'vcenter', 'font_size': 15, 'indent': 1})
                        d_f_21 = wb.add_format({'border':1, 'align':'center', 'valign':'vcenter', 'font_size': 21, 'bold': True})
                        s_f_21 = wb.add_format({'bold':True, 'bg_color':'#E9E9E9', 'border':1, 'num_format':'#,##0', 'valign':'vcenter', 'align':'center', 'font_size': 21})
                        s_f_21_left = wb.add_format({'bold':True, 'bg_color':'#E9E9E9', 'border':1, 'valign':'vcenter', 'align':'left', 'font_size': 21, 'indent': 1})

                        # หัวตารางหน้า "น้ำหนัก" ตามที่เดียร์ต้องการ
                        display_cols = ["เนื้อสันคอ", "เนื้อออส", "หมูสันคอ", "สันคอหมู", "หมูสามชั้น", "หมูสันนอก", "หมูคูโรบุตะ"]

                        def get_val(row, p_name):
                            return row[p_name] if p_name in row else 0

                        # --- 1. หน้าน้ำหนัก ---
                        ws3 = wb.add_worksheet("น้ำหนัก")
                        ws3.set_portrait(); ws3.set_paper(9); ws3.set_margins(0.2, 0.2, 0.2, 0.2); ws3.fit_to_pages(1, 0); ws3.repeat_rows(0, 1)
                        
                        # เขียนหัวตารางแบบตีกรอบทุกช่อง
                        ws3.merge_range(0,0,1,0,"No.",h_f); ws3.merge_range(0,1,1,1,"TRIP",h_f); ws3.merge_range(0,2,1,2,"STORE NAME",h_f)
                        c_idx = 3
                        for p in display_cols:
                            ws3.write(0, c_idx, "จำนวนสั่ง", h_f); ws3.write(1, c_idx, p, h_f)
                            ws3.merge_range(0, c_idx+1, 1, c_idx+1, "จ่ายจริง", h_f)
                            c_idx += 2
                        ws3.merge_range(0, c_idx, 1, c_idx, "ตะกร้า", h_f); ws3.merge_range(0, c_idx+1, 1, c_idx+1, "กล่อง", h_f)
                        
                        # เขียนข้อมูลพร้อมตีกรอบ
                        for i, r_val in m_weight.iterrows():
                            rn = i+2; ws3.set_row(rn, 35)
                            ws3.write(rn, 0, i+1, d_f_15); ws3.write(rn, 1, r_val['TRIP'], d_f_15)
                            ws3.write(rn, 2, r_val['STORE NAME'], d_f_15_left)
                            d_idx = 3
                            for p in display_cols:
                                val = get_val(r_val, p)
                                ws3.write(rn, d_idx, val if val != 0 else "-", d_f_21)
                                ws3.write(rn, d_idx+1, "", d_f_15); d_idx += 2
                            # ช่องตะกร้า/กล่องเปล่าแต่ต้องตีกรอบ
                            ws3.write(rn, d_idx, "", d_f_15); ws3.write(rn, d_idx+1, "", d_f_15)
                        
                        # บรรทัดสรุปผล (TOTAL)
                        t_row = len(m_weight) + 2; ws3.set_row(t_row, 35); ws3.write(t_row, 2, "TOTAL", s_f_21_left)
                        d_idx = 3
                        for p in display_cols:
                            total = m_weight[p].sum() if p in m_weight.columns else 0
                            ws3.write(t_row, d_idx, total if total != 0 else "-", s_f_21)
                            ws3.write(t_row, d_idx+1, "", s_f_21); d_idx += 2
                        
                        ws3.set_column('A:A', 6); ws3.set_column('B:B', 10); ws3.set_column('C:C', 35); ws3.set_column('D:ZZ', 10)

                        # --- หน้าอื่นๆ (จัดกล่อง / Order / ป้าย) คงเดิมแต่เน้นตีกรอบเข้ม ---
                        # [โค้ดส่วนหน้า จัดกล่อง และ Order จะเหมือนเดิมแต่ใช้ Format d_f_15 ที่มี border:1]
                        ws4 = wb.add_worksheet("จัดกล่อง")
                        cols_b = list(m_box.columns); ws4.write(0, 0, "No.", h_f)
                        for idx, col in enumerate(cols_b): ws4.write(0, idx + 1, col, h_f)
                        for i, r_val in m_box.reset_index(drop=True).iterrows():
                            rn = i+1; ws4.set_row(rn, 35); ws4.write(rn, 0, i+1, d_f_15)
                            for idx, col in enumerate(cols_b):
                                val = r_val[col]
                                if col == 'STORE NAME': ws4.write(rn, idx+1, val, d_f_15_left)
                                else: ws4.write(rn, idx+1, val if val != 0 else "-", d_f_21 if col == 'รวมจำนวน' else d_f_15)

                    st.balloons()
                    st.download_button(label="💖 โหลดไฟล์ 'เนื้อสันคอ vs สันคอหมู' แบบตีกรอบเข้มได้เลยค่ะ! 💖", 
                                     data=output.getvalue(), 
                                     file_name=f"Queen_Logistics_Sankor_Split_{datetime.now().strftime('%H%M')}.xlsx")
    except Exception as e: st.error(f"อุ๊ย! มีปัญหาตอนประมวลผลค่ะ: {e}")