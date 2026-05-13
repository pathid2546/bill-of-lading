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
        
        /* พื้นหลังแบบตัวมารดา */
        .main {
            background: linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%);
            color: #ffffff !important;
            font-family: 'Kanit', sans-serif;
        }

        /* หัวข้อจึ้งๆ */
        h1 {
            background: linear-gradient(90deg, #FF007A, #FF85A1, #FFFFFF, #FF85A1, #FF007A);
            background-size: 200% auto;
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            animation: shine 3s linear infinite;
            text-align: center;
            font-size: 4rem !important;
            font-weight: 800 !important;
            padding: 2rem 0;
            text-transform: uppercase;
            letter-spacing: 5px;
        }

        @keyframes shine {
            to { background-position: 200% center; }
        }

        /* ปุ่มแบบเล็บเจลฉ่ำวาว */
        div.stButton > button {
            background: linear-gradient(135deg, #FF007A 0%, #9000FF 100%) !important;
            color: white !important;
            border: none !important;
            border-radius: 50px !important;
            font-weight: bold !important;
            font-size: 1.2rem !important;
            height: 70px !important;
            width: 100% !important;
            transition: 0.4s all ease-in-out !important;
            box-shadow: 0 10px 20px rgba(255, 0, 122, 0.4) !important;
            text-transform: uppercase;
        }

        div.stButton > button:hover {
            transform: scale(1.05) translateY(-5px) !important;
            box-shadow: 0 15px 30px rgba(144, 0, 255, 0.6) !important;
            letter-spacing: 3px;
        }

        /* Tabs แบบตัวแม่ */
        .stTabs [data-baseweb="tab-list"] {
            gap: 10px;
            background-color: rgba(255, 255, 255, 0.05);
            padding: 10px;
            border-radius: 20px;
        }

        .stTabs [data-baseweb="tab"] {
            height: 50px;
            white-space: pre-wrap;
            background-color: transparent;
            border-radius: 15px;
            color: #FF85A1 !important;
            font-weight: 600;
        }

        .stTabs [aria-selected="true"] {
            background: linear-gradient(90deg, #FF007A, #9000FF) !important;
            color: white !important;
        }

        /* Sidebar สไตล์ลูกคุณหนู */
        [data-testid="stSidebar"] {
            background-color: #000000 !important;
            border-right: 2px solid #FF007A;
        }

        /* กล่องอัปโหลด */
        [data-testid="stFileUploadDropzone"] {
            border: 2px dashed #FF007A !important;
            background: rgba(255, 0, 122, 0.05) !important;
            border-radius: 30px !important;
        }
        
        /* แถบสรุปสวยๆ */
        .stAlert {
            border-radius: 20px !important;
            background: rgba(255, 255, 255, 0.1) !important;
            border: 1px solid #FF007A !important;
        }
        </style>
    """, unsafe_allow_html=True)

sassy_css()

st.markdown("<h1>Queen Logistics Center 💅</h1>", unsafe_allow_html=True)

# --- SIDEBAR อวยยศ ---
with st.sidebar:
    st.markdown("### ✨ มุมสวยของพี่")
    theme_color = st.color_picker("จิ้มสีที่ใช่ (แต่สีชมพูคือที่สุด)", "#FF007A")
    st.markdown("---")
    st.info("💡 **คำแนะนำจากตัวแม่:** อัปโหลดไฟล์ที่เริ่ดที่สุดของคุณพี่ลงมาเลยค่ะ ระบบจะจัดการให้สวยสับแบบสับละเอียด!")

# --- SESSION STATE ---
if 'order_box' not in st.session_state: st.session_state.order_box = []
if 'order_total' not in st.session_state: st.session_state.order_total = []

tab_upload, tab_setting, tab_process = st.tabs(["💅 อัปโหลดไฟล์ (ส่งมาสิคะ)", "↕️ ลำดับสินค้า (จัดให้สวย)", "🚀 ประมวลผล (เริ่มเลอ!)"])

with tab_upload:
    file = st.file_uploader("โยนไฟล์ Excel มาให้ไวเลยค่ะคุณพี่", type=["xlsx"])
    if file:
        st.success("กรี๊ด! ไฟล์เข้าแล้วค่ะ สวยมาก!")

if file:
    try:
        # --- Logic หลังบ้าน (เหมือนเดิมทุกประการเพื่อความนิ่ง) ---
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
            fixed_top = ["ปูอัด", "ปูอัดชีส", "หอยเชลล์โฮตาเตะญี่ปุ่น(NW100%)", "ปลาดอลลี่ NW 70% (200-400)", "ชีสมอสซาเรลล่า", "คิมมาริ", "น้ำจิ้มพอนสึ ยูสุ (ถุง 2 ก.ก.)", "น้ำจิ้มสุกี้"]
            
            if not st.session_state.order_box: 
                box_items = [p for p in original_order if not any(kw in p for kw in meat_kw)]
                sorted_box = [p for p in fixed_top if p in box_items] + [p for p in box_items if p not in fixed_top]
                st.session_state.order_box = sorted_box
            if not st.session_state.order_total: st.session_state.order_total = original_order

            with tab_setting:
                st.info("💅 **เลือกจัดลำดับความปัง** ลากวางได้เลยค่ะ สวยๆ")
                c1, c2 = st.columns(2)
                with c1: 
                    st.markdown("✨ **ป้ายกล่อง (ตัวแม่เรียงเอง)**")
                    st.session_state.order_box = sort_items(st.session_state.order_box, key="box")
                with c2: 
                    st.markdown("📋 **รายงานสรุป (เริ่ดๆ)**")
                    st.session_state.order_total = sort_items(st.session_state.order_total, key="total")

            with tab_process:
                st.write("ถ้าคุณพี่พร้อมแล้ว กดปุ่มข้างล่างเพื่อรับความจึ้งได้เลยค่ะ!")
                if st.button("🌟 เสกไฟล์เดี๋ยวนี้! (PREVIEW)"):
                    m_weight = full_df[full_df['Product'].str.contains('|'.join(meat_kw), na=False)].pivot_table(index=['TRIP', 'STORE NAME'], columns='Product', values='Qty', aggfunc='sum').fillna(0).reset_index()
                    m_box = full_df[~full_df['Product'].str.contains('|'.join(meat_kw), na=False)].pivot_table(index=['TRIP', 'STORE NAME'], columns='Product', values='Qty', aggfunc='sum').fillna(0).reset_index()
                    
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

                        # --- 1. ป้ายน้ำหนัก (ย่อขนาดตามสั่ง) ---
                        ws1 = wb.add_worksheet("ป้ายน้ำหนัก")
                        ws1.set_landscape(); ws1.set_margins(0.2, 0.2, 0.2, 0.2)
                        f_bnn = wb.add_format({'bold':True, 'size':30, 'border':2, 'align':'center', 'valign':'vcenter', 'bg_color':header_bg})
                        f_trip_v = wb.add_format({'bold':True, 'size':32, 'border':2, 'align':'center', 'valign':'vcenter'})
                        f_unit_v = wb.add_format({'bold':True, 'size':18, 'border':1, 'align':'center', 'valign':'vcenter'})
                        f_prod_v = wb.add_format({'bold':True, 'size':22, 'border':1, 'valign':'vcenter', 'indent':1})
                        f_store_v = wb.add_format({'bold':True, 'size':24, 'border':1, 'align':'center', 'valign':'vcenter'})
                        ws1.set_column('A:A', 38); ws1.set_column('B:E', 16)
                        fixed_meat_list = ["เนื้อสันคอ", "เนื้อออส", "หมูสันคอ", "หมูสามชั้น", "หมูสันนอก", "หมูคูโรบุตะ"]
                        row_idx = 0; breaks_w = []
                        for _, row_s in m_weight[['TRIP', 'STORE NAME']].iterrows():
                            ws1.merge_range(row_idx, 0, row_idx, 2, label_title, f_bnn)
                            ws1.merge_range(row_idx, 3, row_idx, 4, row_s['TRIP'], f_trip_v)
                            ws1.set_row(row_idx, 65)
                            ws1.write(row_idx + 1, 0, "STORE:", f_unit_v)
                            ws1.merge_range(row_idx + 1, 1, row_idx + 1, 4, row_s['STORE NAME'], f_store_v)
                            ws1.set_row(row_idx + 1, 55)
                            for i, item in enumerate(fixed_meat_list):
                                r = row_idx + 2 + i
                                ws1.write(r, 0, item, f_prod_v); ws1.write(r, 1, "", f_unit_v); ws1.write(r, 2, "KG.", f_unit_v); ws1.write(r, 3, "", f_unit_v)
                                unit_label = "กล่อง" if item in ["เนื้อออส", "หมูคูโรบุตะ"] else "ตะกร้า"
                                ws1.write(r, 4, unit_label, f_unit_v)
                                ws1.set_row(r, 62)
                            row_idx += 9; breaks_w.append(row_idx)
                        ws1.set_h_pagebreaks(breaks_w)

                        # --- 2. ป้ายกล่อง ---
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

                        # --- 3. น้ำหนัก (ชีทสรุป) ---
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
                        
                        total_row_idx = len(m_weight_reset) + 2
                        ws3.write(total_row_idx, 2, "TOTAL", s_f)
                        d_idx = 3
                        for p in fixed_meat_list:
                            val = m_weight[p].sum() if p in m_weight.columns else 0
                            if val == 0:
                                raw_name = next((k for k, v in meat_mapping.items() if v == p), None)
                                if raw_name: val = m_weight[raw_name].sum()
                            ws3.write(total_row_idx, d_idx, val, s_f); ws3.write(total_row_idx, d_idx+1, "", s_f); d_idx += 2
                        ws3.set_column('B:C', 25); ws3.set_column('D:ZZ', 12)

                        # --- 4. จัดกล่อง ---
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

                    st.balloons()
                    st.download_button(label="💖 ดาวน์โหลดไฟล์ความปังได้ที่นี่ค่ะ 💖", data=output.getvalue(), file_name=f"Queen_Report_{datetime.now().strftime('%Y-%m-%d')}.xlsx")
    except Exception as e:
        st.error(f"อุ๊ย! มีข้อผิดพลาดนิดหน่อยค่ะคุณพี่: {e}")