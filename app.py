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
unit_map = dict(zip(edited_df['Description'], edited_df['UNIT']))

st.subheader("📤 อัปโหลดไฟล์ Raw Data")
uploaded_file = st.file_uploader("เลือกไฟล์ Excel (.xlsx)", type="xlsx")

if "download_ready" not in st.session_state:
    st.session_state.download_ready = None

if uploaded_file:
    if st.button("🚀 เริ่มประมวลผลไฟล์"):
        with st.spinner('กำลังประมวลผล...'):
            try:
                # 1. อ่านไฟล์และสร้าง Item No. Mapping
                df_raw = pd.read_excel(uploaded_file)
                
                # เก็บ mapping ระหว่าง Description -> Item No. จากไฟล์ต้นฉบับ
                # สมมติว่า Item No. อยู่ในคอลัมน์ Index ที่ 1 (ถ้าไม่ใช่ ให้แก้เลข 1 เป็นชื่อคอลัมน์)
                item_no_col = df_raw.columns[3] 
                desc_col = df_raw.columns[0] # หรือชื่อคอลัมน์สินค้า
                item_no_map = dict(zip(df_raw[desc_col], df_raw[item_no_col]))

                store_col_original = df_raw.columns[2]
                item_headers = df_raw.columns[4:].tolist()

                # 2. แยก Short Code และจัดกลุ่มสาขา
                short_codes = {}
                clean_names = []
                for val in df_raw[store_col_original]:
                    match = re.search(r'\((.*?)\)', str(val))
                    s_code = match.group(1) if match else ""
                    name = re.sub(r'\(.*?\)', '', str(val)).strip()
                    clean_names.append(name)
                    short_codes[name] = s_code

                df_raw['Clean_Store'] = clean_names
                df_pivot = df_raw.set_index('Clean_Store')[item_headers].T.reset_index()
                df_pivot = df_pivot.rename(columns={'index': 'Description'}).drop_duplicates(subset=['Description']).fillna(0)

                # 3. สร้างไฟล์ Excel ด้วย XlsxWriter
                output = io.BytesIO()
                with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                    workbook = writer.book
                    sheet = workbook.add_worksheet('ใบเบิกสินค้า')

                    # Styles (Cordia New)
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

                    # หัวตารางหลัก (แถวที่ 6)
                    headers = ['#', 'Item No.', 'Description', 'UNIT']
                    for i, h in enumerate(headers):
                        sheet.write(5, i, h, f_grey_head)
                        sheet.write(6, i, "", f_border) # แถวที่ 7 ใต้หัวข้อหลักให้ว่าง

                    stores = [c for c in df_pivot.columns if c != 'Description']
                    for i, s in enumerate(stores):
                        c_idx = i + 4
                        sheet.write(5, c_idx, s, f_rotate)
                        sheet.write(6, c_idx, short_codes.get(s, ""), f_red) # แถวที่ 7: Short Code สีแดง
                        sheet.set_column(c_idx, c_idx, 5)

                    # เขียนข้อมูลสินค้า (เริ่มแถวที่ 8)
                    for r_idx, row in df_pivot.iterrows():
                        e_row = r_idx + 7
                        desc = row['Description']
                        
                        sheet.write(e_row, 0, r_idx + 1, f_border) # ลำดับ (#)
                        sheet.write(e_row, 1, item_no_map.get(desc, ""), f_border) # Item No. ดึงจากรหัสสินค้าต้นฉบับ
                        sheet.write(e_row, 2, desc, f_border) # รายการสินค้า
                        sheet.write(e_row, 3, unit_map.get(desc, "-"), f_border) # หน่วย (UNIT)
                        
                        for c_idx, s in enumerate(stores):
                            sheet.write(e_row, c_idx + 4, row[s], f_border)

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