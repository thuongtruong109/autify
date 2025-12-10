import re
import gspread
from google.oauth2.service_account import Credentials
from typing import Dict, Any, Optional

SPREADSHEET_ID = "16XUax3wefE_jFaVey_ojdIp_qE1GVJ0n0kCOoa7lBpo"
SHEET_RANGE = "A2:E"

def get_sheet_data():
    scopes = [
        "https://www.googleapis.com/auth/spreadsheets.readonly"
    ]

    creds = Credentials.from_service_account_file(
        "service_account.json", scopes=scopes
    )
    client = gspread.authorize(creds)
    sheet = client.open_by_key(SPREADSHEET_ID)
    ws = sheet.sheet1

    values = ws.get(SHEET_RANGE)
    return values

def parse_credentials_from_row(row_data: list) -> Optional[Dict[str, Any]]:
    """
    Parse credentials from a Google Sheet row.
    Format: row[0] = 'email/sometext/password'
    Example: 'ccpnludgdx42059@hotmail.com/kanxghfws25@2020/gunova.site@2020'
    Returns: {'email': 'ccpnludgdx42059@hotmail.com', 'password': 'gunova.site@2020', 'storeId': 'gunova-site'}
    """
    if not row_data or len(row_data) == 0:
        return None

    first_cell = row_data[0]
    parts = re.split(r"[\/|]", first_cell)

    if len(parts) < 3:
        print(f"⚠️ Invalid format in first cell: {first_cell}")
        return None

    email = parts[0].strip()
    password = parts[2].strip()  # Lấy phần thứ 3 (index 2)

    # Extract password trước '@' để tạo storeId
    # gunova.site@2020 -> gunova-site
    if '@' in password:
        store_base = password.split('@')[0]
        store_id = store_base.replace('.', '-').replace('_', '-')
    else:
        store_id = password.replace('.', '-').replace('_', '-')

    domain = password.split('@')[0]

    second_cell = row_data[1]
    third_cell = row_data[2]

    return {
        "email": email,
        "password": password,
        "storeId": store_id,
        "domain": domain,
        "name": second_cell,
        "info": third_cell
    }

def get_credentials_from_sheet(row_index: int = 0) -> Optional[Dict[str, Any]]:
    """
    Get credentials from Google Sheet at specified row index (default: first row = 0)
    """
    try:
        rows = get_sheet_data()
        if not rows or len(rows) == 0:
            print("⚠️ No data found in Google Sheet")
            return None

        if row_index >= len(rows):
            print(f"⚠️ Row index {row_index} out of range. Total rows: {len(rows)}")
            return None

        row_data = rows[row_index]
        credentials = parse_credentials_from_row(row_data)

        if credentials:
            print(f"✅ Loaded credentials from Google Sheet (row {row_index + 1})")
            print(f"   Email: {credentials['email']}")
            print(f"   Store: {credentials['storeId']}")

        return credentials
    except Exception as e:
        print(f"❌ Error loading credentials from Google Sheet: {e}")
        return None

def extract_fullname(name: str):
    parts = name.split()
    firstname = " ".join(parts[:-1])
    lastname = parts[-1]
    return firstname, lastname

def extract_info(info: str):
    info_parts = info.split()
    ssn = info_parts[0]
    birthday = info_parts[1]
    # sex = info_parts[3]

    rest = info.split(info_parts[3])[1].strip()

    address = " ".join(rest.split()[:-1])
    zip = rest.split()[-1]

    return ssn, birthday, address, zip