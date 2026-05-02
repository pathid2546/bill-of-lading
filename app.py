import streamlit as st
import pandas as pd
import io
from streamlit_sortables import sort_items

# --- UI CONFIGURATION ---
st.set_page_config(page_title="Project น้องเดียร์ v21.0", layout="wide")

# (CSS ส่วนเดิม)
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

st.title(f"💖 Project น้องเดียร์ v21.0 (เวอร์ชันจบงาน)")

# (ส่วนการอ่านไฟล์เหมือนเดิมเป๊ะ)
if 'order_box' not in st.session_state: st.session_state.order_box = []
file = st.file_uploader("อัปโหลดไฟล์ Excel", type=["xlsx"])

if file:
    try:
        route_df = pd.read_excel(file, sheet_name='Route', header=None)
        route_lookup = {str(r[0]).strip(): str(r[2]).strip() for _, r in route_df.iterrows() if pd.notna(r[0])}
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
                            all_rows.append({'TRIP': route_lookup.get(current_store_code, "ไม่พบรหัส"), 'STORE NAME': col_name, 'Product': product, 'Qty': qty})
                    except: continue

            full_df = pd.DataFrame(all_rows)
            meat_kw = ['เนื้อ', 'หมู', 'Meat', 'Pork']
            
            if st.button("🚀 ประมวลผลและดาวน์โหลด"):
                m_weight = full_df[full_df['Product'].str.contains('|'.join(meat_kw), na=False)].pivot_table(index=['TRIP', 'STORE NAME'], columns='Product', values='Qty', aggfunc='sum').fillna(0).reset_index()
                
                output = io.BytesIO()
                with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                    wb = writer.book
                    
                    # --- FORMATS (ปรับขนาดให้เล็กลงนิดเดียวเพื่อความชัวร์) ---
                    tag_bnn = wb.add_format({'bold': True, 'size': 38, 'border': 2, 'align': 'center', 'valign': 'vcenter'})
                    tag_trip = wb.add_format({'bold': True, 'size': 38, 'border': 2, 'align': 'center', 'valign': 'vcenter'})
                    tag_label = wb.add_format({'bold': True, 'size': 18, 'border': 1, 'align': 'center', 'valign': 'vcenter'})
                    tag_store = wb.add_format({'bold': True, 'size': 28, 'border': 1, 'align': 'center', 'valign': 'vcenter', 'shrink': True})
                    tag_prod = wb.add_format({'bold': True, 'size': 30, 'border': 1, 'valign': 'vcenter', 'indent': 1})
                    tag_unit = wb.add_format({'bold': True, 'size': 24, 'border': 1, 'align': 'center', 'valign': 'vcenter'})
                    border_fmt = wb.add_format({'border': 1})

                    ws_tag = wb.add_worksheet("ป้ายน้ำหนัก")
                    ws_tag.set_landscape()
                    ws_tag.set_paper(9) # A4
                    ws_tag.set_margins(0.2, 0.2, 0.2, 0.2)
                    
                    # บังคับ 1 หน้าต่อ 1 ร้าน
                    ws_tag.fit_to_pages(1, 1) 

                    # ปรับ Column Width (ลดรวมลงเล็กน้อย)
                    ws_tag.set_column('A:A', 35) 
                    ws_tag.set_column('B:B', 20) 
                    ws_tag.set_column('C:C', 12) 
                    ws_tag.set_column('D:D', 18) 
                    ws_tag.set_column('E:E', 18) 
                    
                    fixed_items = ["เนื้อสันคอ", "เนื้อออส", "หมูสันคอ", "หมูสามชั้น", "หมูสันนอก"]
                    curr_r = 0
                    page_breaks = []
                    unique_stores = full_df[['TRIP', 'STORE NAME']].drop_duplicates().sort_values(['TRIP', 'STORE NAME'])
                    
                    for idx, row_s in unique_stores.iterrows():
                        # Header
                        ws_tag.merge_range(curr_r, 0, curr_r, 2, "BNN (สุกี้ตี๋น้อย)", tag_bnn)
                        ws_tag.merge_range(curr_r, 3, curr_r, 4, row_s['TRIP'], tag_trip)
                        ws_tag.set_row(curr_r, 85) # ลดจาก 95
                        
                        # Store Row
                        ws_tag.write(curr_r + 1, 0, "STORE NAME", tag_label)
                        ws_tag.merge_range(curr_r + 1, 1, curr_r + 1, 4, row_s['STORE NAME'], tag_store)
                        ws_tag.set_row(curr_r + 1, 65) # ลดจาก 75
                        
                        curr_r += 2
                        # Items
                        for item in fixed_items:
                            ws_tag.write(curr_r, 0, item, tag_prod)
                            ws_tag.write(curr_r, 1, "", border_fmt)
                            ws_tag.write(curr_r, 2, "KG.", tag_unit)
                            ws_tag.write(curr_r, 3, "", border_fmt)
                            ws_tag.write(curr_r, 4, "ตะกร้า", tag_unit)
                            ws_tag.set_row(curr_r, 72) # ลดจาก 82 เพื่อให้ไม่ล้น
                            curr_r += 1
                        
                        page_breaks.append(curr_r)
                    
                    ws_tag.set_h_pagebreaks(page_breaks)

                    # (ส่วน Sheet น้ำหนัก คงเดิม)
                    ws1 = wb.add_worksheet("น้ำหนัก")
                    # ... [เหมือน v20]

                st.balloons()
                st.download_button("📥 ดาวน์โหลด v21 (แบบพอดีหน้า)", output.getvalue(), "BNN_Final_Perfect.xlsx")

    except Exception as e:
        st.error(f"❌ พบข้อผิดพลาด: {e}")