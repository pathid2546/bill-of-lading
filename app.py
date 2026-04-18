import streamlit as st
import pandas as pd
import re
import io

# 1. รวบรวมข้อมูลเริ่มต้นตามรูปภาพ
DEFAULT_DATA = [
    {"Item No.": "FG-FZ-0014", "Description": "เนื้อสันคอ", "UNIT": "กิโลกรัม"},
    {"Item No.": "FG-FZ-0037", "Description": "เนื้อวัวออสเตรเลีย", "UNIT": "กิโลกรัม"},
    {"Item No.": "FG-FZ-0021", "Description": "สันคอหมู", "UNIT": "กิโลกรัม"},
    {"Item No.": "FG-FZ-0019", "Description": "หมูสามชั้น", "UNIT": "กิโลกรัม"},
    {"Item No.": "FG-FZ-0020", "Description": "หมูสันนอก", "UNIT": "กิโลกรัม"},
    {"Item No.": "FG-FZ-0009", "Description": "ปูอัด", "UNIT": "ลัง"},
    {"Item No.": "FG-FZ-0010", "Description": "ปูอัดชีส", "UNIT": "ลัง"},
    {"Item No.": "FG-FZ-0012", "Description": "ชีสมอสซาเรลล่า", "UNIT": "ลัง"},
    {"Item No.": "FG-FF-0002", "Description": "น้ำจิ้มสุกี้", "UNIT": "แร็ค (8 ถุง)"},
    {"Item No.": "FG-FZ-0028", "Description": "เกี๊ยวผักโขม", "UNIT": "ลัง"},
    {"Item No.": "FG-FZ-0033", "Description": "ไก่กรอบ", "UNIT": "ลัง"},
    {"Item No.": "FG-FZ-0042", "Description": "สาหร่ายวากาเมะ (แช่แข็ง)", "UNIT": "ลัง"},
    {"Item No.": "FG-CH-0024", "Description": "หัวเชื้อน้ำซุปหม่าล่า", "UNIT": "ลัง"},
    {"Item No.": "FG-FZ-0091", "Description": "ปลาเส้น (แช่แข็ง)", "UNIT": "ลัง"},
    {"Item No.": "FG-CH-0026", "Description": "ไส้กรอกแดง", "UNIT": "ลัง"},
    {"Item No.": "FG-FZ-0120", "Description": "คิมมาริ", "UNIT": "ลัง/10 กก."},
    {"Item No.": "FG-FZ-0129", "Description": "เกี๊ยวกุ้ง", "UNIT": "ลัง/12ถาด/1กิโลกรัม"},
    {"Item No.": "FG-CH-0057", "Description": "น้ำจิ้มสุกี้สูตรโบราณ (ถุง2กก.)", "UNIT": "แร็ค/8ถุง/2 กก"},
    {"Item No.": "FG-CH-0060", "Description": "หัวเชื้อน้ำซุปแจ่วฮ้อน (ถุง 5 กก.)", "UNIT": "ลัง/4 ถุง"},
    {"Item No.": "FG-FZ-0133", "Description": "เป็ดย่างพร้อมน้ำราด ตราดาลี", "UNIT": "ลัง/8 แพ็ค"},
    {"Item No.": "FG-CH-0062", "Description": "น้ำจิ้มเป็ด (ถุง 1 กก)", "UNIT": "ลัง/12ถุง"},
    {"Item No.": "FG-CH-0061", "Description": "น้ำจิ้มพอนสึ ยูสุ (ถุง 2 กก.)", "UNIT": "แร็ค/6ถุง"},
    {"Item No.": "FG-FZ-0144", "Description": "หอยแมลงภู่ชิลี NW 100%", "UNIT": "ลัง/1ถุง/10กิโลกรัม"},
    {"Item No.": "FG-FZ-0145", "Description": "เฟรนฟราย 7.4 mm", "UNIT": "ลัง/4แพ็ค/2.5กก."},
    {"Item No.": "FG-FZ-0143", "Description": "ลูกชิ้นหยดน้ำไส้ไข่ปลา", "UNIT": "ลัง/10กก."},
    {"Item No.": "FG-FZ-0147", "Description": "ปลาดอลลี่ NW 70%", "UNIT": "ลัง/10กก."},
    {"Item No.": "FG-FZ-9035", "Description": "ไก่คาราเกะ", "UNIT": "ลัง/10ถุง/1กิโลกรัม"}
]

st.set_page_config(page_title="BNN Order Converter", layout="wide")
st.title("📦 ระบบแปลงไฟล์ใบเบิกสินค้า (Custom Fix)")

# ส่วนข้อมูลบริษัท
st.subheader("🏢 ข้อมูลหัวเอกสาร")
c1, c2 = st.columns(2)
comp_th = c1.text_input("ชื่อบริษัท (ไทย)", "บริษัท บี เอ็น เอ็น เรสเตอรองท์ กรุ๊ป จำกัด")
comp_en = c2.text_input("ชื่อบริษัท (Eng)", "Company BNN RESTAURANT GROUP COMPANY LIMITED")

# ส่วนจัดการข้อมูลสินค้า (Item No. & UNIT)
st.subheader("📋 ตั้งค่าข้อมูลสินค้า (Item No. และ UNIT)")
st.info("คุณสามารถแก้ไขรหัสสินค้าและหน่วยได้ในตารางนี้ ข้อมูลจะถูกนำไปใช้ในไฟล์ Excel ผลลัพธ์")
master_df = st.data_editor(pd.DataFrame(DEFAULT_DATA), num_rows="dynamic", use_container_width=True)

# สร้าง Mapping สำหรับใช้งาน
item_map = dict(zip(master_df['Description'].str.strip(), master_df['Item No.'].str.strip()))
unit_map = dict(zip(master_df['Description'].str.strip(), master_df['UNIT'].str.strip()))

# ส่วนอัปโหลดไฟล์
st.subheader("📤 อัปโหลดไฟล์ Raw Data")
uploaded_file = st.file_uploader("เลือกไฟล์ Excel ต้นฉบับ", type="xlsx")

if "excel_data" not in st.session_state:
    st.session_state.excel_data = None

if uploaded_file:
    if st.button("🚀 ประมวลผลและสร้างไฟล์ใหม่"):
        with st.spinner('กำลังจัดรูปแบบเอกสาร...'):
            try:
                df_raw = pd.read_excel(uploaded_file)
                
                # เตรียมรายชื่อสินค้าและสาขา
                store_col = df_raw.columns[2]
                item_cols = df_raw.columns[4:].tolist()

                # ดึง Short Code สาขาจากวงเล็บ
                short_codes = {}
                clean_store_names = []
                for val in df_raw[store_col]:
                    v_str = str(val)
                    match = re.search(r'\((.*?)\)', v_str)
                    s_code = match.group(1) if match else ""
                    name = re.sub(r'\(.*?\)', '', v_str).strip()
                    clean_store_names.append(name)
                    short_codes[name] = s_code

                df_raw['Clean_Store'] = clean_store_names
                
                # Pivot ข้อมูล: เอาสินค้ามาเป็นแนวตั้ง
                df_pivot = df_raw.set_index('Clean_Store')[item_cols].T.reset_index()
                df_pivot = df_pivot.rename(columns={'index': 'Description'}).drop_duplicates(subset=['Description']).fillna(0)

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
                    f_grey = workbook.add_format({**f_base, 'bg_color': '#D9D9D9', 'border': 1, 'bold': True, 'align': 'center'})

                    # หัวเอกสาร
                    sheet.merge_range('A1:Z1', 'ใบเบิกสินค้า สาขา', f_header)
                    sheet.write('A2', comp_th, workbook.add_format(f_base))
                    sheet.write('A3', comp_en, workbook.add_format(f_base))

                    # หัวตาราง (แถวที่ 6 และ 7)
                    headers = ['#', 'Item No.', 'Description', 'UNIT']
                    for i, h in enumerate(headers):
                        sheet.write(5, i, h, f_grey)
                        sheet.write(6, i, "", f_border)

                    stores = [c for c in df_pivot.columns if c != 'Description']
                    for i, s in enumerate(stores):
                        col_idx = i + 4
                        sheet.write(5, col_idx, s, f_rotate)
                        sheet.write(6, col_idx, short_codes.get(s, ""), f_red) # แถว Short Code สีแดง
                        sheet.set_column(col_idx, col_idx, 5)

                    # ข้อมูลสินค้า (เริ่มแถวที่ 8)
                    for idx, row in df_pivot.iterrows():
                        row_idx = idx + 7
                        desc = str(row['Description']).strip()
                        
                        sheet.write(row_idx, 0, idx + 1, f_border)
                        # ดึงค่า Item No. จากตารางที่เราตั้งค่าไว้ด้านบน
                        sheet.write(row_idx, 1, item_map.get(desc, "-"), f_border)
                        sheet.write(row_idx, 2, desc, f_border)
                        sheet.write(row_idx, 3, unit_map.get(desc, "-"), f_border)
                        
                        for c_idx, s in enumerate(stores):
                            sheet.write(row_idx, c_idx + 4, row[s], f_border)

                    sheet.set_column('C:C', 30)
                    sheet.set_column('D:D', 15)

                st.session_state.excel_data = output.getvalue()
                st.success("✨ ประมวลผลสำเร็จ! คุณสามารถดาวน์โหลดไฟล์ได้แล้ว")
            except Exception as e:
                st.error(f"เกิดข้อผิดพลาด: {e}")

if st.session_state.excel_data:
    st.download_button(
        label="💾 ดาวน์โหลดไฟล์ใบเบิกสินค้า (.xlsx)",
        data=st.session_state.excel_data,
        file_name="Converted_Order_Form.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )