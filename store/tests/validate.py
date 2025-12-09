import re

def extract_generic_patterns(text: str):
    pattern = re.compile(
        r"""
        (?P<number>(?:\D*\d{4}){4})
        .*?
        (?P<expired>\d{2}/\d{2})
        .*?
        (?P<cvc>\d{3})
        """,
        re.VERBOSE | re.DOTALL
    )

    match = pattern.search(text)
    if not match:
        return {
            "number": None,
            "expired": None,
            "cvc": None,
        }

    raw_blocks = match.group("number")
    blocks_cleaned = re.findall(r"\d{4}", raw_blocks)
    blocks_joined = "".join(blocks_cleaned) if len(blocks_cleaned) == 4 else None

    return {
        "number": blocks_joined,
        "expired": match.group("expired"),
        "cvc": match.group("cvc"),
    }

text = """5342 7110 7781 0057
Exp
Click to copy12/31
Extra text
Code here -> 468
"""

result = extract_generic_patterns(text)
print(result)

# ----------------------------------------
def extract_name(full_name: str):
    parts = full_name.strip().split()

    if len(parts) < 2:
        # Nếu chỉ có 1 từ, coi là last name trống
        return {"first_name": parts[0], "last_name": ""}

    # Last name là từ cuối cùng
    last_name = parts[-1]
    # First name là phần còn lại
    first_name = " ".join(parts[:-1])

    return {"first_name": first_name, "last_name": last_name}

full_name = "KIMBERLY        A        HENDERSON"
result = extract_name(full_name)
print(result)

# ----------------------------------------
def extract_account(text: str):
    # Tách theo cả / và |
    parts = re.split(r"[\/|]", text.strip())

    if len(parts) != 3:
        raise ValueError("Chuỗi không đúng định dạng 3 phần ngăn cách bởi '/' hoặc '|'")

    hotmail_id = parts[0]
    hotmail_password = parts[1]
    shopify_password = parts[2]

    if "@" in shopify_password:
        domain = shopify_password.split("@")[0]
    else:
        domain = None

    return {
        "hotmail_id": hotmail_id,
        "hotmail_password": hotmail_password,
        "shopify_password": shopify_password,
        "domain": domain
    }

text1 = "example@hotmail.com/password@2043/domain@2043"
text2 = "example@hotmail.com|password@2043|domain@2043"
text3 = "example@hotmail.com/password@2043|domain@2043"

print(extract_account(text1))
print(extract_account(text2))
print(extract_account(text3))

# ----------------------------------------
def extract_info(text: str):
    clean = " ".join(text.split())
    pattern = re.compile(
        r"""
        (?P<ssn>\d{9})\s+
        (?P<birthday>\d{1,2}/\d{1,2}/\d{4})
        (?:\s+\d{1,2}:\d{2}:\d{2})?
        \s+
        (?P<gender>[A-Za-z])\s+
        (?P<address>.+?)\s+
        (?P<zip>\d{5})
        """,
        re.VERBOSE,
    )

    m = pattern.search(clean)
    return m.groupdict() if m else None

demo = """
123456789   6/21/1968 0:00:00   F
1172 E BROADWAY UNIT 136   LOUISVILLE   KY   40204
"""

result = extract_info(demo)
print(result)
