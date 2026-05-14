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
        route_df = pd.read_excel(file, sheet_name='Route', header=None)
        route_lookup = {str(r[0]).strip(): str(r[2]).strip() for _, r in route_df.iterrows() if pd.notna(r[0])}
        code_lookup = {str(r[0]).strip(): str(r[0]).strip() for _, r in route_df.iterrows() if pd.notna(r[0])}

        xls = pd.ExcelFile(file); main_sheet = xls.sheet_names[0]
        raw_df = pd.read_excel(file, sheet_name=main_sheet, header=None)
        header_idx = next((i for i, r in raw_df.iterrows() if r.astype(str).str.contains('Description', na=False).any()), None)
        
        if header_idx is not None:
            store_codes_row = raw_df.iloc[header_idx + 1]
            df_clean = raw_df.iloc[header_idx:].copy()
            df_clean.columns = df_clean.iloc[0]; df_clean = df_clean.iloc[1:].reset_index(drop=True)
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
                            store_id = code_lookup.get(current_store_code, "")
                            formatted_store_name = f"{col_name} ( {store_id} )" if store_id else col_name
                            
                            all_rows.append({
                                'TRIP': route_lookup.get(current_store_code, "ไม่พบรหัส"), 
                                'STORE NAME': formatted_store_name, 
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
                    # 1. ข้อมูลสำหรับหน้าน้ำหนัก
                    m_weight = full_df[full_df['Product'].str.contains('|'.join(meat_kw), na=False)].pivot_table(index=['TRIP', 'STORE NAME'], columns='Product', values='Qty', aggfunc='sum').fillna(0).reset_index()
                    
                    # 2. ข้อมูลสำหรับหน้าจัดกล่อง
                    m_box = full_df[~full_df['Product'].str.contains('|'.join(meat_kw), na=False)].pivot_table(index=['TRIP', 'STORE NAME'], columns='Product', values='Qty', aggfunc='sum').fillna(0).reset_index()
                    prods_box_list = [p for p in st.session_state.order_box if p in m_box.columns]
                    m_box = m_box[['TRIP', 'STORE NAME'] + prods_box_list].sort_values(['TRIP', 'STORE NAME'])
                    # ✨ ผลรวมหายไปตรงนี้: เพิ่มกลับเข้าให้นะคะ
                    m_box['รวมจำนวน'] = m_box[prods_box_list].sum(axis=1)

                    # 3. ข้อมูลสำหรับหน้า Order (สรุปทั้งหมด)
                    prods_total_list = [p for p in st.session_state.order_total if p in full_df['Product'].unique()]
                    m_order = full_df.pivot_table(index=['TRIP', 'STORE NAME'], columns='Product', values='Qty', aggfunc='sum').fillna(0).reset_index()
                    m_order = m_order[['TRIP', 'STORE NAME'] + [p for p in prods_total_list if p in m_order.columns]].sort_values(['TRIP', 'STORE NAME'])

                    output = io.BytesIO()
                    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                        wb = writer.book; header_bg = '#F2F2F2'
                        h_f = wb.add_format({'bold':True, 'align':'center', 'valign':'vcenter', 'bg_color':header_bg, 'border':1, 'text_wrap':True})
                        
                        # Formats
                        d_f_text = wb.add_format({'border':1, 'align':'left', 'valign':'vcenter', 'font_size': 14, 'text_wrap': True, 'indent': 1})
                        d_f_num = wb.add_format({'border':1, 'align':'center', 'valign':'vcenter', 'font_size': 14})
                        d_f_num_bold = wb.add_format({'border':1, 'align':'center', 'valign':'vcenter', 'font_size': 16, 'bold': True})
                        s_f_total = wb.add_format({'bold':True, 'bg_color':'#E9E9E9', 'border':1, 'num_format':'#,##0', 'valign':'vcenter', 'align':'center', 'font_size': 16})
                        
                        fixed_meat_list = ["เนื้อสันคอ", "เนื้อออส", "หมูสันคอ", "หมูสามชั้น", "หมูสันนอก", "หมูคูโรบุตะ"]

                        def get_val_by_kw(row, target_name):
                            for col in row.index:
                                if str(target_name).strip() == str(col).strip(): return row[col]
                            return 0

                        # --- หน้า ป้ายน้ำหนัก / ป้ายกล่อง ---
                        # (ส่วนประกอบของป้ายสลิปยังคงไว้ตามเดิม)
                        ws1 = wb.add_worksheet("ป้ายน้ำหนัก")
                        ws1.set_landscape(); ws1.set_margins(0.2, 0.2, 0.2, 0.2); ws1.set_paper(9)
                        ws2 = wb.add_worksheet("ป้ายกล่อง")
                        ws2.set_landscape(); ws2.set_margins(0.2, 0.2, 0.2, 0.2); ws2.set_paper(9)

                        # --- 3. หน้าน้ำหนัก (A4 แนวตั้ง) ---
                        ws3 = wb.add_worksheet("น้ำหนัก")
                        ws3.set_paper(9); ws3.set_portrait(); ws3.set_margins(0.2, 0.2, 0.2, 0.2); ws3.repeat_rows(0, 1)
                        ws3.merge_range(0,0,1,0,"No.",h_f); ws3.merge_range(0,1,1,1,"TRIP",h_f); ws3.merge_range(0,2,1,2,"STORE NAME",h_f)
                        c_idx = 3
                        for p in fixed_meat_list:
                            ws3.write(0, c_idx, "จำนวนสั่ง", h_f); ws3.write(1, c_idx, p, h_f); ws3.merge_range(0, c_idx+1, 1, c_idx+1, "จ่ายจริง", h_f); c_idx += 2
                        ws3.merge_range(0, c_idx, 1, c_idx, "ตะกร้า", h_f); ws3.merge_range(0, c_idx+1, 1, c_idx+1, "กล่อง", h_f)
                        for i, r_val in m_weight.reset_index(drop=True).iterrows():
                            row_n = i+2; ws3.set_row(row_n, 45)
                            ws3.write(row_n, 0, i+1, d_f_num); ws3.write(row_n, 1, r_val['TRIP'], d_f_text); ws3.write(row_n, 2, r_val['STORE NAME'], d_f_text)
                            d_idx = 3
                            for p in fixed_meat_list:
                                val = get_val_by_kw(r_val, p)
                                ws3.write(row_n, d_idx, val if val != 0 else "-", d_f_num_bold); ws3.write(row_n, d_idx+1, "", d_f_num); d_idx += 2
                        ws3.set_column('A:A', 5); ws3.set_column('B:B', 10); ws3.set_column('C:C', 35); ws3.set_column('D:ZZ', 8)

                        # --- 4. หน้าจัดกล่อง (A4 แนวนอน - ผลรวมต้องมา!) ---
                        ws4 = wb.add_worksheet("จัดกล่อง")
                        ws4.set_paper(9); ws4.set_landscape(); ws4.set_margins(0.2, 0.2, 0.2, 0.2); ws4.repeat_rows(0, 0)
                        cols_box = list(m_box.columns); ws4.write(0, 0, "No.", h_f)
                        for idx, col in enumerate(cols_box): ws4.write(0, idx + 1, col, h_f)
                        for i, r_val in m_box.reset_index(drop=True).iterrows():
                            row_n = i+1; ws4.set_row(row_n, 45)
                            ws4.write(row_n, 0, i+1, d_f_num)
                            for idx, col_name in enumerate(cols_box):
                                val = r_val[col_name]
                                if col_name in ['TRIP', 'STORE NAME']:
                                    ws4.write(row_n, idx+1, val, d_f_text)
                                elif col_name == 'รวมจำนวน':
                                    ws4.write(row_n, idx+1, val if val != 0 else "-", s_f_total)
                                else:
                                    ws4.write(row_n, idx+1, val if val != 0 else "-", d_f_num_bold)
                        ws4.set_column('B:B', 10); ws4.set_column('C:C', 35); ws4.set_column('D:ZZ', 12)

                        # --- 5. หน้า Order (A4 แนวตั้ง) ---
                        ws5 = wb.add_worksheet("Order")
                        ws5.set_paper(9); ws5.set_portrait(); ws5.set_margins(0.2, 0.2, 0.2, 0.2); ws5.repeat_rows(0, 0)
                        order_cols = list(m_order.columns); ws5.write(0, 0, "No.", h_f)
                        for idx, col in enumerate(order_cols): ws5.write(0, idx + 1, col, h_f)
                        for i, r_val in m_order.reset_index(drop=True).iterrows():
                            row_n = i+1; ws5.set_row(row_n, 45)
                            ws5.write(row_n, 0, i+1, d_f_num)
                            for idx, col_name in enumerate(order_cols):
                                val = r_val[col_name]
                                ws5.write(row_n, idx+1, val if val != 0 else "-" if col_name not in ['TRIP', 'STORE NAME'] else val, d_f_text if col_name in ['TRIP', 'STORE NAME'] else d_f_num)
                        ws5.set_column('B:B', 10); ws5.set_column('C:C', 35); ws5.set_column('D:ZZ', 10)

                    st.balloons()
                    st.download_button(label="💖 ดาวน์โหลดไฟล์ (คืนชีพผลรวมจัดกล่อง!) 💖", data=output.getvalue(), file_name=f"Queen_Full_Fixed_{datetime.now().strftime('%Y-%m-%d')}.xlsx")
    except Exception as e: st.error(f"อุ๊ย! ผิดพลาดค่ะ: {e}")