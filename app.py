import streamlit as st
import pandas as pd
import io

# --- UI CONFIGURATION ---
st.set_page_config(page_title="Project น้องเดียร์แปลงบิล v6.0", layout="wide")

def local_css(main_color, font_family):
    st.markdown(f"""
        <style>
        @import url('https://fonts.googleapis.com/css2?family={font_family.replace(" ", "+")}:wght@300;400;600&display=swap');
        html, body, [class*="css"], .main {{ background-color: #0F1117; color: #E0E0E0 !important; font-family: '{font_family}', sans-serif; }}
        h1 {{ color: {main_color} !important; text-align: center; text-shadow: 2px 2px 10px {main_color}44; }}
        .stTabs [data-baseweb="tab-list"] {{ gap: 24px; }}
        .stTabs [aria-selected="true"] {{ background-color: {main_color} !important; color: white !important; border-radius: 8px; }}
        div.stButton > button {{
            background: linear-gradient(135deg, {main_color} 0%, #FF85A1 100%);
            color: white !important; border-radius: 12px; font-weight: bold; height: 60px; width: 100%; font-size: 20px;
        }}
        </style>
    """, unsafe_allow_html=True)

# --- SETTINGS ---
theme_color = st.sidebar.color_picker("ธีมสีหลัก", "#FF4B8B")
font_choice = st.sidebar.selectbox("เลือกฟอนต์", ["Kanit", "Mitr", "Sarabun"])
local_css(theme_color, font_choice)

st.title(f"💖 Project น้องเดียร์แปลงบิล v6.0")

# --- SESSION STATE FOR SORTING ---
if 'df_sort_box' not in st.session_state: st.session_state.df_sort_box = None
if 'df_sort_order' not in st.session_state: st.session_state.df_sort_order = None

tab_upload, tab_setting, tab_process = st.tabs(["📥 1. อัปโหลดไฟล์", "📑 2. ตั้งค่าลำดับ (ตาราง)", "🚀 3. ประมวลผล"])

with tab_upload:
    file = st.file_uploader("อัปโหลดไฟล์ Raw Data", type=["xlsx", "csv"])
    if file:
        st.success("อัปโหลดสำเร็จ! กรุณาไปที่หน้า 'ตั้งค่าลำดับ' เพื่อตรวจสอบลำดับสินค้าค่ะ")

if file:
    try:
        # --- ประมวลผล DATA เบื้องต้น ---
        raw_df = pd.read_csv(file, header=None) if file.name.endswith('.csv') else pd.read_excel(file, header=None)
        header_row_idx = next((i for i, r in raw_df.iterrows() if r.astype(str).str.contains('Description', na=False).any()), None)
        
        if header_row_idx is not None:
            trip_codes_row = raw_df.iloc[header_row_idx + 1]
            df_clean = raw_df.iloc[header_row_idx:].copy()
            df_clean.columns = df_clean.iloc[0]; df_clean = df_clean.iloc[1:].reset_index(drop=True)
            df_clean.columns = [str(c).strip() for c in df_clean.columns]
            store_cols = [c for c in df_clean.columns[4:] if "Unnamed" not in c]

            all_rows = []
            for _, row in df_clean.iterrows():
                product = str(row.get('Description', '')).strip()
                if product in ['', 'nan', '0', '0.0'] or 'Description' in product: continue
                for col in store_cols:
                    try:
                        qty = float(row[col])
                        if qty > 0:
                            all_rows.append({
                                'TRIP': str(trip_codes_row[df_clean.columns.get_loc(col)]).strip(), 
                                'STORE NAME': col, 'Product': product, 'Qty': qty
                            })
                    except: continue
            
            full_df = pd.DataFrame(all_rows)
            meat_kw = ['เนื้อ', 'หมู', 'Meat', 'Pork']
            
            # เตรียมรายการสินค้าสำหรับตารางลำดับ
            box_prods = sorted(full_df[~full_df['Product'].str.contains('|'.join(meat_kw), na=False)]['Product'].unique())
            all_prods = sorted(full_df['Product'].unique())

            # สร้าง DataFrame สำหรับ Edit ลำดับ (ถ้ายังไม่มี)
            if st.session_state.df_sort_box is None:
                st.session_state.df_sort_box = pd.DataFrame({'ลำดับ': range(1, len(box_prods)+1), 'ชื่อสินค้า': box_prods})
            if st.session_state.df_sort_order is None:
                st.session_state.df_sort_order = pd.DataFrame({'ลำดับ': range(1, len(all_prods)+1), 'ชื่อสินค้า': all_prods})

            with tab_setting:
                st.subheader("แก้ไขลำดับโดยการพิมพ์ตัวเลขในช่อง 'ลำดับ'")
                col1, col2 = st.columns(2)
                
                with col1:
                    st.markdown("### 📦 สำหรับชีท [จัดกล่อง]")
                    # แก้ไขลำดับแบบตาราง
                    st.session_state.df_sort_box = st.data_editor(
                        st.session_state.df_sort_box,
                        column_config={"ลำดับ": st.column_config.NumberColumn(format="%d")},
                        hide_index=True, use_container_width=True, key="ed_box"
                    )
                
                with col2:
                    st.markdown("### 📝 สำหรับชีท [Order]")
                    st.session_state.df_sort_order = st.data_editor(
                        st.session_state.df_sort_order,
                        column_config={"ลำดับ": st.column_config.NumberColumn(format="%d")},
                        hide_index=True, use_container_width=True, key="ed_order"
                    )
                st.info("💡 ทริค: คลิกที่หัวตาราง 'ลำดับ' เพื่อตรวจสอบการเรียงจากน้อยไปมาก")

            with tab_process:
                if st.button("🚀 ประมวลผลและสร้างไฟล์ Final"):
                    # เตรียมลำดับที่เลือก
                    order_box = st.session_state.df_sort_box.sort_values('ลำดับ')['ชื่อสินค้า'].tolist()
                    order_total = st.session_state.df_sort_order.sort_values('ลำดับ')['ชื่อสินค้า'].tolist()

                    # Matrix Data
                    m_weight = full_df[full_df['Product'].str.contains('|'.join(meat_kw), na=False)].pivot_table(index=['TRIP', 'STORE NAME'], columns='Product', values='Qty', aggfunc='sum').fillna(0).reset_index()
                    m_box = full_df[~full_df['Product'].str.contains('|'.join(meat_kw), na=False)].pivot_table(index=['TRIP', 'STORE NAME'], columns='Product', values='Qty', aggfunc='sum').fillna(0).reset_index()
                    m_order = full_df.pivot_table(index=['TRIP', 'STORE NAME'], columns='Product', values='Qty', aggfunc='sum').fillna(0).reset_index()

                    # Re-index Columns ตามตารางที่แก้
                    m_box = m_box[['TRIP', 'STORE NAME'] + [p for p in order_box if p in m_box.columns]]
                    m_order = m_order[['TRIP', 'STORE NAME'] + [p for p in order_total if p in m_order.columns]]

                    # --- EXCEL WRITER (Logic เดิม) ---
                    output = io.BytesIO()
                    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                        wb = writer.book
                        h_fmt = wb.add_format({'bold': True, 'align': 'center', 'valign': 'vcenter', 'bg_color': theme_color, 'font_color': 'white', 'border': 1, 'text_wrap': True})
                        d_fmt = wb.add_format({'border': 1, 'align': 'center'})
                        sum_fmt = wb.add_format({'bold': True, 'bg_color': '#D9EAD3', 'border': 1, 'num_format': '#,##0'})

                        # ชีท 1: น้ำหนัก
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

                        # ชีท 2: จัดกล่อง
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

                        # ชีท 3: Order
                        ws3 = wb.add_worksheet("Order")
                        ws3.write(0, 0, "No.", h_fmt); ws3.write(0, 1, "TRIP", h_fmt); ws3.write(0, 2, "STORE NAME", h_fmt)
                        prods_o = [p for p in m_order.columns if p not in ['TRIP', 'STORE NAME']]
                        for idx, p in enumerate(prods_o): ws3.write(0, idx+3, p, h_fmt)
                        for i, row in m_order.iterrows():
                            r = i+1; ws3.write(r,0,i+1,d_fmt); ws3.write(r,1,row['TRIP'],d_fmt); ws3.write(r,2,row['STORE NAME'],d_fmt)
                            for idx, p in enumerate(prods_o): ws3.write(r, idx+3, row[p], d_fmt)
                        
                        for ws in [ws1, ws2, ws3]: ws.set_column('C:C', 35)

                    st.balloons()
                    st.download_button(label="📥 ดาวน์โหลดไฟล์ Final Click", data=output.getvalue(), file_name="BNN_Final_Sorted.xlsx")

    except Exception as e:
        st.error(f"❌ โอ๊ะ! มีข้อผิดพลาด: {e}")