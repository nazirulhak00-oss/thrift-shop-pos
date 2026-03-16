"""
Thrift Shop POS System v3.0 (Fixed Dynamic Forms)
ระบบจุดขายร้านเสื้อผ้ามือสอง - Multi-Sheet Database Edition
พัฒนาโดย: AI Assistant สำหรับ C
"""

import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
from datetime import datetime, timedelta
import qrcode
from io import BytesIO
import plotly.express as px
import plotly.graph_objects as go

# ===== การตั้งค่าหน้าเว็บ =====
st.set_page_config(
    page_title="Thrift Shop POS v3.0",
    page_icon="👕",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ===== CSS =====
st.markdown("""
<style>
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 20px;
        border-radius: 15px;
        color: white;
        text-align: center;
        box-shadow: 0 8px 16px rgba(0,0,0,0.1);
        transition: transform 0.3s;
    }
    .metric-card:hover {
        transform: translateY(-5px);
    }
    .metric-value {
        font-size: 36px;
        font-weight: bold;
    }
    .success-box {
        padding: 20px;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        border-radius: 15px;
        color: white;
        margin: 10px 0;
    }
    .barcode-display {
        font-family: 'Courier New', monospace;
        font-size: 20px;
        font-weight: bold;
        color: #FF6B6B;
        text-align: center;
        padding: 15px;
        background: #f8f9fa;
        border-radius: 8px;
        margin: 10px 0;
        border: 2px dashed #FF6B6B;
    }
    .measurement-section {
        background: #f0f2f6;
        padding: 20px;
        border-radius: 10px;
        border-left: 4px solid #4ECDC4;
        margin: 15px 0;
    }
</style>
""", unsafe_allow_html=True)

# ===== ฟังก์ชันเชื่อมต่อ =====
@st.cache_resource
def connect_to_sheets():
    try:
        scope = [
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive"
        ]
        credentials = Credentials.from_service_account_info(
            st.secrets["gcp_service_account"],
            scopes=scope
        )
        client = gspread.authorize(credentials)
        sheet = client.open(st.secrets["sheet_name"])
        return sheet
    except Exception as e:
        st.error(f"❌ เชื่อมต่อไม่สำเร็จ: {e}")
        return None

@st.cache_data(ttl=60)
def load_categories(_sheet):
    try:
        worksheet = _sheet.worksheet("Categories")
        data = worksheet.get_all_values()
        if len(data) <= 1:
            return pd.DataFrame()
        df = pd.DataFrame(data[1:], columns=data[0])
        return df
    except Exception as e:
        st.error(f"❌ โหลด Categories ไม่สำเร็จ: {e}")
        return pd.DataFrame()

@st.cache_data(ttl=60)
def load_brands(_sheet):
    try:
        worksheet = _sheet.worksheet("Brands")
        data = worksheet.get_all_values()
        if len(data) <= 1:
            return pd.DataFrame()
        df = pd.DataFrame(data[1:], columns=data[0])
        return df
    except Exception as e:
        st.error(f"❌ โหลด Brands ไม่สำเร็จ: {e}")
        return pd.DataFrame()

def generate_smart_barcode(brand_code, category_code, sheet):
    try:
        worksheet = sheet.worksheet("Inventory")
        all_records = worksheet.get_all_records()
        count = sum(1 for rec in all_records if str(rec.get('Barcode_ID', '')).startswith(f"{brand_code}-{category_code}"))
        number = str(count + 1).zfill(3)
        return f"{brand_code}-{category_code}-{number}"
    except:
        timestamp = datetime.now().strftime("%H%M%S")
        return f"{brand_code}-{category_code}-{timestamp}"

def generate_qr_code(data, size=10):
    qr = qrcode.QRCode(version=1, error_correction=qrcode.constants.ERROR_CORRECT_L, box_size=size, border=4)
    qr.add_data(data)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    buf = BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    return buf

def add_inventory_item(sheet, barcode_id, item_name, brand, category_id, category_name, 
                       size_label, condition, color, pattern, material, cost, price):
    try:
        worksheet = sheet.worksheet("Inventory")
        new_row = [
            barcode_id, item_name, brand, category_id, category_name, size_label,
            condition, color, pattern, material, float(cost), float(price),
            "Available", datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "Admin",
            "", "", "", ""
        ]
        worksheet.append_row(new_row)
        return True
    except Exception as e:
        st.error(f"❌ บันทึกไม่สำเร็จ: {e}")
        return False

def add_measurements(sheet, sheet_name, barcode_id, data_row):
    try:
        worksheet = sheet.worksheet(sheet_name)
        worksheet.append_row(data_row)
        return True
    except Exception as e:
        st.error(f"❌ บันทึกขนาดไม่สำเร็จ: {e}")
        return False

def find_item_by_barcode(sheet, barcode_id):
    try:
        inv_worksheet = sheet.worksheet("Inventory")
        inv_records = inv_worksheet.get_all_records()
        item = None
        for record in inv_records:
            if str(record['Barcode_ID']) == str(barcode_id):
                item = record
                break
        if not item:
            return None
        
        category_id = item.get('Category_ID', '')
        measurements = {}
        
        sheet_map = {
            'CAT-SH': "Measurements_Shirts",
            'CAT-PA': "Measurements_Pants",
            'CAT-FW': "Measurements_Shoes"
        }
        
        if category_id in sheet_map:
            try:
                meas_ws = sheet.worksheet(sheet_map[category_id])
                meas_records = meas_ws.get_all_records()
                for rec in meas_records:
                    if str(rec['Barcode_ID']) == str(barcode_id):
                        measurements = rec
                        break
            except:
                pass
        
        item['measurements'] = measurements
        return item
    except Exception as e:
        st.error(f"❌ ค้นหาไม่สำเร็จ: {e}")
        return None

def record_sale(sheet, barcode_id, original_price, discount_type, discount_value, 
                final_price, payment_method):
    try:
        sale_id = f"SALE-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        discount_amount = original_price - final_price
        
        sales_ws = sheet.worksheet("Sales")
        new_sale = [
            sale_id, barcode_id, datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            float(original_price), discount_type, float(discount_value) if discount_value else 0,
            float(discount_amount), float(final_price), payment_method,
            "", "Admin", f"REC-{datetime.now().strftime('%Y%m%d%H%M%S')}", ""
        ]
        sales_ws.append_row(new_sale)
        
        inv_ws = sheet.worksheet("Inventory")
        cell = inv_ws.find(str(barcode_id))
        if cell:
            inv_ws.update_cell(cell.row, 13, "Sold")
        
        return True
    except Exception as e:
        st.error(f"❌ บันทึกการขายไม่สำเร็จ: {e}")
        return False

def load_all_inventory(sheet):
    try:
        worksheet = sheet.worksheet("Inventory")
        data = worksheet.get_all_records()
        return pd.DataFrame(data)
    except Exception as e:
        st.error(f"❌ โหลดข้อมูลไม่สำเร็จ: {e}")
        return pd.DataFrame()

# ===== MAIN APP =====
def main():
    st.markdown("""
    <div style='text-align: center; padding: 20px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); border-radius: 15px; margin-bottom: 30px;'>
        <h1 style='color: white; margin: 0;'>👕 Thrift Shop POS v3.0</h1>
        <p style='color: white; opacity: 0.9; margin: 5px 0 0 0;'>ระบบจัดการร้านเสื้อผ้ามือสอง - Fixed Dynamic Forms</p>
    </div>
    """, unsafe_allow_html=True)
    
    sheet = connect_to_sheets()
    if sheet is None:
        st.stop()
    
    categories_df = load_categories(sheet)
    brands_df = load_brands(sheet)
    
    with st.sidebar:
        st.markdown("### 📋 เมนู")
        menu = st.radio("", ["🏠 Dashboard", "📦 รับของเข้าสต็อก", "🛒 จุดขายสินค้า", "🔍 ค้นหาสินค้า"], label_visibility="collapsed")
        st.markdown("---")
        if st.button("🔄 Refresh Data", use_container_width=True):
            st.cache_data.clear()
            st.rerun()
        st.markdown("---")
        st.markdown("<div style='text-align: center;'><p style='font-size: 10px;'>v3.0.1</p></div>", unsafe_allow_html=True)
    
    # ===== Dashboard =====
    if menu == "🏠 Dashboard":
        st.header("📊 Dashboard")
        df = load_all_inventory(sheet)
        
        if not df.empty:
            col1, col2, col3, col4 = st.columns(4)
            total = len(df)
            available = len(df[df['Status'] == 'Available'])
            sold = len(df[df['Status'] == 'Sold'])
            
            sold_df = df[df['Status'] == 'Sold'].copy()
            if not sold_df.empty and 'Price' in sold_df.columns and 'Cost' in sold_df.columns:
                sold_df['Price'] = pd.to_numeric(sold_df['Price'], errors='coerce')
                sold_df['Cost'] = pd.to_numeric(sold_df['Cost'], errors='coerce')
                total_profit = (sold_df['Price'] - sold_df['Cost']).sum()
            else:
                total_profit = 0
            
            with col1:
                st.markdown(f'<div class="metric-card"><div class="metric-value">{total}</div><div>📦 สินค้าทั้งหมด</div></div>', unsafe_allow_html=True)
            with col2:
                st.markdown(f'<div class="metric-card" style="background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);"><div class="metric-value">{available}</div><div>✅ คงเหลือ</div></div>', unsafe_allow_html=True)
            with col3:
                st.markdown(f'<div class="metric-card" style="background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);"><div class="metric-value">{sold}</div><div>💰 ขายแล้ว</div></div>', unsafe_allow_html=True)
            with col4:
                st.markdown(f'<div class="metric-card" style="background: linear-gradient(135deg, #43e97b 0%, #38f9d7 100%);"><div class="metric-value">฿{total_profit:,.0f}</div><div>💵 กำไร</div></div>', unsafe_allow_html=True)
            
            st.markdown("---")
            st.subheader("📋 สินค้าคงเหลือ")
            available_df = df[df['Status'] == 'Available']
            if not available_df.empty:
                display_cols = ['Barcode_ID', 'Item_Name', 'Brand', 'Category_Name', 'Size_Label', 'Price']
                available_cols = [col for col in display_cols if col in available_df.columns]
                st.dataframe(available_df[available_cols], width=None, hide_index=True)
            else:
                st.info("📭 ไม่มีสินค้าคงเหลือ")
        else:
            st.warning("⚠️ ยังไม่มีข้อมูล")
    
    # ===== รับของเข้าสต็อก (แก้ไขแล้ว - Dynamic!) =====
    elif menu == "📦 รับของเข้าสต็อก":
        st.header("📦 รับของเข้าสต็อก")
        
        if categories_df.empty or brands_df.empty:
            st.error("❌ ไม่พบข้อมูล Categories หรือ Brands")
            if st.button("🔄 ลองโหลดใหม่"):
                st.cache_data.clear()
                st.rerun()
            st.stop()
        
        # ===== ส่วนที่ 1: เลือกหมวดหมู่ (นอก form เพื่อให้ dynamic) =====
        st.subheader("🏷️ ขั้นตอนที่ 1: เลือกหมวดหมู่")
        
        active_cats = categories_df[categories_df['Active'] == 'Yes']
        cat_options = {f"{row['Category_Icon']} {row['Category_Name']}": row for _, row in active_cats.iterrows()}
        
        selected_cat_display = st.selectbox("หมวดหมู่สินค้า *", list(cat_options.keys()))
        selected_cat = cat_options[selected_cat_display]
        
        category_id = selected_cat['Category_ID']
        category_name = selected_cat['Category_Name']
        category_code = selected_cat['Code_Prefix']
        
        st.markdown("---")
        
        # ===== ส่วนที่ 2: ข้อมูลสินค้า + ขนาด =====
        st.subheader("📝 ขั้นตอนที่ 2: กรอกข้อมูลสินค้า")
        
        col1, col2 = st.columns(2)
        
        with col1:
            active_brands = brands_df[brands_df['Active'] == 'Yes']
            brand_options = active_brands['Brand_Name'].tolist()
            selected_brand_name = st.selectbox("แบรนด์ *", brand_options)
            brand_row = brands_df[brands_df['Brand_Name'] == selected_brand_name].iloc[0]
            brand_code = brand_row['Brand_Code']
            
            item_name = st.text_input("ชื่อสินค้า *", placeholder="เช่น เสื้อยืดสีขาว")
            size_label = st.selectbox("ไซส์ป้าย", ["XS", "S", "M", "L", "XL", "XXL", "Free Size", "ไม่ระบุ"])
        
        with col2:
            condition = st.selectbox("สภาพสินค้า *", [
                "⭐⭐⭐⭐⭐ Like New", "⭐⭐⭐⭐ Excellent",
                "⭐⭐⭐ Good", "⭐⭐ Fair", "⭐ Vintage"
            ])
            color = st.text_input("สี", placeholder="ขาว, ดำ, ลายดอก")
            pattern = st.text_input("ลวดลาย", placeholder="ลายทาง, ลายจุด")
            material = st.text_input("วัสดุ", placeholder="ฝ้าย, โพลีเอสเตอร์")
        
        col3, col4 = st.columns(2)
        with col3:
            cost = st.number_input("ต้นทุน (฿) *", min_value=0.0, step=1.0)
        with col4:
            price = st.number_input("ราคาขาย (฿) *", min_value=0.0, step=1.0)
        
        # ===== ส่วนที่ 3: วัดขนาด (แสดงตามหมวด - Dynamic!) =====
        st.markdown("---")
        st.markdown('<div class="measurement-section">', unsafe_allow_html=True)
        st.subheader(f"📏 ขั้นตอนที่ 3: วัดขนาด{category_name}")
        
        measurements_data = {}
        
        if category_id == 'CAT-SH':  # เสื้อ
            col_m1, col_m2, col_m3, col_m4 = st.columns(4)
            with col_m1:
                measurements_data['chest'] = st.number_input("รอบอก (ซม.)", min_value=0.0, step=0.5, key="chest")
            with col_m2:
                measurements_data['length'] = st.number_input("ความยาว (ซม.)", min_value=0.0, step=0.5, key="length")
            with col_m3:
                measurements_data['sleeve'] = st.number_input("แขน (ซม.)", min_value=0.0, step=0.5, key="sleeve")
            with col_m4:
                measurements_data['shoulder'] = st.number_input("ไหล่ (ซม.)", min_value=0.0, step=0.5, key="shoulder")
            
            col_m5, col_m6 = st.columns(2)
            with col_m5:
                measurements_data['collar_type'] = st.selectbox("ประเภทคอ", ["คอกลม", "คอวี", "คอปก", "คอเต่า", "อื่นๆ"], key="collar")
            with col_m6:
                measurements_data['fit'] = st.selectbox("ทรง", ["Regular", "Slim", "Oversized"], key="fit")
        
        elif category_id == 'CAT-PA':  # กางเกง
            col_m1, col_m2, col_m3 = st.columns(3)
            with col_m1:
                measurements_data['waist'] = st.number_input("รอบเอว (ซม.)", min_value=0.0, step=0.5, key="waist")
            with col_m2:
                measurements_data['hip'] = st.number_input("รอบสะโพก (ซม.)", min_value=0.0, step=0.5, key="hip")
            with col_m3:
                measurements_data['length'] = st.number_input("ความยาว (ซม.)", min_value=0.0, step=0.5, key="length_p")
            
            col_m4, col_m5, col_m6, col_m7 = st.columns(4)
            with col_m4:
                measurements_data['inseam'] = st.number_input("ขาใน (ซม.)", min_value=0.0, step=0.5, key="inseam")
            with col_m5:
                measurements_data['leg_opening'] = st.number_input("ปลายขา (ซม.)", min_value=0.0, step=0.5, key="leg_opening")
            with col_m6:
                measurements_data['rise'] = st.number_input("ความสูงเป้า (ซม.)", min_value=0.0, step=0.5, key="rise")
            with col_m7:
                measurements_data['thigh'] = st.number_input("รอบขาบน (ซม.)", min_value=0.0, step=0.5, key="thigh")
            
            measurements_data['fit'] = st.selectbox("ทรง", ["Skinny", "Regular", "Wide", "Straight"], key="fit_p")
        
        elif category_id == 'CAT-FW':  # รองเท้า
            col_m1, col_m2, col_m3, col_m4 = st.columns(4)
            with col_m1:
                measurements_data['size_us'] = st.text_input("US Size", placeholder="8", key="size_us")
            with col_m2:
                measurements_data['size_eu'] = st.text_input("EU Size", placeholder="41", key="size_eu")
            with col_m3:
                measurements_data['size_uk'] = st.text_input("UK Size", placeholder="7", key="size_uk")
            with col_m4:
                measurements_data['size_jp'] = st.text_input("JP Size (cm)", placeholder="26", key="size_jp")
            
            col_m5, col_m6, col_m7 = st.columns(3)
            with col_m5:
                measurements_data['insole_length'] = st.number_input("พื้นใน (ซม.)", min_value=0.0, step=0.5, key="insole")
            with col_m6:
                measurements_data['width'] = st.selectbox("ความกว้าง", ["Normal", "Wide", "Narrow"], key="width_s")
            with col_m7:
                measurements_data['heel_height'] = st.number_input("ส้นสูง (ซม.)", min_value=0.0, step=0.5, key="heel")
            
            measurements_data['condition_sole'] = st.text_input("สภาพพื้นรองเท้า", placeholder="ดี 90%", key="sole")
        
        else:
            st.info("💡 หมวดหมู่นี้ไม่ต้องวัดขนาด")
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        # แสดงบาร์โค้ด
        if brand_code and category_code:
            preview_barcode = generate_smart_barcode(brand_code, category_code, sheet)
            st.markdown(f'<div class="barcode-display">💡 บาร์โค้ดที่จะสร้าง: {preview_barcode}</div>', unsafe_allow_html=True)
        
        # ปุ่มบันทึก
        st.markdown("---")
        if st.button("✅ บันทึกสินค้า", use_container_width=True, type="primary"):
            if not item_name:
                st.error("❌ กรุณากรอกชื่อสินค้า")
            elif cost <= 0 or price <= 0:
                st.error("❌ ต้นทุนและราคาต้องมากกว่า 0")
            else:
                barcode_id = generate_smart_barcode(brand_code, category_code, sheet)
                
                with st.spinner("กำลังบันทึก..."):
                    success = add_inventory_item(
                        sheet, barcode_id, item_name, selected_brand_name,
                        category_id, category_name, size_label, condition,
                        color, pattern, material, cost, price
                    )
                    
                    if success and measurements_data:
                        if category_id == 'CAT-SH':
                            data_row = [
                                barcode_id,
                                measurements_data.get('chest', 0),
                                measurements_data.get('length', 0),
                                measurements_data.get('sleeve', 0),
                                measurements_data.get('shoulder', 0),
                                measurements_data.get('collar_type', ''),
                                measurements_data.get('fit', ''),
                                datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                            ]
                            add_measurements(sheet, "Measurements_Shirts", barcode_id, data_row)
                        
                        elif category_id == 'CAT-PA':
                            data_row = [
                                barcode_id,
                                measurements_data.get('waist', 0),
                                measurements_data.get('hip', 0),
                                measurements_data.get('length', 0),
                                measurements_data.get('inseam', 0),
                                measurements_data.get('leg_opening', 0),
                                measurements_data.get('rise', 0),
                                measurements_data.get('thigh', 0),
                                measurements_data.get('fit', ''),
                                datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                            ]
                            add_measurements(sheet, "Measurements_Pants", barcode_id, data_row)
                        
                        elif category_id == 'CAT-FW':
                            data_row = [
                                barcode_id,
                                measurements_data.get('size_us', ''),
                                measurements_data.get('size_eu', ''),
                                measurements_data.get('size_uk', ''),
                                measurements_data.get('size_jp', ''),
                                measurements_data.get('insole_length', 0),
                                measurements_data.get('width', ''),
                                measurements_data.get('heel_height', 0),
                                measurements_data.get('condition_sole', ''),
                                datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                            ]
                            add_measurements(sheet, "Measurements_Shoes", barcode_id, data_row)
                
                if success:
                    st.success("✅ บันทึกสำเร็จ!")
                    st.balloons()
                    
                    qr_image = generate_qr_code(barcode_id)
                    col_qr1, col_qr2 = st.columns([1, 2])
                    with col_qr1:
                        st.image(qr_image, width=200)
                    with col_qr2:
                        st.markdown(f"""
                        ### รหัส: {barcode_id}
                        - **สินค้า:** {item_name}
                        - **แบรนด์:** {selected_brand_name}
                        - **หมวด:** {category_name}
                        - **ราคา:** ฿{price:,.2f}
                        """)
                        st.download_button("💾 ดาวน์โหลด QR", qr_image, f"{barcode_id}.png", "image/png")
    
    # ===== จุดขาย =====
    elif menu == "🛒 จุดขายสินค้า":
        st.header("🛒 จุดขายสินค้า")
        barcode_input = st.text_input("🔍 สแกนรหัสสินค้า")
        
        if barcode_input:
            with st.spinner("กำลังค้นหา..."):
                item = find_item_by_barcode(sheet, barcode_input)
            
            if item:
                if item['Status'] == 'Sold':
                    st.error("❌ สินค้าขายไปแล้ว!")
                else:
                    st.success("✅ พบสินค้า!")
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.markdown(f"""
                        ### 📦 ข้อมูลสินค้า
                        - **รหัส:** {item['Barcode_ID']}
                        - **ชื่อ:** {item['Item_Name']}
                        - **แบรนด์:** {item.get('Brand', 'N/A')}
                        - **หมวด:** {item.get('Category_Name', 'N/A')}
                        - **ไซส์:** {item.get('Size_Label', 'N/A')}
                        """)
                        
                        if item.get('measurements'):
                            st.markdown("#### 📏 ขนาดจริง:")
                            meas = item['measurements']
                            for key, value in meas.items():
                                if key not in ['Barcode_ID', 'Updated_Date'] and value:
                                    st.text(f"• {key}: {value}")
                    
                    with col2:
                        price = float(item.get('Price', 0))
                        cost = float(item.get('Cost', 0))
                        st.markdown(f"""
                        ### 💰 ราคา
                        - **ราคาขาย:** ฿{price:,.2f}
                        - **ต้นทุน:** ฿{cost:,.2f}
                        - **กำไร:** ฿{price - cost:,.2f}
                        """)
                    
                    st.markdown("---")
                    st.subheader("🏷️ ส่วนลด")
                    col_d1, col_d2 = st.columns(2)
                    
                    with col_d1:
                        discount_type = st.radio("ประเภท", ["ไม่มี", "เปอร์เซ็นต์ (%)", "บาท (฿)"])
                    
                    with col_d2:
                        if discount_type == "เปอร์เซ็นต์ (%)":
                            discount_value = st.number_input("ส่วนลด (%)", 0.0, 100.0, step=1.0)
                            discount_amount = price * (discount_value / 100)
                        elif discount_type == "บาท (฿)":
                            discount_amount = st.number_input("ส่วนลด (฿)", 0.0, float(price), step=1.0)
                            discount_value = 0
                        else:
                            discount_amount = 0
                            discount_value = 0
                    
                    final_price = price - discount_amount
                    
                    if discount_amount > 0:
                        st.info(f"💵 ราคาหลังหัก: ฿{final_price:,.2f}")
                    
                    payment_method = st.selectbox("💳 วิธีชำระเงิน", ["Cash", "QR Code", "Card"])
                    
                    if st.button("✅ ยืนยันการขาย", use_container_width=True, type="primary"):
                        with st.spinner("กำลังบันทึก..."):
                            success = record_sale(sheet, barcode_input, price, discount_type, discount_value, final_price, payment_method)
                        
                        if success:
                            st.success("🎉 ขายสำเร็จ!")
                            st.balloons()
                            st.markdown(f"""
                            <div class="success-box">
                                <h3 style="text-align: center;">🧾 ใบเสร็จ</h3>
                                <p><strong>สินค้า:</strong> {item['Item_Name']}</p>
                                <p><strong>ราคา:</strong> ฿{price:,.2f}</p>
                                {f"<p><strong>ส่วนลด:</strong> -฿{discount_amount:,.2f}</p>" if discount_amount > 0 else ""}
                                <p style="font-size: 20px;"><strong>ยอดชำระ:</strong> ฿{final_price:,.2f}</p>
                                <p style="text-align: center;">{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</p>
                            </div>
                            """, unsafe_allow_html=True)
                            import time
                            time.sleep(2)
                            st.rerun()
            else:
                st.error("❌ ไม่พบสินค้า")
    
    # ===== ค้นหา =====
    elif menu == "🔍 ค้นหาสินค้า":
        st.header("🔍 ค้นหาสินค้า")
        df = load_all_inventory(sheet)
        
        if not df.empty:
            search_query = st.text_input("🔎 ค้นหา")
            filtered_df = df.copy()
            
            if search_query:
                filtered_df = filtered_df[
                    filtered_df['Item_Name'].str.contains(search_query, case=False, na=False) |
                    filtered_df['Brand'].str.contains(search_query, case=False, na=False) |
                    filtered_df['Barcode_ID'].str.contains(search_query, case=False, na=False)
                ]
            
            st.markdown(f"### 📋 ผลลัพธ์: {len(filtered_df)} รายการ")
            
            if not filtered_df.empty:
                display_cols = ['Barcode_ID', 'Item_Name', 'Brand', 'Category_Name', 'Size_Label', 'Price', 'Status']
                available_cols = [col for col in display_cols if col in filtered_df.columns]
                st.dataframe(filtered_df[available_cols], width=None, hide_index=True)
            else:
                st.info("📭 ไม่พบสินค้า")
        else:
            st.warning("⚠️ ยังไม่มีข้อมูล")

if __name__ == "__main__":
    main()
