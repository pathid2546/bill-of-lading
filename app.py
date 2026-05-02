import streamlit as st
import pandas as pd
import io
from datetime import datetime
from streamlit_sortables import sort_items

# --- UI CONFIGURATION ---
st.set_page_config(page_title="BNN Smart Logistics System", layout="wide")

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
        .stTabs [aria-selected="true"] {{ background-color: {main_color} !important; color: white !important; border-radius: 8px; }}
        div.stButton > button {{
            background: linear-gradient(135deg, {main_color} 0%, #FF85A1 100%);
            color: white !important; border-radius: 12px; font-weight: bold; height: 60px; width: 100%;
            border: none; transition: 0.3s;
        }}
        div.stButton > button:hover {{ transform: scale(1.02); box-shadow: 0 10px 20px {main_color}44; }}
        </style>
    """, unsafe_allow_html=True)

# Sidebar settings
theme_color = st.sidebar.color_picker("Customize Theme Color", "#FF4B8B")
font_choice = st.sidebar.selectbox("Select Display Font", ["Kanit", "Mitr", "Sarabun"])
local_css(theme_color, font_choice)

st.markdown("<h1>BNN Smart Logistics System</h1>", unsafe_allow_html=True)

# --- SESSION STATE ---
if 'order_box' not in st.session_state: st.session_state.order_box = []
if 'order_total' not in st.session_state: st.session_state.order_total = []

tab_upload, tab_setting, tab_process = st.tabs(["📥 อัปโหลดข้อมูล", "↕️ จัดลำดับสินค้า", "🚀 ประมวลผลและดาวน์โหลด"])

if file := st.file_uploader("ลากไฟล์ Excel มาวางที่นี่", type=["xlsx"]):
    try:
        # Data Processing Logic (Core)
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
                st.info("💡 ลากวางเพื่อกำหนดลำดับสินค้าที่จะปรากฏในไฟล์ Excel")
                c1, c2 = st.columns(2)
                with c1: 
                    st.markdown("📦 **ลำดับป้ายกล่อง (ของแห้ง)**")
                    st.session_state.order_box = sort_items(st.session_state.order_box, key="box")
                with c2: 
                    st.markdown("📋 **ลำดับรายงานสรุป (ทั้งหมด)**")
                    st.session_state.order_total = sort_items(st.session_state.order_total, key="total")

            with tab_process:
                if st.button("Generate Final Documents"):
                    m_weight = full_df[full_df['Product'].str.contains('|'.join(meat_kw), na=False)].pivot_table(index=['TRIP', 'STORE NAME'], columns='Product', values='Qty', aggfunc='sum').fillna(0).reset_index()
                    m_box = full_df[~full_df['Product'].str.contains('|'.join(meat_kw), na=False)].pivot_table(index=['TRIP', 'STORE NAME'], columns='Product', values='Qty', aggfunc='sum').fillna(0).reset_index()
                    m_order = full_df.pivot_table(index=['TRIP', 'STORE NAME'], columns='Product', values='Qty', aggfunc='sum').fillna(0).reset_index()
                    
                    prods_box_list = [p for p in st.session_state.order_box if p in m_box.columns]
                    m_box = m_box[['TRIP', 'STORE NAME'] + prods_box_list].sort_values(['TRIP', 'STORE NAME'])
                    m_box['รวมจำนวน'] = m_box[prods_box_list].sum(axis=1)

                    output = io.BytesIO()
                    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                        wb = writer.book
                        
                        # Style Formats
                        header_bg = '#F2F2F2'
                        h_f = wb.add_format({'bold':True, 'align':'center', 'valign':'vcenter', 'bg_color':header_bg, 'border':1, 'text_wrap':True})
                        d_f = wb.add_format({'border':1, 'align':'center'})
                        s_f = wb.add_format({'bold':True, 'bg_color':'#E9E9E9', 'border':1, 'num_format':'#,##0'})

                        # 1. ป้ายน้ำหนัก
                        ws_tag_w = wb.add_worksheet("ป้ายน้ำหนัก")
                        ws_tag_w.set_landscape(); ws_tag_w.set_margins(0.2, 0.2, 0.2, 0.2); ws_tag_w.fit_to_pages(1, 0)
                        f_bnn = wb.add_format({'bold':True, 'size':36, 'border':2, 'align':'center', 'valign':'vcenter', 'bg_color':header_bg})
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
                                ws_tag_w.write(r, 0, item, f_prod_v); ws_tag_w.write(r, 1, "", d_f); ws_tag_w.write(r, 2, "KG.", f_unit_v)
                                ws_tag_w.write(r, 3, "", d_f); ws_tag_w.write(r, 4, "ตะกร้า", f_unit_v); ws_tag_w.set_row(r, 75)
                            row_idx += 8; breaks_w.append(row_idx)
                        ws_tag_w.set_h_pagebreaks(breaks_w)

                        # 2. ป้ายกล่อง
                        ws_tag_b = wb.add_worksheet("ป้ายกล่อง")
                        ws_tag_b.set_landscape(); ws_tag_b.set_margins(0.2, 0.2, 0.2, 0.2); ws_tag_b.fit_to_pages(1, 0)
                        f_bnn_big = wb.add_format({'bold':True, 'size':60, 'border':2, 'align':'center', 'valign':'vcenter', 'bg_color':header_bg})
                        f_store_big = wb.add_format({'bold':True, 'size':35, 'border':1, 'align':'center', 'valign':'vcenter', 'text_wrap':True})
                        f_qty_big = wb.add_format({'bold':True, 'size':80, 'border':1, 'align':'center', 'valign':'vcenter'})
                        f_label_big = wb.add_format({'bold':True, 'size':40, 'border':1, 'align':'center', 'valign':'vcenter'})
                        f_trip_big = wb.add_format({'bold':True, 'size':70, 'border':1, 'align':'center', 'valign':'vcenter'})
                        ws_tag_b.set_column('A:A', 50); ws_tag_b.set_column('B:B', 60)
                        b_row = 0; breaks_b = []
                        for _, row_b in m_box.iterrows():
                            ws_tag_b.merge_range(b_row, 0, b_row, 1, "BNN (สุกี้ตี๋น้อย)", f_bnn_big); ws_tag_b.set_row(b_row, 120)
                            ws_tag_b.write(b_row+1, 0, "STORE NAME", f_label_big); ws_tag_b.write(b_row+1, 1, row_b['STORE NAME'], f_store_big); ws_tag_b.set_row(b_row+1, 100)
                            ws_tag_b.write(b_row+2, 0, "จำนวนกล่อง", f_label_big); ws_tag_b.write(b_row+2, 1, row_b['รวมจำนวน'], f_qty_big); ws_tag_b.set_row(b_row+2, 130)
                            ws_tag_b.write(b_row+3, 0, "TRIP NO.", f_label_big); ws_tag_b.write(b_row+3, 1, row_b['TRIP'], f_trip_big); ws_tag_b.set_row(b_row+3, 120)
                            b_row += 4; breaks_b.append(b_row)
                        ws_tag_b.set_h_pagebreaks(breaks_b)

                        # 3. ตารางรายงาน
                        sheets_data = {"น้ำหนัก": m_weight, "จัดกล่อง": m_box, "Order": m_order}
                        for name, df_obj in sheets_data.items():
                            ws = wb.add_worksheet(name)
                            if name == "น้ำหนัก":
                                ws1_cols = [p for p in original_order if p in df_obj.columns and p not in ['TRIP', 'STORE NAME']]
                                ws.merge_range(0,0,1,0,"No.",h_f); ws.merge_range(0,1,1,1,"TRIP",h_f); ws.merge_range(0,2,1,2,"STORE NAME",h_f)
                                c_idx = 3
                                for p in ws1_cols:
                                    ws.write(0, c_idx, "จำนวนสั่ง", h_f); ws.write(1, c_idx, p, h_f); ws.merge_range(0, c_idx+1, 1, c_idx+1, "จ่ายจริง", h_f); c_idx += 2
                                for i, row in df_obj.reset_index(drop=True).iterrows():
                                    r = i+2; ws.write(r,0,i+1,d_f); ws.write(r,1,row['TRIP'],d_f); ws.write(r,2,row['STORE NAME'],d_f)
                                    d_idx = 3
                                    for p in ws1_cols: ws.write(r, d_idx, row[p], d_f); ws.write(r, d_idx+1, "", d_f); d_idx += 2
                            else:
                                for idx, col in enumerate(df_obj.columns): ws.write(0, idx, col, h_f)
                                for i, row in df_obj.reset_index(drop=True).iterrows():
                                    for idx, val in enumerate(row): ws.write(i+1, idx, val, d_f if idx < len(row)-1 else s_f)
                            ws.set_column('B:C', 25); ws.set_column('D:ZZ', 12)

                    # Create filename with current date
                    today_str = datetime.now().strftime("%Y-%m-%d")
                    final_filename = f"BNN_Logistics_Report_{today_str}.xlsx"

                    st.balloons()
                    st.download_button(
                        label=f"📥 ดาวน์โหลดไฟล์: {final_filename}",
                        data=output.getvalue(),
                        file_name=final_filename,
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                    )

    except Exception as e:
        st.error(f"⚠️ เกิดข้อผิดพลาดในการประมวลผล: {e}")