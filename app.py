import streamlit as st
import pandas as pd
import io
from streamlit_sortables import sort_items

# --- UI CONFIGURATION ---
st.set_page_config(page_title="Project น้องเดียร์ v11.0", layout="wide")

st.title(f"💖 Project น้องเดียร์แปลงบิล v11.0")
st.caption("ระบบตรวจสอบรหัสจาก Route (A) เพื่อเปลี่ยน Trip (C) ให้ถูกต้องค่ะ")

# --- SESSION STATE ---
if 'order_box' not in st.session_state: st.session_state.order_box = []
if 'order_total' not in st.session_state: st.session_state.order_total = []

tab_upload, tab_setting, tab_process = st.tabs(["📥 1. อัปโหลดไฟล์", "↕️ 2. ลากวางลำดับสินค้า", "🚀 3. ประมวลผล"])

with tab_upload:
    file = st.file_uploader("อัปโหลดไฟล์ Excel (ที่มีชีท Route)", type=["xlsx"])

if file:
    try:
        # 1. อ่านชีท Route (เน้นตำแหน่ง A และ C)
        # usecols=[0, 2] คืออ่านเฉพาะ Column A และ C
        route_df = pd.read_excel(file, sheet_name='Route', header=None)
        
        # คลีนข้อมูลและทำ Dictionary สำหรับ VLOOKUP
        # Key: Column A (Index 0), Value: Column C (Index 2)
        route_lookup = {}
        for _, r in route_df.iterrows():
            code = str(r[0]).strip()
            trip = str(r[2]).strip()
            if code and code != 'nan':
                route_lookup[code] = trip

        # 2. อ่านหน้าแรก (หน้า Order)
        xls = pd.ExcelFile(file)
        main_sheet = xls.sheet_names[0]
        raw_df = pd.read_excel(file, sheet_name=main_sheet, header=None)

        # หาแถว Header (Description)
        header_idx = next((i for i, r in raw_df.iterrows() if r.astype(str).str.contains('Description', na=False).any()), None)
        
        if header_idx is not None:
            # ดึง Store Codes จากแถวที่ 2 (ถัดจาก Header) เพื่อเอาไว้แมพกับ Trip
            # สมมติว่าในหน้าหลัก Store Code เริ่มที่ Column E (Index 4) เป็นต้นไป
            store_codes_row = raw_df.iloc[header_idx + 1] 
            
            df_clean = raw_df.iloc[header_idx:].copy()
            df_clean.columns = df_clean.iloc[0]
            df_clean = df_clean.iloc[1:].reset_index(drop=True)
            
            # รายชื่อร้าน (Header)
            store_columns = [c for c in df_clean.columns[4:] if "Unnamed" not in str(c)]

            all_rows = []
            original_order = [] # ลำดับสินค้าตามไฟล์จริง

            for _, row in df_clean.iterrows():
                product = str(row.get('Description', '')).strip()
                if product in ['', 'nan', '0', '0.0'] or 'Description' in product: continue
                if product not in original_order: original_order.append(product)

                for col_name in store_columns:
                    try:
                        qty = float(row[col_name])
                        if qty > 0:
                            # --- ⚡ LOGIC MATCHING ⚡ ---
                            # 1. หาว่าร้านนี้ (col_name) อยู่ Column ไหนในหน้าหลัก
                            col_idx = list(df_clean.columns).index(col_name)
                            # 2. ไปดู Store Code ในแถวนั้น (จากแถวที่พี่บอกว่าใช้ตรวจ)
                            current_store_code = str(store_codes_row[col_idx]).strip()
                            # 3. VLOOKUP ไปที่ชีท Route (ถ้าเจอใน A ให้เอา C มาใส่)
                            final_trip = route_lookup.get(current_store_code, "ไม่พบรหัส")

                            all_rows.append({
                                'TRIP': final_trip,
                                'STORE NAME': col_name,
                                'Product': product,
                                'Qty': qty
                            })
                    except: continue

            full_df = pd.DataFrame(all_rows)
            meat_kw = ['เนื้อ', 'หมู', 'Meat', 'Pork']
            
            # เตรียมรายการให้ลากวาง (ยึดตาม Original Order)
            init_box = [p for p in original_order if not any(kw in p for kw in meat_kw)]
            init_total = original_order

            if not st.session_state.order_box: st.session_state.order_box = init_box
            if not st.session_state.order_total: st.session_state.order_total = init_total

            with tab_setting:
                st.subheader("↕️ ลากวางสลับลำดับสินค้า (อิงตามไฟล์ต้นฉบับ)")
                c1, c2 = st.columns(2)
                with c1:
                    st.markdown("### 📦 ชีทจัดกล่อง")
                    st.session_state.order_box = sort_items(st.session_state.order_box, key="box")
                with c2:
                    st.markdown("### 📝 ชีท Order")
                    st.session_state.order_total = sort_items(st.session_state.order_total, key="total")

            with tab_process:
                if st.button("🚀 ประมวลผลสร้างไฟล์ Excel"):
                    # สร้าง Matrix
                    m_box = full_df[~full_df['Product'].str.contains('|'.join(meat_kw), na=False)].pivot_table(index=['TRIP', 'STORE NAME'], columns='Product', values='Qty', aggfunc='sum').fillna(0).reset_index()
                    m_order = full_df.pivot_table(index=['TRIP', 'STORE NAME'], columns='Product', values='Qty', aggfunc='sum').fillna(0).reset_index()

                    # เรียง Column ตามใจชอบ
                    m_box = m_box[['TRIP', 'STORE NAME'] + [p for p in st.session_state.order_box if p in m_box.columns]]
                    m_order = m_order[['TRIP', 'STORE NAME'] + [p for p in st.session_state.order_total if p in m_order.columns]]

                    # สั่งเรียงแถวตามทริปที่อัปเดตใหม่
                    m_box = m_box.sort_values('TRIP')
                    m_order = m_order.sort_values('TRIP')

                    output = io.BytesIO()
                    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                        m_box.to_excel(writer, sheet_name='จัดกล่อง', index=False)
                        m_order.to_excel(writer, sheet_name='Order', index=False)
                    
                    st.balloons()
                    st.download_button("📥 ดาวน์โหลดไฟล์ Final", output.getvalue(), "BNN_Sorted_Route.xlsx")

    except Exception as e:
        st.error(f"❌ พบข้อผิดพลาด: {e}")