import streamlit as st
import pandas as pd
import io

# --- การตั้งค่า Theme แบบ Modern Dark ---
st.set_page_config(page_title="BNN Multi-Sheet System", layout="wide")
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Kanit:wght@300;400;500;600&display=swap');
    html, body, [class*="css"], .main { background-color: #0E1117; color: #FFFFFF !important; font-family: 'Kanit', sans-serif; }
    .stButton > button { background: linear-gradient(45deg, #FF4B2B, #FF416C); color: white; border-radius: 10px; border: none; padding: 10px 20px; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

st.title("📦 ระบบแยกชีทใบเบิกสินค้า (Multi-Sheet Version)")

uploaded_file = st.file_uploader("📥 อัปโหลดไฟล์ใบเบิกสินค้าต้นทาง (Raw Data)", type="xlsx")

if uploaded_file:
    if st.button("🚀 ประมวลผลและสร้างไฟล์ 3 ชีท"):
        try:
            # 1. ค้นหาหัวตาราง Description
            raw_excel = pd.read_excel(uploaded_file, header=None)
            header_idx = next((i for i, r in raw_excel.iterrows() if r.astype(str).str.contains('Description', case=False, na=False).any()), None)
            
            if header_idx is not None:
                df = pd.read_excel(uploaded_file, skiprows=header_idx)
                df.columns = [str(c).strip() for c in df.columns]
                
                static_cols = ['#', 'Item No.', 'Description', 'UNIT']
                store_cols = [c for c in df.columns if c not in static_cols and 'Unnamed' not in c]
                
                # เก็บข้อมูล Mapping สาขาและทริป
                trip_map = {s: df[s].iloc[0] for s in store_cols}
                name_map = {s: (df[s].iloc[1] if len(df) > 1 else s) for s in store_cols}

                # 2. คัดแยกข้อมูลตามหน่วย (Unit)
                all_data = []
                for _, row in df.iterrows():
                    item = row.get('Description')
                    unit = str(row.get('UNIT', '')).strip()
                    if pd.isna(item) or str(item).strip() in ['', '0', '0.0']: continue
                    
                    for store in store_cols:
                        qty = row[store]
                        if pd.notna(qty) and isinstance(qty, (int, float)) and qty > 0:
                            all_data.append({
                                'STORE ID': store,
                                'STORE NAME': name_map.get(store),
                                'Trip': trip_map.get(store),
                                'Product': item,
                                'Qty': qty,
                                'Unit': unit
                            })
                
                if all_data:
                    full_df = pd.DataFrame(all_data)

                    # --- กรองข้อมูลแยกชีท ---
                    # ชีทน้ำหนัก: เอาเฉพาะที่มีคำว่า 'กิโลกรัม' หรือหน่วยที่เกี่ยวข้องกับน้ำหนัก
                    weight_list = full_df[full_df['Unit'].str.contains('กิโลกรัม|กรัม|kg|g', case=False, na=False)]
                    
                    # ชีทจัดกล่อง: เอาของที่เป็นชิ้น หรือหน่วยอื่นๆ ที่ไม่ใช่กิโลกรัม
                    box_list = full_df[~full_df['Unit'].str.contains('กิโลกรัม|กรัม|kg|g', case=False, na=False)]

                    # ฟังก์ชันช่วยทำ Matrix
                    def make_matrix(src_df):
                        if src_df.empty: return pd.DataFrame()
                        matrix = src_df.pivot_table(index=['STORE ID', 'STORE NAME', 'Trip'], 
                                                   columns='Product', values='Qty', aggfunc='sum').fillna(0).reset_index()
                        matrix.columns.name = None
                        matrix.insert(0, 'No.', range(1, len(matrix) + 1))
                        return matrix

                    # เตรียม DataFrames สำหรับแต่ละชีท
                    sheet_weight = make_matrix(weight_list)
                    sheet_box = make_matrix(box_list)
                    sheet_order = make_matrix(full_df)

                    # 3. เขียนไฟล์ Excel แบบ 3 ชีท
                    output = io.BytesIO()
                    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                        sheet_weight.to_excel(writer, sheet_name='น้ำหนัก', index=False)
                        sheet_box.to_excel(writer, sheet_name='จัดกล่อง', index=False)
                        sheet_order.to_excel(writer, sheet_name='Order', index=False)
                        
                        # เพิ่มความสวยงาม (Auto-Fit คอลัมน์)
                        for sheet in writer.sheets.values():
                            sheet.set_column('A:Z', 20)

                    st.success("✅ แยกข้อมูลลง 3 ชีทเรียบร้อยแล้ว!")
                    st.download_button(
                        label="📥 ดาวน์โหลดไฟล์ Excel (3 ชีท)",
                        data=output.getvalue(),
                        file_name="BNN_Categorized_Report.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                    )
                else:
                    st.warning("ไม่พบยอดการสั่งซื้อในไฟล์")
            else:
                st.error("ไม่พบคอลัมน์ 'Description'")
        except Exception as e:
            st.error(f"เกิดข้อผิดพลาด: {e}")