import streamlit as st
import pandas as pd
import re
import io

# 1. ข้อมูล Default UNIT
DEFAULT_UNITS = [
    {"Description": "เนื้อสันคอ", "UNIT": "กิโลกรัม"},
    {"Description": "เนื้อวัวออสเตรเลีย", "UNIT": "กิโลกรัม"},
    {"Description": "สันคอหมู", "UNIT": "กิโลกรัม"},
    {"Description": "หมูสามชั้น", "UNIT": "กิโลกรัม"},
    {"Description": "หมูสันนอก", "UNIT": "กิโลกรัม"},
    {"Description": "ปูอัด", "UNIT": "ลัง"},
    {"Description": "ปูอัดชีส", "UNIT": "ลัง"},
    {"Description": "ชีสมอสซาเรลล่า", "UNIT": "ลัง"},
    {"Description": "น้ำจิ้มสุกี้", "UNIT": "แร็ค (8 ถุง)"},
    {"Description": "เกี๊ยวผักโขม", "UNIT": "ลัง"},
    {"Description": "ไก่กรอบ", "UNIT": "ลัง"},
    {"Description": "สาหร่ายวากาเมะ (แช่แข็ง)", "UNIT": "ลัง"},
    {"Description": "หัวเชื้อน้ำซุปหม่าล่า", "UNIT": "ลัง"},
    {"Description": "ปลาเส้น (แช่แข็ง)", "UNIT": "ลัง"},
    {"Description": "ไส้กรอกแดง", "UNIT": "ลัง"},
    {"Description": "คิมมาริ", "UNIT": "ลัง/10 กก."},
    {"Description": "เกี๊ยวกุ้ง", "UNIT": "ลัง/12ถาด/1กิโลกรัม"},
    {"Description": "น้ำจิ้มสุกี้สูตรโบราณ (ถุง2กก.)", "UNIT": "แร็ค/8ถุง/2 กก"},
    {"Description": "หัวเชื้อน้ำซุปแจ่วฮ้อน (ถุง 5 กก.)", "UNIT": "ลัง/4 ถุง"},
    {"Description": "เป็ดย่างพร้อมน้ำราด ตราดาลี", "UNIT": "ลัง/8 แพ็ค"},
    {"Description": "น้ำจิ้มเป็ด (ถุง 1 กก)", "UNIT": "ลัง/12ถุง"},
    {"Description": "น้ำจิ้มพอนสึ ยูสุ (ถุง 2 กก.)", "UNIT": "แร็ค/6ถุง"},
    {"Description": "หอยแมลงภู่ชิลี NW 100%", "UNIT": "ลัง/1ถุง/10กิโลกรัม"},
    {"Description": "เฟรนฟราย 7.4 mm", "UNIT": "ลัง/4แพ็ค/2.5กก."},
    {"Description": "ลูกชิ้นหยดน้ำไส้ไข่ปลา", "UNIT": "ลัง/10กก."},
    {"Description": "ปลาดอลลี่ NW 70%", "UNIT": "ลัง/10กก."},
    {"Description": "ไก่คาราเกะ", "UNIT": "ลัง/10ถุง/1กิโลกรัม"}
]

st.set_page_config(page_title="BNN Excel Converter", layout="wide")
st.title("📦 ระบบจัดการใบเบิกสินค้า (Streamlit)")

# ส่วนข้อมูลบริษัท
st.subheader("🏢 ข้อมูลบริษัท")
c1, c2 = st.columns(2)
comp_th = c1.text_input("ชื่อภาษาไทย", "บริษัท บี เอ็น เอ็น เรสเตอรองท์ กรุ๊ป จำกัด")
comp_en = c2.text_input("ชื่อภาษาอังกฤษ", "Company BNN RESTAURANT GROUP COMPANY LIMITED")

# ตารางจัดการ UNIT
st.subheader("📋 จัดการหน่วยสินค้า (UNIT)")
edited_df = st.data_editor(pd.DataFrame(DEFAULT_UNITS), num_rows="dynamic", use_container_width=True)
unit_map = dict(zip(edited_df['Description'].str.strip(), edited_df['UNIT'].str.strip()))

st.subheader("📤 อัปโหลดไฟล์ Raw Data")
uploaded_file = st.file_uploader("เลือกไฟล์ Excel (.xlsx)", type="xlsx")

if "download_ready" not in st.session_state:
    st.session_state.download_ready = None

if uploaded_file:
    if st.button("🚀 เริ่มประมวลผลไฟล์"):
        with st.spinner('กำลังประมวลผล...'):
            try:
                # 1. อ่านไฟล์ Raw Data
                df_raw = pd.read_excel(uploaded_file)
                
                # ระบุตำแหน่งคอลัมน์ Trip และ Store Name จากรูปภาพ
                # Column C (index 2) = STORE NAME, Column D (index 3) = Trip
                store_col = df_raw.columns[2]
                trip_col = df_raw.columns[3]
                item_start_idx = 4 # สินค้าเริ่มที่คอลัมน์ E (index 4) เป็นต้นไป

                # --- NEW LOGIC: สร้าง Item No. Map ---
                # เนื่องจากสินค้าเป็นหัวคอลัมน์ เราต้องหาว่าสินค้าแต่ละตัวอยู่ใน Trip ไหน
                # เราจะสแกนคอลัมน์สินค้า และหา Trip ที่มีค่ามากกว่า 0
                item_names = df_raw.columns[item_start_idx:].tolist()
                trip_for_items = {}

                for item in item_names:
                    # หาแถวที่สินค้านั้นๆ มีจำนวน (ไม่เป็น 0 หรือ NaN) และดึงค่า Trip มา
                    valid_trips = df_raw[df_raw[item] > 0][trip_col].unique()
                    if len(valid_trips) > 0:
                        trip_for_items[str(item).strip()] = str(valid_trips[0])
                    else:
                        trip_for_items[str(item).strip()] = "-"

                # 2. แยก Short Code และจัดกลุ่มสาขา
                short_codes = {}
                clean_names = []
                for val in df_raw[store_col]:
                    v_str = str(val)
                    match = re.search(r'\((.*?)\)', v_str)
                    s_code = match.group(1) if match else ""
                    name = re.sub(r'\(.*?\)', '', v_str).strip()
                    clean_names.append(name)
                    short_codes[name] = s_code

                df_raw['Clean_Store'] = clean_names
                
                # ทำ Pivot ตาราง (สลับสินค้ามาเป็นแนวตั้ง)
                df_pivot = df_raw.set_index('Clean_Store')[item_names].T.reset_index()
                df_pivot = df_pivot.rename(columns={'index': 'Description'}).drop_duplicates(subset=['Description']).fillna(0)

                # 3. สร้างไฟล์ Excel
                output = io.BytesIO()
                with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                    workbook = writer.book
                    sheet = workbook.add_worksheet('ใบเบิกสินค้า')

                    # Styles
                    f_base = {'font_name': 'Cordia New', 'font_size': 14}
                    f_header = workbook.add_format({**f_base, 'bg_color': '#002060', 'font_color': 'white', 'bold': True, 'border': 1, 'align': 'center'})
                    f_red = workbook.add_format({**f_base, 'font_size': 11, 'bg_color': '#FF0000', 'font_color': 'white', 'border': 1, 'align': 'center', 'bold': True})
                    f_rotate = workbook.add_format({**f_base, 'font_size': 11, 'rotation': 45, 'valign': 'bottom', 'align': 'center', 'border': 1})
                    f_border = workbook.add_format({**f_base, 'border': 1})
                    f_grey_head = workbook.add_format({**f_base, 'bg_color': '#D9D9D9', 'border': 1, 'bold': True, 'align': 'center'})

                    # เขียนส่วนหัว
                    sheet.merge_range('A1:Z1', 'ใบเบิกสินค้า สาขา', f_header)
                    sheet.write('A2', comp_th, workbook.add_format(f_base))
                    sheet.write('A3', comp_en, workbook.add_format(f_base))

                    # หัวตารางหลัก
                    headers = ['#', 'Item No.', 'Description', 'UNIT']
                    for i, h in enumerate(headers):
                        sheet.write(5, i, h, f_grey_head)
                        sheet.write(6, i, "", f_border)

                    stores = [c for c in df_pivot.columns if c != 'Description']
                    for i, s in enumerate(stores):
                        c_idx = i + 4
                        sheet.write(5, c_idx, s, f_rotate)
                        sheet.write(6, c_idx, short_codes.get(s, ""), f_red) #
                        sheet.set_column(c_idx, c_idx, 5)

                    # เขียนข้อมูลรายสินค้า
                    for r_idx, row in df_pivot.iterrows():
                        e_row = r_idx + 7
                        desc_val = str(row['Description']).strip()
                        
                        sheet.write(e_row, 0, r_idx + 1, f_border)
                        # ดึงค่า Trip ที่จับคู่ไว้มาใส่ในช่อง Item No.
                        sheet.write(e_row, 1, trip_for_items.get(desc_val, "-"), f_border) 
                        sheet.write(e_row, 2, desc_val, f_border)
                        sheet.write(e_row, 3, unit_map.get(desc_val, "-"), f_border)
                        
                        for c_idx, s in enumerate(stores):
                            sheet.write(e_row, c_idx + 4, row[s], f_border)

                    sheet.set_column('C:C', 35)
                    sheet.set_column('D:D', 15)

                st.session_state.download_ready = output.getvalue()
                st.success("✅ ประมวลผลสำเร็จ!")
            except Exception as e:
                st.error(f"เกิดข้อผิดพลาด: {e}")

    if st.session_state.download_ready:
        st.download_button(
            label="💾 ดาวน์โหลดไฟล์ใบเบิกสินค้า",
            data=st.session_state.download_ready,
            file_name="Converted_Order_File.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )