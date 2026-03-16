"""
สคริปต์ตรวจสอบ Google Sheets
"""

import gspread
from google.oauth2.service_account import Credentials
import json

print("🔍 ตรวจสอบ Google Sheets")
print("=" * 60)

# โหลด secrets
try:
    with open('.streamlit/secrets.toml', 'r', encoding='utf-8') as f:
        import toml
        secrets = toml.load(f)
except:
    print("❌ ไม่พบไฟล์ secrets.toml")
    input("กด Enter เพื่อออก...")
    exit(1)

# เชื่อมต่อ
print("\n🔗 กำลังเชื่อมต่อ...")

try:
    scope = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive"
    ]
    
    credentials = Credentials.from_service_account_info(
        secrets["gcp_service_account"],
        scopes=scope
    )
    
    client = gspread.authorize(credentials)
    sheet = client.open(secrets["sheet_name"])
    
    print(f"✅ เชื่อมต่อสำเร็จ: {secrets['sheet_name']}")
except Exception as e:
    print(f"❌ เชื่อมต่อไม่สำเร็จ: {e}")
    input("กด Enter เพื่อออก...")
    exit(1)

# ตรวจสอบ Sheets ทั้งหมด
print("\n" + "=" * 60)
print("📋 รายการ Sheets ทั้งหมด:")
print("=" * 60)

worksheets = sheet.worksheets()
print(f"\nพบ {len(worksheets)} sheets:\n")

for i, ws in enumerate(worksheets, 1):
    print(f"{i}. {ws.title} (Rows: {ws.row_count}, Cols: {ws.col_count})")

# ตรวจสอบ Categories
print("\n" + "=" * 60)
print("🏷️ ตรวจสอบ Categories:")
print("=" * 60)

try:
    cat_ws = sheet.worksheet("Categories")
    cat_data = cat_ws.get_all_values()
    
    print(f"✅ พบ Sheet 'Categories'")
    print(f"จำนวนแถว: {len(cat_data)}")
    
    if len(cat_data) > 0:
        print(f"\nHeader: {cat_data[0]}")
        
        if len(cat_data) > 1:
            print(f"\nข้อมูล {len(cat_data) - 1} แถว:")
            for i, row in enumerate(cat_data[1:6], 1):
                print(f"  {i}. {row}")
            
            if len(cat_data) > 6:
                print(f"  ... และอีก {len(cat_data) - 6} แถว")
        else:
            print("\n⚠️ ไม่มีข้อมูล (มีแค่ header)")
    else:
        print("\n❌ Sheet ว่างเปล่า")
        
except Exception as e:
    print(f"❌ ไม่พบ Sheet 'Categories': {e}")

# ตรวจสอบ Brands
print("\n" + "=" * 60)
print("🏢 ตรวจสอบ Brands:")
print("=" * 60)

try:
    brand_ws = sheet.worksheet("Brands")
    brand_data = brand_ws.get_all_values()
    
    print(f"✅ พบ Sheet 'Brands'")
    print(f"จำนวนแถว: {len(brand_data)}")
    
    if len(brand_data) > 0:
        print(f"\nHeader: {brand_data[0]}")
        
        if len(brand_data) > 1:
            print(f"\nข้อมูล {len(brand_data) - 1} แถว:")
            for i, row in enumerate(brand_data[1:6], 1):
                print(f"  {i}. {row}")
            
            if len(brand_data) > 6:
                print(f"  ... และอีก {len(brand_data) - 6} แถว")
        else:
            print("\n⚠️ ไม่มีข้อมูล (มีแค่ header)")
    else:
        print("\n❌ Sheet ว่างเปล่า")
        
except Exception as e:
    print(f"❌ ไม่พบ Sheet 'Brands': {e}")

# ตรวจสอบ Inventory
print("\n" + "=" * 60)
print("📦 ตรวจสอบ Inventory:")
print("=" * 60)

try:
    inv_ws = sheet.worksheet("Inventory")
    inv_data = inv_ws.get_all_values()
    
    print(f"✅ พบ Sheet 'Inventory'")
    print(f"จำนวนแถว: {len(inv_data)}")
    
    if len(inv_data) > 0:
        print(f"\nHeader: {inv_data[0]}")
        
        if len(inv_data) > 1:
            print(f"\nข้อมูล {len(inv_data) - 1} แถว")
        else:
            print("\n⚠️ ไม่มีข้อมูล (มีแค่ header)")
    else:
        print("\n❌ Sheet ว่างเปล่า")
        
except Exception as e:
    print(f"❌ ไม่พบ Sheet 'Inventory': {e}")

# สรุป
print("\n" + "=" * 60)
print("📝 สรุป:")
print("=" * 60)

required_sheets = [
    "Inventory",
    "Categories", 
    "Brands",
    "Measurements_Shirts",
    "Measurements_Pants",
    "Measurements_Shoes",
    "Sales"
]

existing_sheets = [ws.title for ws in worksheets]

print("\nSheets ที่จำเป็น vs มีอยู่:")
for req in required_sheets:
    if req in existing_sheets:
        print(f"  ✅ {req}")
    else:
        print(f"  ❌ {req} (ยังไม่มี)")

print("\n" + "=" * 60)
print("✨ ตรวจสอบเสร็จสิ้น")
print("=" * 60)

input("\nกด Enter เพื่อออก...")
