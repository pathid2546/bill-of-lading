import streamlit as st
import pandas as pd
import re
import io

# --- CONFIG & ASSETS ---
st.set_page_config(page_title="BNN | Smart Order System", layout="wide", initial_sidebar_state="expanded")

# Custom CSS เพื่อความสวยงาม (ไม่ให้ดูเหมือน AI Draft ทั่วไป)
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Kanit:wght@300;400;500&display=swap');
    html, body, [class*="css"] { font-family: 'Kanit', sans-serif; }
    .main { background-color: #f8f9fa; }
    .stButton>button { width: 100%; border-radius: 8px; height: 3em; background-color: #002060; color: white; border: none; font-weight: 500; }
    .stButton>button:hover { background-color: #003399; color: white; }
    .metric-card { background: white; padding: 20px; border-radius: 10px; border-left: 5px solid #002060; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }
    </style>
    """, unsafe_allow_html=True)

# --- DEFAULT DATA ---
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
        {"#": 13, "Item No. : "FG-CH-0024", "Description": "หัวเชื้อน้ำซุปหม่าล่า", "UNIT": "ลัง"},
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

# --- SIDEBAR NAV ---
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/4090/4090434.png", width=80)
    st.title("BNN Group")
    st.markdown("---")
    menu = st.radio("เมนูหลัก", ["📤 อัปโหลดข้อมูล", "⚙️ ตั้งค่าระบบ", "📊 ประวัติการทำงาน"])
    st.markdown("---")
    st.caption("v2.1.0 - Professional Edition")

# --- MAIN CONTENT ---
if menu == "📤 อัปโหลดข้อมูล":
    st.header("📤 การประมวลผลใบเบิกสินค้า")
    
    # Header Info Cards
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown('<div class="metric-card"><b>สถานะระบบ</b><br><span style="color:green">● พร้อมใช้งาน</span></div>', unsafe_allow_html=True)
    with col2:
        st.markdown(f'<div class="metric-card"><b>สินค้าในระบบ</b><br>{len(st.session_state.master_data)} รายการ</div>', unsafe_allow_html=True)
    with col3:
        st.markdown('<div class="metric-card"><b>ฟอร์แมตไฟล์</b><br>Excel (.xlsx)</div>', unsafe_allow_html=True)
    
    st.write("")
    
    # Upload Area
    with st.container():
        st.subheader("1. เลือกไฟล์ต้นฉบับ")
        uploaded_file = st.file_uploader("", type="xlsx", help="ลากไฟล์ Raw Data มาวางที่นี่")
        
        if uploaded_file:
            st.success(f"พบไฟล์: {uploaded_file.name}")
            if st.button("🚀 เริ่มต้นการแปลงข้อมูล"):
                with st.spinner('ระบบกำลังวิเคราะห์โครงสร้างตารางและสร้างไฟล์...'):
                    # Logic การประมวลผล (ยกจากเวอร์ชันก่อนหน้า)
                    try:
                        df_raw = pd.read_excel(uploaded_file)
                        store_col = df_raw.columns[2]
                        item_cols = df_raw.columns[4:].tolist()

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
                        df_pivot = df_raw.set_index('Clean_Store')[item_cols].T.reset_index()
                        df_pivot = df_pivot.rename(columns={'index': 'Description'}).drop_duplicates(subset=['Description']).fillna(0)

                        # Mapping Data
                        master_df = pd.DataFrame(st.session_state.master_data)
                        idx_map = dict(zip(master_df['Description'].str.strip(), master_df['#']))
                        it_map = dict(zip(master_df['Description'].str.strip(), master_df['Item No.'].str.strip()))
                        un_map = dict(zip(master_df['Description'].str.strip(), master_df['UNIT'].str.strip()))

                        output = io.BytesIO()
                        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                            workbook = writer.book
                            sheet = workbook.add_worksheet('ใบเบิกสินค้า')

                            f_base = {'font_name': 'Cordia New', 'font_size': 14}
                            f_h = workbook.add_format({**f_base, 'bg_color': '#002060', 'font_color': 'white', 'bold': True, 'border': 1, 'align': 'center'})
                            f_r = workbook.add_format({**f_base, 'font_size': 11, 'bg_color': '#FF0000', 'font_color': 'white', 'border': 1, 'align': 'center', 'bold': True})
                            f_rot = workbook.add_format({**f_base, 'font_size': 11, 'rotation': 45, 'valign': 'bottom', 'align': 'center', 'border': 1})
                            f_b = workbook.add_format({**f_base, 'border': 1})
                            f_g = workbook.add_format({**f_base, 'bg_color': '#D9D9D9', 'border': 1, 'bold': True, 'align': 'center'})

                            # Header
                            sheet.merge_range('A1:Z1', 'ใบเบิกสินค้า สาขา', f_h)
                            sheet.write('A2', "บริษัท บี เอ็น เอ็น เรสเตอรองท์ กรุ๊ป จำกัด", workbook.add_format(f_base))
                            sheet.write('A3', "Company BNN RESTAURANT GROUP COMPANY LIMITED", workbook.add_format(f_base))

                            # Table Head
                            for i, h in enumerate(['#', 'Item No.', 'Description', 'UNIT']):
                                sheet.write(5, i, h, f_g)
                                sheet.write(6, i, "", f_b)

                            stores = [c for c in df_pivot.columns if c != 'Description']
                            for i, s in enumerate(stores):
                                ci = i + 4
                                sheet.write(5, ci, s, f_rot)
                                sheet.write(6, ci, short_codes.get(s, ""), f_r) #
                                sheet.set_column(ci, ci, 5)

                            for i, row in df_pivot.iterrows():
                                ri = i + 7
                                d = str(row['Description']).strip()
                                sheet.write(ri, 0, idx_map.get(d, i+1), f_b)
                                sheet.write(ri, 1, it_map.get(d, "-"), f_b)
                                sheet.write(ri, 2, d, f_b)
                                sheet.write(ri, 3, un_map.get(d, "-"), f_b)
                                for cj, st_name in enumerate(stores):
                                    sheet.write(ri, cj + 4, row[st_name], f_b)

                            sheet.set_column('C:C', 35)
                            sheet.set_column('D:D', 20)

                        st.session_state.ready_file = output.getvalue()
                        st.balloons()
                        st.success("🎉 ประมวลผลเรียบร้อย!")

            if 'ready_file' in st.session_state:
                st.download_button("📥 ดาวน์โหลดไฟล์ใบเบิกที่เสร็จแล้ว", st.session_state.ready_file, "BNN_Order_Form.xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

elif menu == "⚙️ ตั้งค่าระบบ":
    st.header("⚙️ ตั้งค่ามาสเตอร์ไฟล์")
    
    tab1, tab2 = st.tabs(["📋 รายการสินค้า & Item No.", "🏢 ข้อมูลองค์กร"])
    
    with tab1:
        st.subheader("จัดการ Mapping ข้อมูลสินค้า")
        # Editable Table
        edited_df = st.data_editor(pd.DataFrame(st.session_state.master_data), num_rows="dynamic", use_container_width=True, key="data_editor")
        if st.button("💾 บันทึกการเปลี่ยนแปลง"):
            st.session_state.master_data = edited_df.to_dict('records')
            st.toast("บันทึกข้อมูลสำเร็จ!", icon="✅")

    with tab2:
        st.subheader("รายละเอียดหัวกระดาษ")
        st.text_input("ชื่อบริษัท (ภาษาไทย)", "บริษัท บี เอ็น เอ็น เรสเตอรองท์ กรุ๊ป จำกัด")
        st.text_input("ชื่อบริษัท (English)", "Company BNN RESTAURANT GROUP COMPANY LIMITED")
        st.color_picker("สีหลักของหัวตาราง", "#002060")

elif menu == "📊 ประวัติการทำงาน":
    st.header("📊 บันทึกการทำงาน")
    st.info("ส่วนนี้ไว้สำหรับดูประวัติการอัปโหลดไฟล์ในอนาคต")
    st.empty()