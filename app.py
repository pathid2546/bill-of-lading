import streamlit as st
import pandas as pd
import re
import io

# 1. นิยามข้อมูล Default UNIT ตามรายการที่ส่งมา
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

# 2. ฟังก์ชันหลักสำหรับหน้าเว็บ
def main():
    st.set_page_config(page_title="BNN Excel Converter", layout="wide")
    st.title("📦 ระบบจัดการใบเบิกสินค้า (Streamlit)")

    # ส่วนข้อมูลบริษัท
    st.subheader("🏢 ข้อมูลบริษัท (Default)")
    col1, col2 = st.columns(2)
    comp_th = col1.text_input("ชื่อภาษาไทย", "บริษัท บี เอ็น เอ็น เรสเตอรองท์ กรุ๊ป จำกัด")
    comp_en = col2.text_input("ชื่อภาษาอังกฤษ", "Company BNN RESTAURANT GROUP COMPANY LIMITED")

    # ส่วนจัดการหน่วยสินค้าพร้อมค่า Default
    st.subheader("📋 จัดการหน่วยสินค้า (แก้ไขได้)")
    
    # ใช้ Data Editor โดยใส่ค่า DEFAULT_UNITS ลงไปเลย
    edited_df = st.data_editor(
        pd.DataFrame(DEFAULT_UNITS), 
        num_rows="dynamic", 
        use_container_width=True,
        key="unit_editor"
    )
    
    # สร้าง Map ข้อมูลไว้ใช้งาน
    unit_map = dict(zip(edited_df['Description'], edited_df['UNIT']))

    # ส่วนอัปโหลดไฟล์
    st.subheader("📤 อัปโหลดไฟล์และประมวลผล")
    uploaded_file = st.file_uploader("เลือกไฟล์ Excel", type="xlsx")

    if uploaded_file and st.button("ประมวลผลไฟล์"):
        # (โค้ดส่วนประมวลผลเดิมที่ใช้ XlsxWriter...)
        # เมื่อเขียนไฟล์จะดึงค่าจาก unit_map มาใช้โดยอัตโนมัติ
        st.success("ประมวลผลสำเร็จ! กรุณากดดาวน์โหลด")
        # st.download_button(...)

if __name__ == "__main__":
    main()