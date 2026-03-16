"""
Thrift Shop POS System v2.0
ระบบจุดขายร้านเสื้อผ้ามือสอง - ฉบับอัปเกรด
พัฒนาโดย: AI Assistant สำหรับ C
"""

import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
from datetime import datetime, timedelta
import qrcode
from io import BytesIO
import base64
from PIL import Image, ImageDraw, ImageFont
import plotly.express as px
import plotly.graph_objects as go

# ===== การตั้งค่าหน้าเว็บ =====
st.set_page_config(
    page_title="Thrift Shop POS v2.0",
    page_icon="👕",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ===== ข้อมูลหมวดหมู่และแบรนด์ =====
CATEGORIES = {
    "👕 เสื้อ": "SH",
    "👖 กางเกง": "PA",
    "👗 กระโปรง/เดรส": "SK",
    "👟 รองเท้า": "FW",
    "👜 กระเป๋า": "BA",
    "💍 เครื่องประดับ": "AC",
    "🧥 เสื้อโค้ท": "CT",
    "🎽 เสื้อกีฬา": "SP"
}

BRANDS = [
    "Uniqlo", "Zara", "H&M", "Nike", "Adidas", "Levi's",
    "Forever 21", "Pull&Bear", "Bershka", "COS", "Gap",
    "Mango", "Topshop", "Vintage", "ไม่ระบุแบรนด์"
]

SIZES = ["XS", "S", "M", "L", "XL", "XXL", "Free Size"]

CONDITIONS = {
    "⭐⭐⭐⭐⭐ Like New": 5,
    "⭐⭐⭐⭐ Excellent": 4,
    "⭐⭐⭐ Good": 3,
    "⭐⭐ Fair": 2,
    "⭐ Vintage": 1
}

# ===== CSS สำหรับปรับแต่งหน้าตา =====
st.markdown("""
<style>
    /* Main Theme Colors */
    :root {
        --primary-color: #FF6B6B;
        --secondary-color: #4ECDC4;
        --success-color: #95E1D3;
        --warning-color: #FFE66D;
        --dark-color: #2C3E50;
    }
    
    /* Headers */
    h1, h2, h3 {
        font-family: 'Sarabun', sans-serif;
        color: var(--dark-color);
    }
    
    /* Cards */
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
        box-shadow: 0 12px 24px rgba(0,0,0,0.15);
    }
    
    .metric-value {
        font-size: 36px;
        font-weight: bold;
        font-family: 'Kanit', sans-serif;
    }
    
    .metric-label {
        font-size: 14px;
        opacity: 0.9;
    }
    
    /* Success Box */
    .success-box {
        padding: 20px;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        border-radius: 15px;
        border-left: 5px solid var(--success-color);
        color: white;
        margin: 10px 0;
    }
    
    /* Buttons */
    .stButton>button {
        border-radius: 12px;
        font-weight: 600;
        transition: all 0.3s;
    }
    
    .stButton>button:hover {
        transform: scale(1.02);
        box-shadow: 0 8px 16px rgba(0,0,0,0.2);
    }
    
    /* Tables */
    .dataframe {
        border-radius: 10px;
        overflow: hidden;
    }
    
    /* Warning Box */
    .warning-box {
        padding: 15px;
        background-color: #FFF3CD;
        border-left: 4px solid var(--warning-color);
        border-radius: 8px;
        margin: 10px 0;
    }
    
    /* Sidebar */
    .css-1d391kg {
        background: linear-gradient(180deg, #667eea 0%, #764ba2 100%);
    }
    
    /* Barcode Display */
    .barcode-display {
        font-family: 'Courier New', monospace;
        font-size: 24px;
        font-weight: bold;
        color: var(--primary-color);
        text-align: center;
        padding: 10px;
        background: #f8f9fa;
        border-radius: 8px;
        margin: 10px 0;
    }
</style>
""", unsafe_allow_html=True)

# ===== ฟังก์ชันเชื่อมต่อ Google Sheets =====
@st.cache_resource
def connect_to_sheets():
    """เชื่อมต่อกับ Google Sheets ผ่าน Service Account"""
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
        st.error(f"❌ เชื่อมต่อ Google Sheets ไม่สำเร็จ: {e}")
        return None

# ===== ฟังก์ชันสร้างรหัสบาร์โค้ดอัจฉริยะ =====
def generate_smart_barcode(brand, category_code):
    """
    สร้างรหัสบาร์โค้ดแบบอัจฉริยะ
    รูปแบบ: BRAND-CATEGORY-NUMBER
    เช่น: UNIQLO-SH-001
    """
    # แปลงแบรนด์เป็นตัวพิมพ์ใหญ่และลบช่องว่าง
    brand_code = brand.upper().replace(" ", "").replace("&", "")[:10]
    
    # นับจำนวนสินค้าที่มีแบรนด์และหมวดเดียวกัน
    sheet = connect_to_sheets()
    if sheet:
        try:
            worksheet = sheet.worksheet("Inventory")
            all_records = worksheet.get_all_records()
            
            # หาจำนวนสินค้าที่ตรงกัน
            count = 0
            for record in all_records:
                barcode = str(record.get('Barcode_ID', ''))
                if barcode.startswith(f"{brand_code}-{category_code}"):
                    count += 1
            
            # สร้างเลขลำดับใหม่
            number = str(count + 1).zfill(3)
            return f"{brand_code}-{category_code}-{number}"
            
        except:
            # ถ้าเกิด error ใช้เวลาแทน
            timestamp = datetime.now().strftime("%H%M%S")
            return f"{brand_code}-{category_code}-{timestamp}"
    
    # Fallback: ใช้เวลา
    timestamp = datetime.now().strftime("%H%M%S")
    return f"{brand_code}-{category_code}-{timestamp}"

# ===== ฟังก์ชันสร้าง QR Code =====
def generate_qr_code(data, size=10):
    """สร้าง QR Code จากข้อมูลที่กำหนด"""
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=size,
        border=4,
    )
    qr.add_data(data)
    qr.make(fit=True)
    
    img = qr.make_image(fill_color="black", back_color="white")
    
    buf = BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    return buf

# ===== ฟังก์ชันสร้างป้ายบาร์โค้ด (3 แบบ) =====
def create_barcode_label(barcode_id, item_name, price, size, template="standard"):
    """
    สร้างป้ายบาร์โค้ดแบบต่างๆ
    template: 'small', 'standard', 'premium'
    """
    if template == "small":
        # แบบเล็ก 3x3 cm (113x113 px)
        width, height = 300, 300
        qr_size = 8
    elif template == "premium":
        # แบบหรู 7x4 cm (264x151 px)
        width, height = 700, 400
        qr_size = 12
    else:
        # แบบมาตรฐาน 5x3 cm (189x113 px)
        width, height = 500, 300
        qr_size = 10
    
    # สร้างภาพพื้นหลัง
    img = Image.new('RGB', (width, height), 'white')
    draw = ImageDraw.Draw(img)
    
    # สร้าง QR Code
    qr_img = qrcode.make(barcode_id, box_size=qr_size, border=1)
    qr_img = qr_img.resize((int(height * 0.7), int(height * 0.7)))
    
    # วาง QR Code
    img.paste(qr_img, (10, 10))
    
    # เพิ่มข้อความ (ใช้ default font เนื่องจาก custom font ต้องติดตั้งแยก)
    qr_width = int(height * 0.7) + 20
    
    if template == "small":
        # แบบเล็ก: แค่บาร์โค้ดกับราคา
        draw.text((qr_width, 20), barcode_id[:15], fill='black')
        draw.text((qr_width, 60), f"฿{price}", fill='red')
    elif template == "premium":
        # แบบหรู: เต็มรูปแบบ
        draw.text((qr_width, 20), barcode_id, fill='black')
        draw.text((qr_width, 60), item_name[:20], fill='black')
        draw.text((qr_width, 100), f"Size: {size}", fill='black')
        draw.text((qr_width, 140), f"฿{price}", fill='red')
        draw.text((10, height - 30), "Thrift Shop", fill='gray')
    else:
        # แบบมาตรฐาน
        draw.text((qr_width, 20), barcode_id, fill='black')
        draw.text((qr_width, 60), item_name[:15], fill='black')
        draw.text((qr_width, 100), f"Size: {size}", fill='black')
        draw.text((qr_width, 140), f"฿{price}", fill='red')
    
    # แปลงเป็น BytesIO
    buf = BytesIO()
    img.save(buf, format='PNG')
    buf.seek(0)
    return buf

# ===== ฟังก์ชันบันทึกข้อมูลสินค้า (อัปเกรด) =====
def add_inventory_item(sheet, barcode_id, item_name, brand, category, size, 
                       condition, cost, price, color="", pattern="", material=""):
    """เพิ่มสินค้าใหม่เข้าสู่ Google Sheets (เวอร์ชันอัปเกรด)"""
    try:
        worksheet = sheet.worksheet("Inventory")
        
        # สร้างแถวข้อมูลใหม่
        new_row = [
            barcode_id,
            item_name,
            brand,
            category,
            size,
            condition,
            color,
            pattern,
            material,
            float(cost),
            float(price),
            "Available",
            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            ""  # Sold_Date
        ]
        
        worksheet.append_row(new_row)
        return True
    except Exception as e:
        st.error(f"❌ บันทึกข้อมูลไม่สำเร็จ: {e}")
        return False

# ===== ฟังก์ชันค้นหาสินค้า =====
def find_item_by_barcode(sheet, barcode_id):
    """ค้นหาสินค้าจากรหัสบาร์โค้ด"""
    try:
        worksheet = sheet.worksheet("Inventory")
        all_records = worksheet.get_all_records()
        
        for record in all_records:
            if str(record['Barcode_ID']) == str(barcode_id):
                return record
        
        return None
    except Exception as e:
        st.error(f"❌ ค้นหาข้อมูลไม่สำเร็จ: {e}")
        return None

# ===== ฟังก์ชันอัปเดตสถานะสินค้าเป็น Sold =====
def mark_as_sold(sheet, barcode_id, discount=0):
    """เปลี่ยนสถานะสินค้าจาก Available เป็น Sold"""
    try:
        worksheet = sheet.worksheet("Inventory")
        
        cell = worksheet.find(str(barcode_id))
        
        if cell:
            row_num = cell.row
            
            # อัปเดตสถานะและวันที่ขาย
            worksheet.update_cell(row_num, 12, "Sold")  # Status
            worksheet.update_cell(row_num, 14, datetime.now().strftime("%Y-%m-%d %H:%M:%S"))  # Sold_Date
            
            # บันทึกส่วนลด (ถ้ามี)
            if discount > 0:
                # เพิ่มคอลัมน์ส่วนลดถ้ายังไม่มี
                try:
                    worksheet.update_cell(row_num, 15, float(discount))
                except:
                    pass
            
            return True
        else:
            st.error("❌ ไม่พบรหัสสินค้านี้ในระบบ")
            return False
            
    except Exception as e:
        st.error(f"❌ อัปเดตสถานะไม่สำเร็จ: {e}")
        return False

# ===== ฟังก์ชันโหลดข้อมูลทั้งหมด =====
def load_all_inventory(sheet):
    """โหลดข้อมูลสินค้าทั้งหมดจาก Google Sheets"""
    try:
        worksheet = sheet.worksheet("Inventory")
        data = worksheet.get_all_records()
        df = pd.DataFrame(data)
        return df
    except Exception as e:
        st.error(f"❌ โหลดข้อมูลไม่สำเร็จ: {e}")
        return pd.DataFrame()

# ===== MAIN APP =====
def main():
    # Header
    st.markdown("""
    <div style='text-align: center; padding: 20px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); border-radius: 15px; margin-bottom: 30px;'>
        <h1 style='color: white; margin: 0;'>👕 Thrift Shop POS v2.0</h1>
        <p style='color: white; opacity: 0.9; margin: 5px 0 0 0;'>ระบบจัดการร้านเสื้อผ้ามือสอง - Premium Edition</p>
    </div>
    """, unsafe_allow_html=True)
    
    # เชื่อมต่อ Google Sheets
    sheet = connect_to_sheets()
    
    if sheet is None:
        st.stop()
    
    # สร้าง Sidebar สำหรับเลือกเมนู
    with st.sidebar:
        st.markdown("### 📋 เมนู")
        menu = st.radio(
            "",
            ["🏠 Dashboard", "📦 รับของเข้าสต็อก", "🛒 จุดขายสินค้า (POS)", 
             "🔍 ค้นหาสินค้า", "📊 รายงาน", "🖨️ พิมพ์ป้าย"],
            label_visibility="collapsed"
        )
        
        st.markdown("---")
        st.markdown("""
        <div style='text-align: center; padding: 10px;'>
            <p style='font-size: 12px; color: #666;'>Powered by AI Assistant</p>
            <p style='font-size: 10px; color: #999;'>v2.0.0</p>
        </div>
        """, unsafe_allow_html=True)
    
    # ===== หน้า Dashboard =====
    if menu == "🏠 Dashboard":
        st.header("📊 Dashboard & Analytics")
        
        df = load_all_inventory(sheet)
        
        if not df.empty:
            # Metrics Cards
            col1, col2, col3, col4 = st.columns(4)
            
            total_items = len(df)
            available_items = len(df[df['Status'] == 'Available'])
            sold_items = len(df[df['Status'] == 'Sold'])
            
            # คำนวณกำไร
            sold_df = df[df['Status'] == 'Sold'].copy()
            if not sold_df.empty and 'Price' in sold_df.columns and 'Cost' in sold_df.columns:
                sold_df['Price'] = pd.to_numeric(sold_df['Price'], errors='coerce')
                sold_df['Cost'] = pd.to_numeric(sold_df['Cost'], errors='coerce')
                sold_df['Profit'] = sold_df['Price'] - sold_df['Cost']
                total_profit = sold_df['Profit'].sum()
            else:
                total_profit = 0
            
            with col1:
                st.markdown(f"""
                <div class="metric-card" style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);">
                    <div class="metric-value">{total_items}</div>
                    <div class="metric-label">📦 สินค้าทั้งหมด</div>
                </div>
                """, unsafe_allow_html=True)
            
            with col2:
                st.markdown(f"""
                <div class="metric-card" style="background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);">
                    <div class="metric-value">{available_items}</div>
                    <div class="metric-label">✅ คงเหลือ</div>
                </div>
                """, unsafe_allow_html=True)
            
            with col3:
                st.markdown(f"""
                <div class="metric-card" style="background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);">
                    <div class="metric-value">{sold_items}</div>
                    <div class="metric-label">💰 ขายแล้ว</div>
                </div>
                """, unsafe_allow_html=True)
            
            with col4:
                st.markdown(f"""
                <div class="metric-card" style="background: linear-gradient(135deg, #43e97b 0%, #38f9d7 100%);">
                    <div class="metric-value">฿{total_profit:,.0f}</div>
                    <div class="metric-label">💵 กำไรสะสม</div>
                </div>
                """, unsafe_allow_html=True)
            
            st.markdown("---")
            
            # กราฟ
            col_chart1, col_chart2 = st.columns(2)
            
            with col_chart1:
                st.subheader("📈 ยอดขายรายวัน (7 วันล่าสุด)")
                
                if not sold_df.empty and 'Sold_Date' in sold_df.columns:
                    sold_df['Sold_Date'] = pd.to_datetime(sold_df['Sold_Date'], errors='coerce')
                    sold_df = sold_df.dropna(subset=['Sold_Date'])
                    
                    # กรองข้อมูล 7 วันล่าสุด
                    today = datetime.now()
                    last_7_days = today - timedelta(days=7)
                    recent_sales = sold_df[sold_df['Sold_Date'] >= last_7_days]
                    
                    if not recent_sales.empty:
                        daily_sales = recent_sales.groupby(recent_sales['Sold_Date'].dt.date)['Price'].sum().reset_index()
                        daily_sales.columns = ['Date', 'Sales']
                        
                        fig = px.line(daily_sales, x='Date', y='Sales', 
                                     title='ยอดขายรายวัน',
                                     markers=True)
                        fig.update_traces(line_color='#667eea', line_width=3)
                        fig.update_layout(hovermode='x unified')
                        st.plotly_chart(fig, use_container_width=True)
                    else:
                        st.info("📭 ยังไม่มีข้อมูลการขายใน 7 วันล่าสุด")
                else:
                    st.info("📭 ยังไม่มีข้อมูลการขาย")
            
            with col_chart2:
                st.subheader("🥧 กำไรตามหมวดหมู่")
                
                if not sold_df.empty and 'Category' in sold_df.columns:
                    category_profit = sold_df.groupby('Category')['Profit'].sum().reset_index()
                    category_profit = category_profit[category_profit['Profit'] > 0]
                    
                    if not category_profit.empty:
                        fig = px.pie(category_profit, values='Profit', names='Category',
                                    title='กำไรแยกตามหมวดหมู่',
                                    color_discrete_sequence=px.colors.qualitative.Pastel)
                        st.plotly_chart(fig, use_container_width=True)
                    else:
                        st.info("📭 ยังไม่มีข้อมูลกำไร")
                else:
                    st.info("📭 ยังไม่มีข้อมูลหมวดหมู่")
            
            st.markdown("---")
            
            # Top 5 สินค้าขายดี
            st.subheader("🏆 สินค้าขายดี Top 5")
            
            if not df.empty:
                # นับจำนวนตามแบรนด์และหมวดหมู่
                sold_items_df = df[df['Status'] == 'Sold']
                
                if not sold_items_df.empty and len(sold_items_df) >= 5:
                    top_items = sold_items_df.head(5)[['Barcode_ID', 'Item_Name', 'Brand', 'Price']]
                    st.dataframe(top_items, width=None, hide_index=True)
                else:
                    st.info("📭 ยังมีข้อมูลการขายไม่เพียงพอ")
            
            # สินค้าค้างนาน
            st.subheader("⚠️ สินค้าค้างนาน (>30 วัน)")
            
            if not df.empty and 'Added_Date' in df.columns:
                df['Added_Date'] = pd.to_datetime(df['Added_Date'], errors='coerce')
                df = df.dropna(subset=['Added_Date'])
                
                today = datetime.now()
                df['Days_Old'] = (today - df['Added_Date']).dt.days
                
                old_items = df[(df['Status'] == 'Available') & (df['Days_Old'] > 30)]
                
                if not old_items.empty:
                    old_items['Suggested_Discount'] = old_items['Days_Old'].apply(
                        lambda x: "30%" if x > 60 else ("20%" if x > 45 else "15%")
                    )
                    
                    display_cols = ['Barcode_ID', 'Item_Name', 'Days_Old', 'Price', 'Suggested_Discount']
                    st.dataframe(old_items[display_cols], width=None, hide_index=True)
                else:
                    st.success("✅ ไม่มีสินค้าค้างนาน")
        else:
            st.warning("⚠️ ยังไม่มีข้อมูลในระบบ กรุณาเพิ่มสินค้าก่อน")
    
    # ===== หน้ารับของเข้าสต็อก (อัปเกรด) =====
    elif menu == "📦 รับของเข้าสต็อก":
        st.header("📦 รับของเข้าสต็อก (Smart Edition)")
        
        with st.form("inventory_form_v2", clear_on_submit=True):
            st.subheader("📝 ข้อมูลสินค้า")
            
            col1, col2 = st.columns(2)
            
            with col1:
                category_display = st.selectbox("หมวดหมู่ *", list(CATEGORIES.keys()))
                category = category_display.split(" ", 1)[1] if " " in category_display else category_display
                category_code = CATEGORIES[category_display]
                
                brand = st.selectbox("แบรนด์ *", BRANDS)
                
                # ถ้าเลือก "ไม่ระบุแบรนด์" ให้กรอกเอง
                if brand == "ไม่ระบุแบรนด์":
                    brand = st.text_input("ระบุแบรนด์:", placeholder="เช่น Local Brand")
                
                item_name = st.text_input("ชื่อสินค้า *", placeholder="เช่น เสื้อยืดสีขาว")
                
                size = st.selectbox("ไซส์ *", SIZES)
            
            with col2:
                condition = st.selectbox("สภาพสินค้า *", list(CONDITIONS.keys()))
                
                color = st.text_input("สี", placeholder="เช่น ขาว, ดำ, ลายดอก")
                pattern = st.text_input("ลวดลาย", placeholder="เช่น ลายทาง, ลายจุด")
                material = st.text_input("วัสดุ", placeholder="เช่น ฝ้าย, โพลีเอสเตอร์")
            
            col3, col4 = st.columns(2)
            
            with col3:
                cost = st.number_input("ต้นทุน (฿) *", min_value=0.0, step=1.0, format="%.2f")
            
            with col4:
                price = st.number_input("ราคาขาย (฿) *", min_value=0.0, step=1.0, format="%.2f")
            
            # แสดงบาร์โค้ดที่จะสร้าง
            if brand and category_code:
                preview_barcode = generate_smart_barcode(brand, category_code)
                st.markdown(f"""
                <div class="barcode-display">
                    💡 บาร์โค้ดที่จะสร้าง: {preview_barcode}
                </div>
                """, unsafe_allow_html=True)
            
            submitted = st.form_submit_button("✅ บันทึกและสร้างป้าย", use_container_width=True, type="primary")
            
            if submitted:
                if not item_name or not brand:
                    st.error("❌ กรุณากรอกข้อมูลให้ครบถ้วน")
                elif cost <= 0 or price <= 0:
                    st.error("❌ ต้นทุนและราคาขายต้องมากกว่า 0")
                elif price < cost:
                    st.warning("⚠️ ราคาขายต่ำกว่าต้นทุน คุณจะขาดทุน!")
                else:
                    barcode_id = generate_smart_barcode(brand, category_code)
                    
                    with st.spinner("กำลังบันทึกข้อมูล..."):
                        success = add_inventory_item(
                            sheet, barcode_id, item_name, brand, category,
                            size, condition, cost, price, color, pattern, material
                        )
                    
                    if success:
                        st.success("✅ บันทึกสินค้าสำเร็จ!")
                        st.balloons()
                        
                        # แสดงข้อมูลสินค้า
                        st.markdown(f"""
                        <div class="success-box">
                            <h3>📋 ข้อมูลสินค้า</h3>
                            <p><strong>รหัสสินค้า:</strong> {barcode_id}</p>
                            <p><strong>ชื่อสินค้า:</strong> {item_name}</p>
                            <p><strong>แบรนด์:</strong> {brand} | <strong>หมวด:</strong> {category}</p>
                            <p><strong>ไซส์:</strong> {size} | <strong>สภาพ:</strong> {condition}</p>
                            <p><strong>ต้นทุน:</strong> ฿{cost:.2f} | <strong>ราคาขาย:</strong> ฿{price:.2f}</p>
                            <p><strong>กำไร:</strong> ฿{price - cost:.2f}</p>
                        </div>
                        """, unsafe_allow_html=True)
                        
                        # สร้างและแสดง QR Code + ป้าย
                        st.markdown("---")
                        st.subheader("📱 QR Code และป้ายสินค้า")
                        
                        col_label1, col_label2, col_label3 = st.columns(3)
                        
                        with col_label1:
                            st.markdown("**แบบเล็ก (3x3 cm)**")
                            label_small = create_barcode_label(barcode_id, item_name, price, size, "small")
                            st.image(label_small, width=200)
                            st.download_button(
                                label="💾 ดาวน์โหลด",
                                data=label_small,
                                file_name=f"{barcode_id}_small.png",
                                mime="image/png",
                                use_container_width=True
                            )
                        
                        with col_label2:
                            st.markdown("**แบบมาตรฐาน (5x3 cm)**")
                            label_std = create_barcode_label(barcode_id, item_name, price, size, "standard")
                            st.image(label_std, width=300)
                            st.download_button(
                                label="💾 ดาวน์โหลด",
                                data=label_std,
                                file_name=f"{barcode_id}_standard.png",
                                mime="image/png",
                                use_container_width=True
                            )
                        
                        with col_label3:
                            st.markdown("**แบบหรู (7x4 cm)**")
                            label_premium = create_barcode_label(barcode_id, item_name, price, size, "premium")
                            st.image(label_premium, width=400)
                            st.download_button(
                                label="💾 ดาวน์โหลด",
                                data=label_premium,
                                file_name=f"{barcode_id}_premium.png",
                                mime="image/png",
                                use_container_width=True
                            )
    
    # ===== หน้าจุดขายสินค้า (POS) =====
    elif menu == "🛒 จุดขายสินค้า (POS)":
        st.header("🛒 จุดขายสินค้า (POS)")
        
        barcode_input = st.text_input(
            "🔍 สแกนหรือพิมพ์รหัสสินค้า",
            placeholder="กรอกรหัสแล้วกด Enter",
            key="barcode_scanner_v2"
        )
        
        if barcode_input:
            with st.spinner("กำลังค้นหาสินค้า..."):
                item = find_item_by_barcode(sheet, barcode_input)
            
            if item:
                if item['Status'] == 'Sold':
                    st.error("❌ สินค้านี้ถูกขายไปแล้ว!")
                    if 'Sold_Date' in item:
                        st.info(f"📅 ขายเมื่อ: {item['Sold_Date']}")
                else:
                    st.success("✅ พบสินค้าในระบบ!")
                    
                    col_item1, col_item2 = st.columns(2)
                    
                    with col_item1:
                        st.markdown(f"""
                        ### 📦 ข้อมูลสินค้า
                        - **รหัส:** {item['Barcode_ID']}
                        - **ชื่อ:** {item['Item_Name']}
                        - **แบรนด์:** {item.get('Brand', 'N/A')}
                        - **หมวด:** {item.get('Category', 'N/A')}
                        - **ไซส์:** {item.get('Size', 'N/A')}
                        - **สภาพ:** {item.get('Condition', 'N/A')}
                        """)
                    
                    with col_item2:
                        price = float(item.get('Price', 0))
                        cost = float(item.get('Cost', 0))
                        profit = price - cost
                        
                        st.markdown(f"""
                        ### 💰 ข้อมูลราคา
                        - **ราคาขาย:** ฿{price:,.2f}
                        - **ต้นทุน:** ฿{cost:,.2f}
                        - **กำไร:** ฿{profit:,.2f}
                        """)
                    
                    st.markdown("---")
                    
                    # ส่วนลด
                    st.subheader("🏷️ ส่วนลด (ถ้ามี)")
                    col_dis1, col_dis2 = st.columns(2)
                    
                    with col_dis1:
                        discount_type = st.radio("ประเภทส่วนลด", ["ไม่มี", "เปอร์เซ็นต์ (%)", "บาท (฿)"])
                    
                    with col_dis2:
                        if discount_type == "เปอร์เซ็นต์ (%)":
                            discount_value = st.number_input("ส่วนลด (%)", min_value=0.0, max_value=100.0, step=1.0)
                            discount_amount = price * (discount_value / 100)
                        elif discount_type == "บาท (฿)":
                            discount_amount = st.number_input("ส่วนลด (฿)", min_value=0.0, max_value=float(price), step=1.0)
                        else:
                            discount_amount = 0
                    
                    final_price = price - discount_amount
                    
                    if discount_amount > 0:
                        st.info(f"💵 ราคาหลังหัก: ฿{final_price:,.2f} (ลด ฿{discount_amount:,.2f})")
                    
                    st.markdown("---")
                    
                    # ปุ่มยืนยันการขาย
                    col_btn1, col_btn2, col_btn3 = st.columns([1, 1, 1])
                    
                    with col_btn2:
                        if st.button("✅ ยืนยันการขาย", use_container_width=True, type="primary"):
                            with st.spinner("กำลังบันทึกการขาย..."):
                                success = mark_as_sold(sheet, barcode_input, discount_amount)
                            
                            if success:
                                st.success("🎉 ขายสินค้าสำเร็จ!")
                                st.balloons()
                                
                                # แสดงใบเสร็จ
                                st.markdown(f"""
                                <div class="success-box">
                                    <h3 style="text-align: center;">🧾 ใบเสร็จรับเงิน</h3>
                                    <p style="text-align: center;">Thrift Shop POS</p>
                                    <hr>
                                    <p><strong>สินค้า:</strong> {item['Item_Name']}</p>
                                    <p><strong>แบรนด์:</strong> {item.get('Brand', 'N/A')} ({item.get('Size', 'N/A')})</p>
                                    <p><strong>ราคา:</strong> ฿{price:,.2f}</p>
                                    {f"<p><strong>ส่วนลด:</strong> -฿{discount_amount:,.2f}</p>" if discount_amount > 0 else ""}
                                    <p style="font-size: 20px;"><strong>ยอดชำระ:</strong> ฿{final_price:,.2f}</p>
                                    <hr>
                                    <p style="text-align: center;"><strong>ขอบคุณที่ใช้บริการ!</strong></p>
                                    <p style="text-align: center; font-size: 12px;">{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</p>
                                </div>
                                """, unsafe_allow_html=True)
                                
                                # Confetti effect (แทน balloons)
                                import time
                                time.sleep(2)
                                st.rerun()
            else:
                st.error("❌ ไม่พบรหัสสินค้านี้ในระบบ")
                st.info("💡 กรุณาตรวจสอบรหัสอีกครั้งหรือเพิ่มสินค้าในหน้า 'รับของเข้าสต็อก'")
    
    # ===== หน้าค้นหาสินค้า (ใหม่!) =====
    elif menu == "🔍 ค้นหาสินค้า":
        st.header("🔍 ค้นหาสินค้าขั้นสูง")
        
        df = load_all_inventory(sheet)
        
        if not df.empty:
            col_search1, col_search2 = st.columns([2, 1])
            
            with col_search1:
                search_query = st.text_input("🔎 ค้นหา", placeholder="ชื่อสินค้า, แบรนด์, รหัส...")
            
            with col_search2:
                search_status = st.selectbox("สถานะ", ["ทั้งหมด", "Available", "Sold"])
            
            # ฟิลเตอร์ขั้นสูง
            with st.expander("🎛️ ฟิลเตอร์ขั้นสูง"):
                col_f1, col_f2, col_f3 = st.columns(3)
                
                with col_f1:
                    if 'Brand' in df.columns:
                        brands_list = ["ทั้งหมด"] + sorted(df['Brand'].unique().tolist())
                        filter_brand = st.selectbox("แบรนด์", brands_list)
                    else:
                        filter_brand = "ทั้งหมด"
                
                with col_f2:
                    if 'Category' in df.columns:
                        categories_list = ["ทั้งหมด"] + sorted(df['Category'].unique().tolist())
                        filter_category = st.selectbox("หมวดหมู่", categories_list)
                    else:
                        filter_category = "ทั้งหมด"
                
                with col_f3:
                    if 'Size' in df.columns:
                        sizes_list = ["ทั้งหมด"] + sorted(df['Size'].unique().tolist())
                        filter_size = st.selectbox("ไซส์", sizes_list)
                    else:
                        filter_size = "ทั้งหมด"
                
                col_f4, col_f5 = st.columns(2)
                
                with col_f4:
                    price_min = st.number_input("ราคาต่ำสุด (฿)", min_value=0.0, value=0.0)
                
                with col_f5:
                    price_max = st.number_input("ราคาสูงสุด (฿)", min_value=0.0, value=10000.0)
            
            # ใช้ฟิลเตอร์
            filtered_df = df.copy()
            
            if search_query:
                filtered_df = filtered_df[
                    filtered_df['Item_Name'].str.contains(search_query, case=False, na=False) |
                    filtered_df['Brand'].str.contains(search_query, case=False, na=False) |
                    filtered_df['Barcode_ID'].str.contains(search_query, case=False, na=False)
                ]
            
            if search_status != "ทั้งหมด":
                filtered_df = filtered_df[filtered_df['Status'] == search_status]
            
            if filter_brand != "ทั้งหมด":
                filtered_df = filtered_df[filtered_df['Brand'] == filter_brand]
            
            if filter_category != "ทั้งหมด":
                filtered_df = filtered_df[filtered_df['Category'] == filter_category]
            
            if filter_size != "ทั้งหมด":
                filtered_df = filtered_df[filtered_df['Size'] == filter_size]
            
            if 'Price' in filtered_df.columns:
                filtered_df['Price'] = pd.to_numeric(filtered_df['Price'], errors='coerce')
                filtered_df = filtered_df[
                    (filtered_df['Price'] >= price_min) & 
                    (filtered_df['Price'] <= price_max)
                ]
            
            # แสดงผลลัพธ์
            st.markdown(f"### 📋 ผลการค้นหา: {len(filtered_df)} รายการ")
            
            if not filtered_df.empty:
                # เลือกคอลัมน์ที่จะแสดง
                display_cols = ['Barcode_ID', 'Item_Name', 'Brand', 'Category', 
                               'Size', 'Price', 'Status']
                available_cols = [col for col in display_cols if col in filtered_df.columns]
                
                st.dataframe(filtered_df[available_cols], width=None, hide_index=True)
            else:
                st.info("📭 ไม่พบสินค้าที่ตรงกับเงื่อนไข")
        else:
            st.warning("⚠️ ยังไม่มีข้อมูลในระบบ")
    
    # ===== หน้ารายงาน (ใหม่!) =====
    elif menu == "📊 รายงาน":
        st.header("📈 รายงานและส่งออกข้อมูล")
        
        df = load_all_inventory(sheet)
        
        if not df.empty:
            # เลือกช่วงเวลา
            col_date1, col_date2 = st.columns(2)
            
            with col_date1:
                start_date = st.date_input("จากวันที่", value=datetime.now() - timedelta(days=30))
            
            with col_date2:
                end_date = st.date_input("ถึงวันที่", value=datetime.now())
            
            # ประเภทรายงาน
            st.subheader("📊 ประเภทรายงาน")
            
            report_type = st.selectbox(
                "เลือกรายงาน",
                ["🧾 รายงานการขาย", "📦 รายงานสต็อก", "💰 รายงานกำไร-ขาดทุน", "🏆 สินค้าขายดี/ขายไม่ดี"]
            )
            
            if report_type == "🧾 รายงานการขาย":
                sold_df = df[df['Status'] == 'Sold'].copy()
                
                if not sold_df.empty and 'Sold_Date' in sold_df.columns:
                    sold_df['Sold_Date'] = pd.to_datetime(sold_df['Sold_Date'], errors='coerce')
                    sold_df = sold_df.dropna(subset=['Sold_Date'])
                    
                    # กรองตามช่วงวันที่
                    mask = (sold_df['Sold_Date'].dt.date >= start_date) & (sold_df['Sold_Date'].dt.date <= end_date)
                    filtered_sold = sold_df[mask]
                    
                    st.markdown(f"### รายการขายระหว่าง {start_date} - {end_date}")
                    st.markdown(f"**จำนวน:** {len(filtered_sold)} รายการ")
                    
                    if not filtered_sold.empty:
                        display_cols = ['Barcode_ID', 'Item_Name', 'Brand', 'Price', 'Sold_Date']
                        available_cols = [col for col in display_cols if col in filtered_sold.columns]
                        st.dataframe(filtered_sold[available_cols], width=None, hide_index=True)
                        
                        # ส่งออก CSV
                        csv = filtered_sold.to_csv(index=False).encode('utf-8-sig')
                        st.download_button(
                            label="📥 ดาวน์โหลด CSV",
                            data=csv,
                            file_name=f"sales_report_{start_date}_{end_date}.csv",
                            mime="text/csv"
                        )
                    else:
                        st.info("📭 ไม่มีข้อมูลการขายในช่วงเวลานี้")
                else:
                    st.info("📭 ยังไม่มีข้อมูลการขาย")
            
            elif report_type == "📦 รายงานสต็อก":
                available_df = df[df['Status'] == 'Available']
                
                st.markdown(f"### สินค้าคงเหลือทั้งหมด: {len(available_df)} ชิ้น")
                
                if not available_df.empty:
                    # คำนวณมูลค่าสต็อก
                    if 'Cost' in available_df.columns:
                        available_df['Cost'] = pd.to_numeric(available_df['Cost'], errors='coerce')
                        total_value = available_df['Cost'].sum()
                        st.metric("💰 มูลค่าสต็อกรวม", f"฿{total_value:,.2f}")
                    
                    display_cols = ['Barcode_ID', 'Item_Name', 'Brand', 'Category', 'Size', 'Cost', 'Price']
                    available_cols = [col for col in display_cols if col in available_df.columns]
                    st.dataframe(available_df[available_cols], width=None, hide_index=True)
                    
                    # ส่งออก CSV
                    csv = available_df.to_csv(index=False).encode('utf-8-sig')
                    st.download_button(
                        label="📥 ดาวน์โหลด CSV",
                        data=csv,
                        file_name=f"inventory_report_{datetime.now().strftime('%Y%m%d')}.csv",
                        mime="text/csv"
                    )
                else:
                    st.info("📭 ไม่มีสินค้าคงเหลือ")
            
            elif report_type == "💰 รายงานกำไร-ขาดทุน":
                sold_df = df[df['Status'] == 'Sold'].copy()
                
                if not sold_df.empty and 'Price' in sold_df.columns and 'Cost' in sold_df.columns:
                    sold_df['Price'] = pd.to_numeric(sold_df['Price'], errors='coerce')
                    sold_df['Cost'] = pd.to_numeric(sold_df['Cost'], errors='coerce')
                    sold_df['Profit'] = sold_df['Price'] - sold_df['Cost']
                    
                    total_revenue = sold_df['Price'].sum()
                    total_cost = sold_df['Cost'].sum()
                    total_profit = sold_df['Profit'].sum()
                    
                    col_p1, col_p2, col_p3 = st.columns(3)
                    
                    with col_p1:
                        st.metric("📈 รายได้รวม", f"฿{total_revenue:,.2f}")
                    
                    with col_p2:
                        st.metric("📉 ต้นทุนรวม", f"฿{total_cost:,.2f}")
                    
                    with col_p3:
                        st.metric("💰 กำไรสุทธิ", f"฿{total_profit:,.2f}")
                    
                    # รายละเอียด
                    display_cols = ['Barcode_ID', 'Item_Name', 'Cost', 'Price', 'Profit']
                    st.dataframe(sold_df[display_cols], width=None, hide_index=True)
                    
                    # ส่งออก CSV
                    csv = sold_df.to_csv(index=False).encode('utf-8-sig')
                    st.download_button(
                        label="📥 ดาวน์โหลด CSV",
                        data=csv,
                        file_name=f"profit_loss_report_{datetime.now().strftime('%Y%m%d')}.csv",
                        mime="text/csv"
                    )
                else:
                    st.info("📭 ยังไม่มีข้อมูลการขาย")
            
            elif report_type == "🏆 สินค้าขายดี/ขายไม่ดี":
                col_top1, col_top2 = st.columns(2)
                
                with col_top1:
                    st.subheader("🏆 Top 10 สินค้าขายดี")
                    sold_df = df[df['Status'] == 'Sold']
                    
                    if not sold_df.empty and len(sold_df) >= 10:
                        top_10 = sold_df.head(10)[['Barcode_ID', 'Item_Name', 'Brand', 'Price']]
                        st.dataframe(top_10, width=None, hide_index=True)
                    else:
                        st.info("📭 ข้อมูลยังไม่เพียงพอ")
                
                with col_top2:
                    st.subheader("📦 สินค้าค้างนาน")
                    
                    if 'Added_Date' in df.columns:
                        df['Added_Date'] = pd.to_datetime(df['Added_Date'], errors='coerce')
                        df = df.dropna(subset=['Added_Date'])
                        
                        today = datetime.now()
                        df['Days_Old'] = (today - df['Added_Date']).dt.days
                        
                        old_items = df[(df['Status'] == 'Available') & (df['Days_Old'] > 30)]
                        old_items = old_items.sort_values('Days_Old', ascending=False)
                        
                        if not old_items.empty:
                            display_cols = ['Barcode_ID', 'Item_Name', 'Days_Old', 'Price']
                            st.dataframe(old_items.head(10)[display_cols], width=None, hide_index=True)
                        else:
                            st.success("✅ ไม่มีสินค้าค้างนาน")
        else:
            st.warning("⚠️ ยังไม่มีข้อมูลในระบบ")
    
    # ===== หน้าพิมพ์ป้าย (ใหม่!) =====
    elif menu == "🖨️ พิมพ์ป้าย":
        st.header("🖨️ พิมพ์ป้ายบาร์โค้ดแบบชุด")
        
        df = load_all_inventory(sheet)
        
        if not df.empty:
            # เลือกเทมเพลต
            st.subheader("📋 เลือกเทมเพลตป้าย")
            
            col_temp1, col_temp2, col_temp3 = st.columns(3)
            
            with col_temp1:
                if st.button("แบบเล็ก (3x3 cm)", use_container_width=True):
                    st.session_state['label_template'] = 'small'
            
            with col_temp2:
                if st.button("แบบมาตรฐาน (5x3 cm)", use_container_width=True):
                    st.session_state['label_template'] = 'standard'
            
            with col_temp3:
                if st.button("แบบหรู (7x4 cm)", use_container_width=True):
                    st.session_state['label_template'] = 'premium'
            
            template = st.session_state.get('label_template', 'standard')
            st.info(f"📌 เทมเพลตปัจจุบัน: **{template}**")
            
            st.markdown("---")
            
            # เลือกสินค้า
            st.subheader("📦 เลือกสินค้าที่จะพิมพ์")
            
            # ฟิลเตอร์เฉพาะสินค้าที่ Available
            available_df = df[df['Status'] == 'Available'].copy()
            
            if not available_df.empty:
                # เลือกทั้งหมด
                select_all = st.checkbox("☑ เลือกทั้งหมด")
                
                if select_all:
                    selected_items = available_df['Barcode_ID'].tolist()
                else:
                    # แสดงรายการให้เลือก
                    selected_items = st.multiselect(
                        "เลือกสินค้า",
                        options=available_df['Barcode_ID'].tolist(),
                        format_func=lambda x: f"{x} | {available_df[available_df['Barcode_ID']==x]['Item_Name'].values[0]} | ฿{available_df[available_df['Barcode_ID']==x]['Price'].values[0]}"
                    )
                
                st.info(f"🏷️ เลือกแล้ว: {len(selected_items)} รายการ")
                
                if selected_items:
                    if st.button("🖨️ สร้างไฟล์พิมพ์", use_container_width=True, type="primary"):
                        st.success(f"✅ กำลังสร้างป้าย {len(selected_items)} ป้าย...")
                        
                        # สร้างป้ายทีละอัน
                        for barcode in selected_items[:3]:  # แสดงตัวอย่าง 3 อันแรก
                            item_data = available_df[available_df['Barcode_ID'] == barcode].iloc[0]
                            
                            label_img = create_barcode_label(
                                barcode,
                                item_data['Item_Name'],
                                item_data['Price'],
                                item_data.get('Size', 'N/A'),
                                template
                            )
                            
                            col_preview1, col_preview2 = st.columns([1, 2])
                            
                            with col_preview1:
                                st.image(label_img, width=300)
                            
                            with col_preview2:
                                st.markdown(f"""
                                **{barcode}**  
                                {item_data['Item_Name']}  
                                ฿{item_data['Price']}
                                """)
                                
                                st.download_button(
                                    label=f"💾 ดาวน์โหลด {barcode}",
                                    data=label_img,
                                    file_name=f"{barcode}_{template}.png",
                                    mime="image/png",
                                    key=f"download_{barcode}"
                                )
                        
                        if len(selected_items) > 3:
                            st.info(f"💡 แสดงตัวอย่าง 3 ป้ายแรก (รวม {len(selected_items)} ป้าย)")
            else:
                st.warning("⚠️ ไม่มีสินค้าคงเหลือในสต็อก")
        else:
            st.warning("⚠️ ยังไม่มีข้อมูลในระบบ")

# ===== เรียกใช้แอป =====
if __name__ == "__main__":
    main()
