import streamlit as st
import pandas as pd
import re
import io

# --- CONFIG & UI ---
st.set_page_config(page_title="BNN | Smart Order System", layout="wide")

# Custom CSS เพื่อความสวยงาม
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Kanit:wght@300;400;500&display=swap');
    html, body, [class*="css"] { font-family: 'Kanit', sans-serif; }
    .main { background-color: #f8f9fa; }
    .stMetric { background-color: #ffffff; padding: 15px; border-radius: 10px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); border-left: 5px solid #002060; }
    div.stButton > button { width: 100%; border-radius: 5px; height: 3em; background-color: #002060; color: white; border: none; font-weight: 500; }
    div.stButton > button:hover { background-color: #003399; color: white; }
    .status-box { padding: 20px; border-radius: 10px; color: white; margin-bottom: 20px; text-align: center; font-weight: 500; }
    </style>
    """, unsafe_allow_html=True)

# --- SESSION STATE (MASTER DATA & HEADERS) ---
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
    st.image("https://cdn-icons-png.flaticon.com/512/3063/3063822.png", width=80)
    st.title("BNN Group")
    st.caption("v2.5.0 - Smart Ordering System")
    st.divider()
    menu = st.radio("เลือกการทำงาน", ["📊 Dashboard & Upload", "⚙️ ตั้งค่าระบบ"])

# --- DASHBOARD & UPLOAD PAGE ---
if menu == "📊 Dashboard & Upload":
    st.title("📊 ประมวลผลใบเบิกสินค้า")
    
    # Overview Cards
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("📦 มาสเตอร์สินค้า", f"{len(st.session_state.master_data)} รายการ")
    with col2:
        st.metric("🏢 ข้อมูลสาขา", "พร้อมดึง Trip Code", delta="Short Code")
    with col3:
        st.metric("📄 รูปแบบไฟล์", "Excel (XLSX)")

    st.divider()

    # Upload Zone
    with st.expander("📂 ขั้นตอนการใช้งาน", expanded=True):
        st.write("1. เลือกไฟล์ Raw Data จากระบบ")
        st.write("2. กดปุ่ม 'ประมวลผล' ระบบจะเรียงลำดับสินค้าตาม Index และนำสินค้าใหม่ไปไว้ท้ายตาราง")
        st.write("3. ตรวจสอบข้อมูลเบื้องต้นและดาวน์โหลดไฟล์")

    uploaded_file = st.file_uploader("ลากไฟล์มาวางที่นี่ หรือ คลิกเพื่อเลือกไฟล์", type="xlsx")
    
    if uploaded_file:
        if st.button("🚀 เริ่มการประมวลผลข้อมูล"):
            try:
                # Processing Logic
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

                master_df = pd.DataFrame(st.session_state.master_data)
                master_df['Description'] = master_df['Description'].str.strip()
                master_df['#'] = pd.to_numeric(master_df['#'], errors='coerce')

                merged_df = pd.merge(master_df, df_pivot, on='Description', how='outer')

                # แยกกลุ่มและเรียงลำดับ
                group_a = merged_df[merged_df['#'].notnull()].sort_values(by='#', ascending=True)
                group_b = merged_df[merged_df['#'].isnull()]
                final_df = pd.concat([group_a, group_b], ignore_index=True).fillna(0)

                # Show Stats after processing
                st.divider()
                st.subheader("✅ ตรวจสอบข้อมูลก่อนดาวน์โหลด")
                s1, s2, s3 = st.columns(3)
                s1.success(f"พบข้อมูลการเบิกจาก {len(item_cols)} สาขา")
                s2.info(f"สินค้าในมาสเตอร์: {len(group_a)} รายการ")
                s3.warning(f"สินค้าใหม่ (ต่อท้าย): {len(group_b)} รายการ")

                # Preview Table
                st.dataframe(final_df.head(10), use_container_width=True)

                # Excel Creation
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
                st.balloons()
            except Exception as e:
                st.error(f"❌ เกิดข้อผิดพลาด: {str(e)}")

    if 'ready_file' in st.session_state:
        st.divider()
        st.download_button(
            label="📥 ดาวน์โหลดไฟล์ใบเบิกสินค้า (Excel)",
            data=st.session_state.ready_file,
            file_name="BNN_Final_Order.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

# --- SETTINGS PAGE ---
elif menu == "⚙️ ตั้งค่าระบบ":
    st.title("⚙️ ตั้งค่าระบบ")
    
    with st.tabs(["📝 ข้อมูลหัวใบเบิก", "📦 มาสเตอร์สินค้า & ลำดับ"]):
        with st.tab("📝 ข้อมูลหัวใบเบิก"):
            st.subheader("แก้ไขข้อมูลที่จะไปปรากฏที่หัวไฟล์ Excel")
            col_a, col_b = st.columns(2)
            with col_a:
                st.session_state.header_title = st.text_input("หัวข้อเอกสาร (บรรทัดสีน้ำเงิน)", st.session_state.header_title)
                st.session_state.company_name_th = st.text_input("ชื่อบริษัท (ไทย)", st.session_state.company_name_th)
            with col_b:
                st.session_state.company_name_en = st.text_input("ชื่อบริษัท (English)", st.session_state.company_name_en)
                st.write("")
                if st.button("💾 บันทึกหัวเอกสาร"):
                    st.success("บันทึกสำเร็จ ข้อมูลจะเปลี่ยนในไฟล์ดาวน์โหลดครั้งถัดไป")

        with st.tab("📦 มาสเตอร์สินค้า & ลำดับ"):
            st.subheader("จัดการลำดับ Index (#) และสินค้าหลัก")
            st.info("💡 รายการที่ไม่มีเลขลำดับ (#) ในตารางนี้ จะถูกนำไปต่อท้ายสุดของไฟล์ Excel เสมอ")
            edited_df = st.data_editor(
                pd.DataFrame(st.session_state.master_data), 
                num_rows="dynamic", 
                use_container_width=True
            )
            if st.button("💾 บันทึกรายการมาสเตอร์"):
                st.session_state.master_data = edited_df.to_dict('records')
                st.success("อัปเดตมาสเตอร์สินค้าเรียบร้อย")