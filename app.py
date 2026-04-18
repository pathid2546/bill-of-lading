import streamlit as st
import pandas as pd
import re
import io

# ตั้งค่าหน้าเว็บ
st.set_page_config(page_title="BNN Excel Converter", layout="wide")

st.title("📦 ระบบจัดการใบเบิกสินค้า (Streamlit Version)")

# 1. ส่วนตั้งค่าชื่อบริษัท
st.subheader("🏢 ข้อมูลบริษัท")
col_th, col_en = st.columns(2)
comp_th = col_th.text_input("ชื่อภาษาไทย", "บริษัท บี เอ็น เอ็น เรสเตอรองท์ กรุ๊ป จำกัด")
comp_en = col_en.text_input("ชื่อภาษาอังกฤษ", "Company BNN RESTAURANT GROUP COMPANY LIMITED")

# 2. ส่วนจัดการ UNIT
st.subheader("📋 ตั้งค่าหน่วยสินค้า (UNIT)")
if 'unit_data' not in st.session_state:
    st.session_state.unit_data = [{"Description": "เกี๊ยวกุ้ง", "UNIT": "ลัง/12ถาด/1กิโลกรัม"}]

# ตารางแก้ไขข้อมูล
edited_df = st.data_editor(pd.DataFrame(st.session_state.unit_data), num_rows="dynamic", use_container_width=True)
unit_map = dict(zip(edited_df['Description'], edited_df['UNIT']))

# 3. ส่วนอัปโหลดและประมวลผล
st.subheader("📤 อัปโหลดไฟล์ Raw Data")
uploaded_file = st.file_uploader("เลือกไฟล์ Excel (.xlsx)", type="xlsx")

if uploaded_file:
    if st.button("ประมวลผลและดาวน์โหลด"):
        df_raw = pd.read_excel(uploaded_file)
        store_col = df_raw.columns[2]
        item_headers = df_raw.columns[4:].tolist()

        # แยก Short Code
        short_codes = {}
        clean_names = []
        for val in df_raw[store_col]:
            match = re.search(r'\((.*?)\)', str(val))
            s_code = match.group(1) if match else ""
            name = re.sub(r'\(.*?\)', '', str(val)).strip()
            clean_names.append(name)
            short_codes[name] = s_code

        df_raw['Clean_Store'] = clean_names
        df_pivot = df_raw.set_index('Clean_Store')[item_headers].T.reset_index()
        df_pivot = df_pivot.rename(columns={'index': 'Description'}).drop_duplicates(subset=['Description']).fillna(0)

        # สร้าง Excel ด้วย XlsxWriter
        output = io.BytesIO()
        writer = pd.ExcelWriter(output, engine='xlsxwriter')
        workbook = writer.book
        sheet = workbook.add_worksheet('ใบเบิกสินค้า')

        # Styles (Cordia New)
        f_base = {'font_name': 'Cordia New', 'font_size': 14}
        f_header = workbook.add_format({**f_base, 'bg_color': '#002060', 'font_color': 'white', 'bold': True, 'border': 1, 'align': 'center'})
        f_red = workbook.add_format({**f_base, 'font_size': 11, 'bg_color': '#FF0000', 'font_color': 'white', 'border': 1, 'align': 'center'})
        f_rotate = workbook.add_format({**f_base, 'font_size': 11, 'rotation': 45, 'valign': 'bottom', 'align': 'center', 'border': 1})
        f_border = workbook.add_format({**f_base, 'border': 1})

        # เขียนข้อมูล
        sheet.merge_range('A1:Z1', 'ใบเบิกสินค้า สาขา', f_header)
        sheet.write('A2', comp_th, workbook.add_format(f_base))
        sheet.write('A3', comp_en, workbook.add_format(f_base))

        headers = ['#', 'Item No.', 'Description', 'UNIT']
        for i, h in enumerate(headers):
            sheet.write(5, i, h, workbook.add_format({**f_base, 'bg_color': '#D9D9D9', 'border': 1}))
            sheet.write(6, i, "", f_border)

        stores = [c for c in df_pivot.columns if c != 'Description']
        for i, s in enumerate(stores):
            c_idx = i + 4
            sheet.write(5, c_idx, s, f_rotate)
            sheet.write(6, c_idx, short_codes.get(s, ""), f_red) # Short Code แถวสีแดง
            sheet.set_column(c_idx, c_idx, 5)

        for r_idx, row in df_pivot.iterrows():
            e_row = r_idx + 7
            sheet.write(e_row, 0, r_idx + 1, f_border)
            sheet.write(e_row, 1, "", f_border)
            sheet.write(e_row, 2, row['Description'], f_border)
            sheet.write(e_row, 3, unit_map.get(row['Description'], "-"), f_border)
            for c_idx, s in enumerate(stores):
                sheet.write(e_row, c_idx + 4, row[s], f_border)

        writer.close()
        st.download_button(
            label="💾 คลิกเพื่อดาวน์โหลดไฟล์ Excel",
            data=output.getvalue(),
            file_name="ใบเบิกสินค้า_Final.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )