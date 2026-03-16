"""
สคริปต์ทดสอบก่อนรันแอป
ตรวจสอบว่าทุกอย่างพร้อมหรือยัง
"""

import sys

print("🔍 ตรวจสอบความพร้อมในการรันแอป")
print("=" * 60)

# 1. ตรวจสอบ Python version
print("\n1. Python Version:")
print(f"   ✅ {sys.version}")

# 2. ตรวจสอบ Libraries
print("\n2. ตรวจสอบ Libraries:")

required_libs = [
    'streamlit',
    'gspread',
    'google.oauth2.service_account',
    'pandas',
    'qrcode',
    'PIL',
    'plotly'
]

missing_libs = []

for lib in required_libs:
    try:
        if lib == 'google.oauth2.service_account':
            __import__('google.oauth2.service_account', fromlist=['Credentials'])
        elif lib == 'PIL':
            __import__('PIL')
        else:
            __import__(lib)
        print(f"   ✅ {lib}")
    except ImportError:
        print(f"   ❌ {lib} (ไม่พบ)")
        missing_libs.append(lib)

if missing_libs:
    print("\n⚠️ ต้องติดตั้ง libraries ที่ขาดหายไป:")
    print(f"   pip install {' '.join(missing_libs)}")
else:
    print("\n✅ Libraries ครบถ้วน!")

# 3. ตรวจสอบไฟล์สำคัญ
print("\n3. ตรวจสอบไฟล์:")

import os

files_to_check = [
    'app.py',
    '.streamlit/secrets.toml',
    'requirements.txt'
]

for file_path in files_to_check:
    if os.path.exists(file_path):
        size = os.path.getsize(file_path)
        print(f"   ✅ {file_path} ({size:,} bytes)")
    else:
        print(f"   ❌ {file_path} (ไม่พบ)")

# 4. ทดสอบเชื่อมต่อ Google Sheets
print("\n4. ทดสอบเชื่อมต่อ Google Sheets:")

if not os.path.exists('.streamlit/secrets.toml'):
    print("   ❌ ไม่พบ secrets.toml")
    print("   💡 รัน: 1-Setup-Secrets.bat")
else:
    try:
        import toml
        secrets = toml.load('.streamlit/secrets.toml')
        
        if 'gcp_service_account' in secrets and 'sheet_name' in secrets:
            print("   ✅ พบ secrets.toml")
            print(f"   📊 Sheet: {secrets['sheet_name']}")
            
            # ทดสอบเชื่อมต่อ
            try:
                import gspread
                from google.oauth2.service_account import Credentials
                
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
                
                print("   ✅ เชื่อมต่อ Google Sheets สำเร็จ!")
                
                # แสดง Sheets ที่มี
                worksheets = sheet.worksheets()
                print(f"\n   📋 พบ {len(worksheets)} sheets:")
                for ws in worksheets[:5]:
                    print(f"      • {ws.title}")
                if len(worksheets) > 5:
                    print(f"      ... และอีก {len(worksheets) - 5} sheets")
                
            except Exception as e:
                print(f"   ❌ เชื่อมต่อไม่สำเร็จ: {e}")
        else:
            print("   ❌ secrets.toml ไม่ครบถ้วน")
    except Exception as e:
        print(f"   ❌ อ่าน secrets.toml ไม่สำเร็จ: {e}")

# สรุป
print("\n" + "=" * 60)

if missing_libs:
    print("⚠️ ยังไม่พร้อม - ต้องติดตั้ง libraries ที่ขาดหายก่อน")
    print(f"   รัน: pip install {' '.join(missing_libs)}")
elif not os.path.exists('.streamlit/secrets.toml'):
    print("⚠️ ยังไม่พร้อม - ต้องสร้าง secrets.toml")
    print("   รัน: 1-Setup-Secrets.bat")
else:
    print("✅ พร้อมรันแอปแล้ว!")
    print("\n🚀 วิธีรัน:")
    print("   • Windows: ดับเบิลคลิก 6-Run-Local.bat")
    print("   • หรือพิมพ์: streamlit run app.py")

print("\n" + "=" * 60)

input("\nกด Enter เพื่อออก...")
