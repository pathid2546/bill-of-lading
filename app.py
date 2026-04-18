import streamlit as st
import pandas as pd
import re
import io

# --- CONFIG & UI ---
st.set_page_config(page_title="BNN | Smart Order System", layout="wide")

# --- SESSION STATE ---
if 'master_data' not in st.session_state:
    st.session_state.master_data = [
        {"#": 1, "Item No.": "FG-FZ-0014", "Description": "เนื้อสันคอ", "UNIT": "กิโลกรัม"},
        {"#": 2, "Item No.": "FG-FZ-0037", "Description": "เนื้อวัวออสเตรเลีย", "UNIT": "กิโลกรัม"},
        {"#": 3, "Item No.": "FG-FZ-0021", "Description": "สันคอหมู", "UNIT": "กิโลกรัม"},
        {"#": 4, "Item No.": "FG-FZ-0019", "Description": "หมูสามชั้น", "UNIT": "กิโลกรัม"},
        {"#": 5, "Item No.": "FG-FZ-0020", "Description": "หมูสันนอก", "UNIT": "กิโลกรัม"},
        {"#": 6, "Item No.": "FG-FZ-0009", "Description": "ปูอัด", "UNIT": "ลัง"},
        {"#": 7, "Item No.": "FG-FZ-0010", "Description": "ปูอัดชีส", "UNIT": "ลัง"},
        {"#": 8, "Item No.": "FG-FZ-0012", "Description": "ชีสมอสซาเรลล่า", "UNIT": "ลัง"},
        {"#": 9, "Item No.": "FG-FF-0002", "Description": "น้ำจิ้มสุกี้", "UNIT": "แร็ค (8 ถุง)"},
        {"#": 10, "Item No.": "FG-FZ-0028", "Description": "เกี๊ยวผักโขม", "UNIT": "ลัง"},
        {"#": 11, "Item No.": "FG-FZ-0033", "Description": "ไก่กรอบ", "UNIT": "ลัง"},
        {"#": 12, "Item No.": "FG-FZ-0042", "Description": "สาหร่ายวากาเมะ (แช่แข็ง)", "UNIT": "ลัง"},
        {"#": 13, "Item No.": "FG-CH-0024", "Description": "หัวเชื้อน้ำซุปหม่าล่า", "UNIT": "ลัง"},
        {"#": 14, "Item No.": "FG-FZ-0091", "Description": "ปลาเส้น (แช่แข็ง)", "UNIT": "ลัง"},
        {"#": 15, "Item No.": "FG-CH-0026", "Description": "ไส้กรอกแดง", "UNIT": "ลัง"},
        {"#": 16, "Item No.": "FG-FZ-0120", "Description": "คิมมาริ", "UNIT": "ลัง/10 กก."},
        {"#": 17, "Item No.": "FG-FZ-0129", "Description": "เกี๊ยวกุ้ง", "UNIT": "ลัง/12ถาด/1กิโลกรัม"},
        {"#": 18, "Item No.": "FG-CH-0057", "Description": "น้ำจิ้มสุกี้สูตรโบราณ (ถุง2กก.)", "UNIT": "แร็ค/8ถุง/2 กก"},
        {"#": 19, "Item No.": "FG-CH-0060", "Description": "หัวเชื้อน้ำซุปแจ่วฮ้อน (ถุง 5 กก.)", "UNIT": "ลัง/4 ถุง"},
        {"#": 20, "Item No.": "FG-FZ-0133", "Description": "เป็ดย่างพร้อมน้ำราด ตราดาลี", "UNIT": "ลัง/8 แพ็ค"},
        {"#": 21, "Item No.": "FG-CH-0062", "Description": "น้ำจิ้มเป็ด (ถุง 1 กก)", "UNIT": "ลัง/12ถุง"},
        {"#": 22, "Item No.": "FG-CH-0061", "Description": "น้ำจิ้มพอนสึ ยูสุ (ถุง 2 กก.)", "UNIT": "แร็ค/6ถุง"},
        {"#": 23, "Item No.": "FG-FZ-0144", "Description": "หอยแมลงภู่ชิลี NW 100%", "UNIT": "ลัง/1ถุง/10กิโลกรัม"},
        {"#": 24, "Item No.": "FG-FZ-0145", "Description": "เฟรนฟราย 7.4 mm", "UNIT": "ลัง/4แพ็ค/2.5กก."},
        {"#": 25, "Item No.": "FG-FZ-0143", "Description": "ลูกชิ้นหยดน้ำไส้ไข่ปลา", "UNIT": "ลัง/10กก."},
        {"#": 26, "Item No.": "FG-FZ-0147", "Description": "ปลาดอลลี่ NW 70%", "UNIT": "ลัง/10กก."},
        {"#": 27, "Item No.": "FG-FZ-9035", "Description": "ไก่คาราเกะ", "UNIT": "ลัง/10ถุง/1กิโลกรัม"}
    ]

if 'header_title' not in st.session_state:
    st.session_state.header_title = "ใบเบิกสินค้า สาขา"
if 'company_name_th' not in st.session_state:
    st.session_state.company_name_th = "บริษัท บี เอ็น เอ็น เรสเตอรองท์ กรุ๊ป จำกัด"
if 'company_name_en' not in st.session_state:
    st.session_state.company_name_en = "Company BNN RESTAURANT GROUP COMPANY LIMITED"

# --- SIDEBAR ---
with st.sidebar:
    st.title("BNN Group")
    menu = st.radio("เมนูหลัก", ["📤 อัปโหลดข้อมูล", "⚙️ ตั้งค่าระบบ"])

# --- UPLOAD PAGE ---
if menu == "📤 อัปโหลดข้อมูล":
    st.header("📤 ประมวลผลใบเบิกสินค้า")
    uploaded_file = st.file_uploader("เลือกไฟล์ Raw Data (.xlsx)", type="xlsx")
    
    if uploaded_file:
        if st.button("🚀 เริ่มการประมวลผล"):
            try:
                df_raw = pd.read_excel(uploaded_file)
                store_col = df_raw.columns[2]
                item_cols = df_raw.columns[4:].tolist()

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
                df_pivot = df_raw.set_index('Clean_Store')[item_cols].T.reset_index()
                df_pivot = df_pivot.rename(columns={'index': 'Description'})
                df_pivot['Description'] = df_pivot['Description'].str.strip()

                # --- ตรรกะการเรียงลำดับใหม่เพื่อป้องกันรายการใหม่ขึ้นก่อน ---
                master_df = pd.DataFrame(st.session_state.master_data)
                master_df['Description'] = master_df['Description'].str.strip()
                master_df['#'] = pd.to_numeric(master_df['#'], errors='coerce')

                # 1. รวมข้อมูล (Outer Join)
                merged_df = pd.merge(master_df, df_pivot, on='Description', how='outer')

                # 2. แยกเป็น 2 กลุ่ม
                # กลุ่ม A: รายการที่มีเลขลำดับ (#) (รายการจาก Master)
                group_a = merged_df[merged_df['#'].notnull()].sort_values(by='#', ascending=True)
                
                # กลุ่ม B: รายการที่ไม่มีเลขลำดับ (#) (รายการใหม่จาก Raw Data)
                group_b = merged_df[merged_df['#'].isnull()]

                # 3. นำกลุ่ม A ตั้ง แล้วเอากลุ่ม B ต่อท้าย (Append)
                final_df = pd.concat([group_a, group_b], ignore_index=True).fillna(0)

                # 4. เขียนไฟล์ Excel
                output = io.BytesIO()
                with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                    workbook = writer.book
                    sheet = workbook.add_worksheet('ใบเบิก')
                    
                    f_base = {'font_name': 'Cordia New', 'font_size': 14}
                    f_header = workbook.add_format({**f_base, 'bg_color': '#002060', 'font_color': 'white', 'bold': True, 'border': 1, 'align': 'center'})
                    f_grey = workbook.add_format({**f_base, 'bg_color': '#D9D9D9', 'border': 1, 'bold': True, 'align': 'center'})
                    f_border = workbook.add_format({**f_base, 'border': 1})
                    f_rotate = workbook.add_format({**f_base, 'font_size': 11, 'rotation': 45, 'valign': 'bottom', 'align': 'center', 'border': 1})
                    f_trip = workbook.add_format({**f_base, 'font_size': 11, 'bg_color': '#FF0000', 'font_color': 'white', 'border': 1, 'align': 'center', 'bold': True})

                    # หัวเอกสาร
                    sheet.merge_range('A1:Z1', st.session_state.header_title, f_header)
                    sheet.write('A2', st.session_state.company_name_th, workbook.add_format(f_base))
                    sheet.write('A3', st.session_state.company_name_en, workbook.add_format(f_base))

                    for i, h in enumerate(['#', 'Item No.', 'Description', 'UNIT']):
                        sheet.write(5, i, h, f_grey)
                        sheet.write(6, i, "", f_border)

                    stores = [c for c in final_df.columns if c not in ['#', 'Item No.', 'Description', 'UNIT']]
                    for i, s in enumerate(stores):
                        col_idx = i + 4
                        sheet.write(5, col_idx, s, f_rotate)
                        sheet.write(6, col_idx, short_codes.get(s, ""), f_trip)
                        sheet.set_column(col_idx, col_idx, 5)

                    for i, row in final_df.iterrows():
                        ri = i + 7
                        # ถ้าเป็นรายการใหม่ที่ไม่มีเลขลำดับ ให้ใส่ "-" หรือปล่อยว่างตามที่คุณต้องการ
                        disp_idx = int(row['#']) if row['#'] != 0 else "-"
                        
                        sheet.write(ri, 0, disp_idx, f_border)
                        sheet.write(ri, 1, row.get('Item No.', "-") if row.get('Item No.') != 0 else "-", f_border)
                        sheet.write(ri, 2, row['Description'], f_border)
                        sheet.write(ri, 3, row.get('UNIT', "-") if row.get('UNIT') != 0 else "-", f_border)
                        for cj, sn in enumerate(stores):
                            sheet.write(ri, cj+4, row[sn], f_border)

                    sheet.set_column('C:C', 35)
                    sheet.set_column('D:D', 15)

                st.session_state.ready_file = output.getvalue()
                st.success("✅ แก้ไขการเรียงลำดับแล้ว! รายการใหม่จะไปต่อท้ายเสมอ")
            except Exception as e:
                st.error(f"Error: {e}")

    if 'ready_file' in st.session_state:
        st.download_button("📥 ดาวน์โหลดไฟล์ Excel", st.session_state.ready_file, "BNN_Correct_Sorting.xlsx")

# --- SETTINGS PAGE ---
elif menu == "⚙️ ตั้งค่าระบบ":
    st.header("⚙️ ตั้งค่าระบบ")
    st.subheader("📦 มาสเตอร์สินค้า (ลำดับ 1-27)")
    edited_df = st.data_editor(pd.DataFrame(st.session_state.master_data), num_rows="dynamic", use_container_width=True)
    if st.button("💾 บันทึกมาสเตอร์"):
        st.session_state.master_data = edited_df.to_dict('records')
        st.success("บันทึกเรียบร้อย")