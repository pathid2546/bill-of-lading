import streamlit as st
import pandas as pd
import io

# --- UI CONFIGURATION ---
st.set_page_config(page_title="Project น้องเดียร์แปลงบิล v4.0", layout="wide")

# --- CUSTOM CSS ---
def local_css(main_color, font_family):
    st.markdown(f"""
        <style>
        @import url('https://fonts.googleapis.com/css2?family={font_family.replace(" ", "+")}:wght@300;400;600&display=swap');
        html, body, [class*="css"], .main {{
            background-color: #0F1117;
            color: #E0E0E0 !important;
            font-family: '{font_family}', sans-serif;
        }}
        [data-testid="stSidebar"] {{ background-color: #1A1C24; border-right: 2px solid {main_color}; }}
        h1 {{ color: {main_color} !important; text-align: center; text-shadow: 2px 2px 10px {main_color}44; }}
        div.stButton > button {{
            background: linear-gradient(135deg, {main_color} 0%, #FF85A1 100%);
            color: white !important; border-radius: 12px; font-weight: bold; height: 55px; width: 100%;
            transition: all 0.3s; box-shadow: 0 4px 15px {main_color}66;
        }}
        </style>
    """, unsafe_allow_html=True)

# --- SIDEBAR SETTINGS ---
st.sidebar.header("🎨 Appearance")
theme_color = st.sidebar.color_picker("เลือกธีมสี", "#FF4B8B")
font_choice = st.sidebar.selectbox("เลือกฟอนต์", ["Kanit", "Mitr", "Sarabun", "Roboto"])
local_css(theme_color, font_choice)

st.title(f"💖 Project น้องเดียร์แปลงบิล v4.0")
st.info("คำแนะนำ: อัปโหลดไฟล์ก่อน แล้วค่อยจัดลำดับสินค้าที่ Sidebar ด้านซ้ายนะคะ")

# --- FILE UPLOAD ---
file = st.file_uploader("📥 อัปโหลดไฟล์ใบเบิกสินค้า (Raw Data)", type=["xlsx", "csv"])

if file:
    try:
        # 1. อ่านข้อมูลเบื้องต้นเพื่อหา Header และรายชื่อสินค้า
        raw_df = pd.read_csv(file, header=None) if file.name.endswith('.csv') else pd.read_excel(file, header=None)
        header_row_idx = next((i for i, r in raw_df.iterrows() if r.astype(str).str.contains('Description', na=False).any()), None)
        
        if header_row_idx is not None:
            # เตรียมข้อมูล Clean
            trip_codes_row = raw_df.iloc[header_row_idx + 1]
            df_clean = raw_df.iloc[header_row_idx:].copy()
            df_clean.columns = df_clean.iloc[0]; df_clean = df_clean.iloc[1:].reset_index(drop=True)
            df_clean.columns = [str(c).strip() for c in df_clean.columns]
            store_cols = [c for c in df_clean.columns[4:] if "Unnamed" not in c]

            # วน Loop เก็บข้อมูล Long Format เพื่อหาชื่อสินค้าทั้งหมด
            all_rows = []
            for _, row in df_clean.iterrows():
                product = str(row.get('Description', '')).strip()
                if product in ['', 'nan', '0', '0.0'] or 'Description' in product: continue
                for col in store_cols:
                    try:
                        qty = float(row[col])
                        if qty > 0:
                            all_rows.append({'TRIP': str(trip_codes_row[df_clean.columns.get_loc(col)]).strip(), 
                                             'STORE NAME': col, 'Product': product, 'Qty': qty})
                    except: continue
            
            full_df = pd.DataFrame(all_rows)
            meat_kw = ['เนื้อ', 'หมู', 'Meat', 'Pork']
            
            # แยกรายการสินค้าสำหรับ UI Setting
            box_products = sorted(full_df[~full_df['Product'].str.contains('|'.join(meat_kw), na=False)]['Product'].unique())
            all_products = sorted(full_df['Product'].unique())

            # --- ⚙️ UI จัดลำดับสินค้า (Sidebar) ---
            st.sidebar.markdown("---")
            st.sidebar.header("⚙️ Product Sequence")
            
            with st.sidebar.expander("📦 จัดลำดับชีท: จัดกล่อง"):
                sort_box = st.multiselect("ลากวางหรือเลือกสินค้าตามลำดับ", options=box_products, default=box_products)
            
            with st.sidebar.expander("📝 จัดลำดับชีท: Order"):
                sort_order = st.multiselect("ลากวางหรือเลือกสินค้าตามลำดับ", options=all_products, default=all_products)

            # --- ประมวลผล ---
            if st.button("🚀 ประมวลผลและสร้างไฟล์ Final"):
                # สร้าง Matrix พื้นฐาน
                m_weight = full_df[full_df['Product'].str.contains('|'.join(meat_kw), na=False)].pivot_table(index=['TRIP', 'STORE NAME'], columns='Product', values='Qty', aggfunc='sum').fillna(0).reset_index()
                m_box = full_df[~full_df['Product'].str.contains('|'.join(meat_kw), na=False)].pivot_table(index=['TRIP', 'STORE NAME'], columns='Product', values='Qty', aggfunc='sum').fillna(0).reset_index()
                m_order = full_df.pivot_table(index=['TRIP', 'STORE NAME'], columns='Product', values='Qty', aggfunc='sum').fillna(0).reset_index()

                # Re-order Columns ตามที่ User เลือก
                if sort_box:
                    m_box = m_box[['TRIP', 'STORE NAME'] + [p for p in sort_box if p in m_box.columns]]
                if sort_order:
                    m_order = m_order[['TRIP', 'STORE NAME'] + [p for p in sort_order if p in m_order.columns]]

                # --- สร้างไฟล์ Excel ---
                output = io.BytesIO()
                with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                    wb = writer.book
                    h_fmt = wb.add_format({'bold': True, 'align': 'center', 'valign': 'vcenter', 'bg_color': theme_color, 'font_color': 'white', 'border': 1, 'text_wrap': True})
                    d_fmt = wb.add_format({'border': 1, 'align': 'center'})
                    sum_fmt = wb.add_format({'bold': True, 'bg_color': '#D9EAD3', 'border': 1, 'num_format': '#,##0'})

                    # ชีท 1: น้ำหนัก (เหมือนเดิม)
                    ws1 = wb.add_worksheet("น้ำหนัก")
                    ws1.merge_range(0,0,1,0,"No.",h_fmt); ws1.merge_range(0,1,1,1,"TRIP",h_fmt); ws1.merge_range(0,2,1,2,"STORE NAME",h_fmt)
                    prods_w = [p for p in m_weight.columns if p not in ['TRIP', 'STORE NAME']]
                    c_ptr = 3
                    for p in prods_w:
                        ws1.write(0, c_ptr, "จำนวนสั่ง", h_fmt); ws1.write(1, c_ptr, p, h_fmt)
                        ws1.merge_range(0, c_ptr+1, 1, c_ptr+1, "จ่ายจริง", h_fmt); c_ptr += 2
                    for i, row in m_weight.iterrows():
                        r = i+2; ws1.write(r,0,i+1,d_fmt); ws1.write(r,1,row['TRIP'],d_fmt); ws1.write(r,2,row['STORE NAME'],d_fmt)
                        d_ptr = 3
                        for p in prods_w:
                            ws1.write(r, d_ptr, row[p], d_fmt); ws1.write(r, d_ptr+1, "", d_fmt); d_ptr += 2

                    # ชีท 2: จัดกล่อง (ใช้ลำดับใหม่)
                    ws2 = wb.add_worksheet("จัดกล่อง")
                    ws2.write(0,0,"No.",h_fmt); ws2.write(0,1,"TRIP",h_fmt); ws2.write(0,2,"STORE NAME",h_fmt)
                    prods_b = [p for p in m_box.columns if p not in ['TRIP', 'STORE NAME']]
                    for idx, p in enumerate(prods_b): ws2.write(0, idx+3, p, h_fmt)
                    s_col = len(prods_b)+3; ws2.write(0, s_col, "รวมจำนวน", h_fmt)
                    for i, row in m_box.iterrows():
                        r = i+1; ws2.write(r,0,i+1,d_fmt); ws2.write(r,1,row['TRIP'],d_fmt); ws2.write(r,2,row['STORE NAME'],d_fmt)
                        for idx, p in enumerate(prods_b): ws2.write(r, idx+3, row[p], d_fmt)
                        ws2.write(r, s_col, sum(row[p] for p in prods_b), sum_fmt)
                    l_r = len(m_box)+1; ws2.write(l_r, 2, "TOTAL", sum_fmt)
                    for idx, p in enumerate(prods_b): ws2.write(l_r, idx+3, m_box[p].sum(), sum_fmt)
                    ws2.write(l_r, s_col, m_box[prods_b].sum().sum(), sum_fmt)

                    # ชีท 3: Order (ใช้ลำดับใหม่)
                    ws3 = wb.add_worksheet("Order")
                    ws3.write(0, 0, "No.", h_fmt); ws3.write(0, 1, "TRIP", h_fmt); ws3.write(0, 2, "STORE NAME", h_fmt)
                    prods_o = [p for p in m_order.columns if p not in ['TRIP', 'STORE NAME']]
                    for idx, p in enumerate(prods_o): ws3.write(0, idx+3, p, h_fmt)
                    for i, row in m_order.iterrows():
                        r = i+1; ws3.write(r,0,i+1,d_fmt); ws3.write(r,1,row['TRIP'],d_fmt); ws3.write(r,2,row['STORE NAME'],d_fmt)
                        for idx, p in enumerate(prods_o): ws3.write(r, idx+3, row[p], d_fmt)
                    
                    for ws in [ws1, ws2, ws3]: ws.set_column('C:C', 35)

                st.balloons()
                st.success(f"✅ เรียงลำดับตามใจพี่เดียร์เรียบร้อยแล้วค่ะ!")
                st.download_button(label="📥 ดาวน์โหลดไฟล์ Final", data=output.getvalue(), file_name="BNN_น้องเดียร์_CustomOrder.xlsx")

    except Exception as e:
        st.error(f"❌ เกิดข้อผิดพลาด: {e}")