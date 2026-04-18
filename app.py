import streamlit as st
import pandas as pd
import re
import io

# --- CONFIG & MODERN DARK THEME ---
st.set_page_config(page_title="BNN | Smart Order", layout="wide")

# CSS สำหรับ Theme มืดแต่สดใส
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Kanit:wght@300;400;500;600&display=swap');
    
    /* พื้นหลังหลักและฟอนต์ */
    html, body, [class*="css"], .main {
        background-color: #0E1117;
        color: #E0E0E0;
        font-family: 'Kanit', sans-serif;
    }

    /* ตกแต่ง Sidebar */
    [data-testid="stSidebar"] {
        background-color: #161B22;
        border-right: 1px solid #30363D;
    }

    /* Metric Cards แบบ Modern Glow */
    div[data-testid="metric-container"] {
        background: #1C2128;
        border: 1px solid #30363D;
        padding: 20px;
        border-radius: 20px;
        box-shadow: 0 10px 20px rgba(0,0,0,0.3);
        transition: 0.3s;
    }
    div[data-testid="metric-container"]:hover {
        border-color: #FF4B91; /* สีชมพูสดใส */
        transform: translateY(-5px);
    }
    
    /* ปรับสีตัวเลขและตัวหนังสือใน Metric ให้ชัดเจน */
    [data-testid="stMetricValue"] {
        color: #00D4FF !important; /* สีฟ้า Neon */
        font-weight: 600 !important;
        font-size: 2.8rem !important;
    }
    [data-testid="stMetricLabel"] {
        color: #FF4B91 !important; /* สีชมพูสดใส */
        font-size: 1rem !important;
        letter-spacing: 1px;
    }

    /* ปุ่มกดสไตล์ Modern Neon */
    div.stButton > button {
        background: linear-gradient(45deg, #FF4B91, #FF7676);
        color: white;
        border: none;
        border-radius: 12px;
        padding: 10px 25px;
        font-weight: 500;
        width: 100%;
        transition: 0.3s ease-in-out;
        box-shadow: 0 4px 15px rgba(255, 75, 145, 0.3);
    }
    div.stButton > button:hover {
        box-shadow: 0 0 25px rgba(255, 75, 145, 0.6);
        transform: scale(1.02);
    }

    /* ตาราง Dataframe */
    [data-testid="stDataFrame"] {
        background-color: #1C2128;
        border-radius: 15px;
    }

    /* ส่วนหัวข้อ */
    h1, h2, h3 {
        background: -webkit-linear-gradient(#00D4FF, #FF4B91);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-weight: 600;
    }
    </style>
    """, unsafe_allow_html=True)

# --- SESSION STATE (DATA) ---
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

if 'h_title' not in st.session_state: st.session_state.h_title = "ใบเบิกสินค้า สาขา"
if 'c_th' not in st.session_state: st.session_state.c_th = "บริษัท บี เอ็น เอ็น เรสเตอรองท์ กรุ๊ป จำกัด"
if 'c_en' not in st.session_state: st.session_state.c_en = "Company BNN RESTAURANT GROUP COMPANY LIMITED"

# --- NAVIGATION ---
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/3063/3063822.png", width=70)
    st.markdown("### BNN Ordering")
    st.divider()
    menu = st.radio("MENU", ["📊 Analytics & Upload", "⚙️ System Config"])
    st.v_spacer(height=20)
    st.info("Version 3.0.0 - Dark Edition")

# --- DASHBOARD PAGE ---
if menu == "📊 Analytics & Upload":
    st.title("ประมวลผลใบเบิกสินค้า")
    
    # Hero Metric Cards
    m1, m2, m3 = st.columns(3)
    with m1:
        st.metric(label="📦 PRODUCT MASTER", value=f"{len(st.session_state.master_data)}")
    with m2:
        st.metric(label="🚛 TRIP CODE STATUS", value="ACTIVE", delta="Ready to Extract")
    with m3:
        st.metric(label="📄 EXPORT FORMAT", value="XLSX")

    st.divider()

    # Functional Zone
    col_up, col_info = st.columns([2, 1])
    with col_up:
        st.markdown("#### 📂 อัปโหลดไฟล์ Raw Data")
        file = st.file_uploader("ลากไฟล์วางที่นี่ (Excel เท่านั้น)", type="xlsx", label_visibility="collapsed")
    
    with col_info:
        st.markdown("#### 💡 คู่มือด่วน")
        st.caption("1. ระบบจะดึงรหัสร้านค้าจากในวงเล็บ (Trip Code)")
        st.caption("2. สินค้าที่เรียงเลข 1-27 จะอยู่ลำดับบนสุด")
        st.caption("3. สินค้าใหม่ที่ไม่อยู่ในมาสเตอร์จะถูกต่อท้ายให้ทันที")

    if file:
        if st.button("✨ เริ่มประมวลผลอัจฉริยะ"):
            try:
                # [Processing Logic เดิม]
                df_raw = pd.read_excel(file)
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
                group_a = merged_df[merged_df['#'].notnull()].sort_values(by='#', ascending=True)
                group_b = merged_df[merged_df['#'].isnull()]
                final_df = pd.concat([group_a, group_b], ignore_index=True).fillna(0)

                # สรุปผล
                st.balloons()
                st.markdown("### ✅ ประมวลผลสำเร็จ!")
                c1, c2, c3 = st.columns(3)
                c1.info(f"🏢 พบสาขา: {len(item_cols)} แห่ง")
                c2.success(f"📦 สินค้ามาสเตอร์: {len(group_a)} รายการ")
                c3.warning(f"🆕 รายการใหม่: {len(group_b)} รายการ")

                st.dataframe(final_df, use_container_width=True)

                # Excel Generator
                output = io.BytesIO()
                with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                    workbook = writer.book
                    sheet = workbook.add_worksheet('ใบเบิก')
                    f_base = {'font_name': 'Cordia New', 'font_size': 14}
                    f_h = workbook.add_format({**f_base, 'bg_color': '#002060', 'font_color': 'white', 'bold': True, 'border': 1, 'align': 'center'})
                    f_g = workbook.add_format({**f_base, 'bg_color': '#D9D9D9', 'border': 1, 'bold': True, 'align': 'center'})
                    f_b = workbook.add_format({**f_base, 'border': 1})
                    f_r = workbook.add_format({**f_base, 'font_size': 11, 'rotation': 45, 'valign': 'bottom', 'align': 'center', 'border': 1})
                    f_t = workbook.add_format({**f_base, 'font_size': 11, 'bg_color': '#FF0000', 'font_color': 'white', 'border': 1, 'align': 'center', 'bold': True})

                    sheet.merge_range('A1:Z1', st.session_state.h_title, f_h)
                    sheet.write('A2', st.session_state.c_th, workbook.add_format(f_base))
                    sheet.write('A3', st.session_state.c_en, workbook.add_format(f_base))

                    for i, h in enumerate(['#', 'Item No.', 'Description', 'UNIT']):
                        sheet.write(5, i, h, f_g)
                        sheet.write(6, i, "", f_b)

                    stores = [c for c in final_df.columns if c not in ['#', 'Item No.', 'Description', 'UNIT']]
                    for i, s in enumerate(stores):
                        col_idx = i + 4
                        sheet.write(5, col_idx, s, f_r)
                        sheet.write(6, col_idx, short_codes.get(s, ""), f_t)
                        sheet.set_column(col_idx, col_idx, 5)

                    for i, row in final_df.iterrows():
                        ri = i + 7
                        sheet.write(ri, 0, int(row['#']) if row['#'] != 0 else "-", f_b)
                        sheet.write(ri, 1, row.get('Item No.', "-") if row.get('Item No.') != 0 else "-", f_b)
                        sheet.write(ri, 2, row['Description'], f_b)
                        sheet.write(ri, 3, row.get('UNIT', "-") if row.get('UNIT') != 0 else "-", f_b)
                        for cj, sn in enumerate(stores):
                            sheet.write(ri, cj+4, row[sn], f_b)
                    
                    sheet.set_column('C:C', 35)
                    sheet.set_column('D:D', 15)

                st.session_state.export_ready = output.getvalue()
            except Exception as e:
                st.error(f"❌ Error: {e}")

    if 'export_ready' in st.session_state:
        st.divider()
        st.download_button("🎁 ดาวน์โหลดไฟล์ใบเบิกสินค้า (.xlsx)", st.session_state.export_ready, "BNN_Smart_Order.xlsx")

# --- SETTINGS PAGE ---
elif menu == "⚙️ System Config":
    st.title("ตั้งค่าระบบ")
    t1, t2 = st.tabs(["Header Setup", "Master Data Management"])
    
    with t1:
        st.markdown("### 📝 ข้อมูลหัวกระดาษ")
        st.session_state.h_title = st.text_input("ชื่อหัวเอกสาร", st.session_state.h_title)
        st.session_state.c_th = st.text_input("ชื่อบริษัท (TH)", st.session_state.c_th)
        st.session_state.c_en = st.text_input("ชื่อบริษัท (EN)", st.session_state.c_en)
        if st.button("💾 บันทึกการเปลี่ยนแปลง"):
            st.success("Config Updated!")

    with t2:
        st.markdown("### 📦 รายการสินค้ามาสเตอร์")
        st.info("ระบุเลข 1-27 เพื่อบังคับลำดับ ส่วนรายการใหม่ที่ไม่อยู่ในตารางนี้จะไปอยู่ล่างสุดเสมอ")
        edited = st.data_editor(pd.DataFrame(st.session_state.master_data), num_rows="dynamic", use_container_width=True)
        if st.button("💾 บันทึกมาสเตอร์"):
            st.session_state.master_data = edited.to_dict('records')
            st.success("Master Data Synchronized!")