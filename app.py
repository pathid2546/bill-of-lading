import streamlit as st
import pandas as pd
import io
from streamlit_sortables import sort_items

# --- UI CONFIGURATION ---
st.set_page_config(page_title="Project น้องเดียร์แปลงบิล v9.0", layout="wide")

def local_css(main_color, font_family):
    st.markdown(f"""
        <style>
        @import url('https://fonts.googleapis.com/css2?family={font_family.replace(" ", "+")}:wght@300;400;600&display=swap');
        html, body, [class*="css"], .main {{ background-color: #0F1117; color: #E0E0E0 !important; font-family: '{font_family}', sans-serif; }}
        h1 {{ color: {main_color} !important; text-align: center; text-shadow: 2px 2px 10px {main_color}44; }}
        .stTabs [aria-selected="true"] {{ background-color: {main_color} !important; color: white !important; border-radius: 8px; }}
        div.stButton > button {{
            background: linear-gradient(135deg, {main_color} 0%, #FF85A1 100%);
            color: white !important; border-radius: 12px; font-weight: bold; height: 60px; width: 100%;
        }}
        .st-sortable-item {{ background-color: #1A1C24 !important; border: 1px solid #444 !important; color: white !important; }}
        </style>
    """, unsafe_allow_html=True)

theme_color = st.sidebar.color_picker("ธีมสีหลัก", "#FF4B8B")
font_choice = st.sidebar.selectbox("เลือกฟอนต์", ["Kanit", "Mitr", "Sarabun"])
local_css(theme_color, font_choice)

st.title(f"💖 Project น้องเดียร์แปลงบิล v9.0")
st.caption("ระบบตรวจสอบ Trip No. จากชีท Route อัตโนมัติด้วย Store Code ค่ะ")

# --- SESSION STATE ---
if 'order_box' not in st.session_state: st.session_state.order_box = []
if 'order_total' not in st.session_state: st.session_state.order_total = []
if 'last_file' not in st.session_state: st.session_state.last_file = None

tab_upload, tab_setting, tab_process = st.tabs(["📥 1. อัปโหลดไฟล์", "↕️ 2. ลากวางลำดับสินค้า", "🚀 3. ประมวลผล"])

with tab_upload:
    file = st.file_uploader("อัปโหลดไฟล์ Raw Data (ที่มีชีท Route)", type=["xlsx"])
    if file and file != st.session_state.last_file:
        st.session_state.order_box = []
        st.session_state.order_total = []
        st.session_state.last_file = file
        st.success("อัปโหลดสำเร็จ! ตรวจพบไฟล์และพร้อมดึงข้อมูลจากชีท Route ค่ะ")

if file:
    try:
        # 1. อ่านชีท Route เพื่อทำ Mapping Dictionary
        route_df = pd.read_excel(file, sheet_name='Route')
        # คลีนชื่อ Column กันพลาด
        route_df.columns = [str(c).strip().upper() for c in route_df.columns]
        
        # ค้นหา Column ที่ต้องการ (ใช้ Keywords เพราะบางทีชื่ออาจมีเว้นวรรค)
        code_col = next((c for c in route_df.columns if 'STORE CODE' in c), None)
        trip_col = next((c for c in route_df.columns if 'TRIP NO' in c), None)
        
        if code_col and trip_col:
            # สร้าง Dictionary: { 'LT-PLK': 'FZ-007', ... }
            route_map = dict(zip(route_df[code_col].astype(str).str.strip(), 
                                 route_df[trip_col].astype(str).str.strip()))
            st.sidebar.success(f"🔗 พบฐานข้อมูล Route {len(route_map)} สาขา")
        else:
            st.error("❌ ไม่พบ Column 'STORE CODE' หรือ 'TRIP NO.' ในชีท Route")
            st.stop()

        # 2. อ่านชีทหลัก (Order/หน้าแรก)
        all_sheets = pd.ExcelFile(file).sheet_names
        main_sheet_name = all_sheets[0] # สมมติว่าหน้าแรกคือหน้า Order
        raw_df = pd.read_excel(file, sheet_name=main_sheet_name, header=None)

        header_row_idx = next((i for i, r in raw_df.iterrows() if r.astype(str).str.contains('Description', na=False).any()), None)
        
        if header_row_idx is not None:
            # ค้นหา Column Store Code ในหน้าหลัก (ปกติคือ Column A หรือ index 0)
            df_clean = raw_df.iloc[header_row_idx:].copy()
            df_clean.columns = df_clean.iloc[0]; df_clean = df_clean.iloc[1:].reset_index(drop=True)
            df_clean.columns = [str(c).strip() for c in df_clean.columns]
            
            # ดึงรายชื่อหัวร้านค้า (Column C เป็นต้นไป)
            store_cols = [c for c in df_clean.columns[4:] if "Unnamed" not in c]

            all_rows = []
            original_product_order = []

            for _, row in df_clean.iterrows():
                product = str(row.get('Description', '')).strip()
                if product in ['', 'nan', '0', '0.0'] or 'Description' in product: continue
                if product not in original_product_order: original_product_order.append(product)

                for col in store_cols:
                    try:
                        qty = float(row[col])
                        if qty > 0:
                            # --- ⚡ LOGIC MAPPING TRIP ⚡ ---
                            # ค้นหา Store Code ของร้านนี้ (col คือ Store Name)
                            # เราต้องหา Store Code ที่ตรงกับ Store Name นี้จากชีท Route
                            store_code_info = route_df[route_df['STORE NAME'].str.strip() == col.strip()]
                            
                            if not store_code_info.empty:
                                mapped_trip = str(store_code_info.iloc[0][trip_col]).strip()
                            else:
                                mapped_trip = "ไม่พบใน Route"
                            
                            all_rows.append({
                                'TRIP': mapped_trip, 
                                'STORE NAME': col, 
                                'Product': product, 
                                'Qty': qty
                            })
                    except: continue
            
            full_df = pd.DataFrame(all_rows)
            meat_kw = ['เนื้อ', 'หมู', 'Meat', 'Pork']
            
            initial_box = [p for p in original_product_order if not any(kw in p for kw in meat_kw)]
            initial_total = original_product_order

            if not st.session_state.order_box: st.session_state.order_box = initial_box
            if not st.session_state.order_total: st.session_state.order_total = initial_total

            with tab_setting:
                st.subheader("↕️ ลากสลับลำดับสินค้า")
                c1, c2 = st.columns(2)
                with c1: st.session_state.order_box = sort_items(st.session_state.order_box, key="b")
                with c2: st.session_state.order_total = sort_items(st.session_state.order_total, key="o")

            with tab_process:
                if st.button("🚀 ประมวลผลและสร้างไฟล์ Final"):
                    # สร้าง Matrix
                    m_box = full_df[~full_df['Product'].str.contains('|'.join(meat_kw), na=False)].pivot_table(index=['TRIP', 'STORE NAME'], columns='Product', values='Qty', aggfunc='sum').fillna(0).reset_index()
                    m_order = full_df.pivot_table(index=['TRIP', 'STORE NAME'], columns='Product', values='Qty', aggfunc='sum').fillna(0).reset_index()

                    # เรียง Column
                    m_box = m_box[['TRIP', 'STORE NAME'] + [p for p in st.session_state.order_box if p in m_box.columns]]
                    m_order = m_order[['TRIP', 'STORE NAME'] + [p for p in st.session_state.order_total if p in m_order.columns]]
                    
                    # Sort แถวตามทริปเพื่อให้ดูง่าย
                    m_box = m_box.sort_values(['TRIP', 'STORE NAME'])
                    m_order = m_order.sort_values(['TRIP', 'STORE NAME'])

                    output = io.BytesIO()
                    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                        wb = writer.book
                        h_fmt = wb.add_format({'bold': True, 'align': 'center', 'bg_color': theme_color, 'font_color': 'white', 'border': 1})
                        d_fmt = wb.add_format({'border': 1, 'align': 'center'})
                        
                        # --- เขียนชีท (จัดกล่อง / Order) ---
                        for sheet_name, data in zip(["จัดกล่อง", "Order"], [m_box, m_order]):
                            ws = wb.add_worksheet(sheet_name)
                            cols = data.columns.tolist()
                            for idx, col in enumerate(cols):
                                ws.write(0, idx, col, h_fmt)
                                for r_idx, val in enumerate(data[col]):
                                    ws.write(r_idx+1, idx, val, d_fmt)
                            ws.set_column('B:B', 30)

                    st.balloons()
                    st.download_button("📥 ดาวน์โหลดไฟล์", output.getvalue(), "BNN_Final_With_Route.xlsx")

    except Exception as e:
        st.error(f"❌ Error: {e}")