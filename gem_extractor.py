import os
import re
import pypdf
from typing import Dict, List, Any
# Import the database function from your manager script
from gem_db_manager import save_extracted_to_dump

# ==============================================================================
# CONFIGURATION
# ==============================================================================

# This points to the folder where GeM_Automation.py downloads the PDFs
BASE_DIR = os.path.join(os.getcwd(), "gem_bids", "Split_Air_Conditioner")

TARGET_STATES = [
    "Tamil Nadu", "Kerala", "Karnataka", "Telangana", "Andhra Pradesh", 
    "Maharashtra", "Mumbai", "Goa", "Gujarat", "Puducherry", "Dadra", "Daman"
]

# ==============================================================================
# EXTRACTION LOGIC (AC & FRIDGE)
# ==============================================================================

def extract_fridge_details(block: str) -> str:
    tech = "Frost-free" if re.search(r"Frost\s*-?\s*free", block, re.I) else "Direct Cool" if re.search(r"Direct\s*Cool", block, re.I) else ""
    volume = ""
    vol_match = re.search(r"Total\s*Volume\s*.*?[:\-\s]+([\d\s\-]+)", block, re.I)
    if vol_match: volume = f"{vol_match.group(1).strip()}L"
    
    star = ""
    star_match = re.search(r"BEE\s*Star\s*Rating\s*[:\-]?\s*(\d)", block, re.I)
    if star_match: star = f"{star_match.group(1)} Star"

    if tech:
        return f"Fridge {tech} {volume} {star}".strip()
    return "BOQ"

def extract_ac_details(block: str) -> str:
    ton_match = re.search(r"Nominal\s*Capacity.*?Ton\)\s*[:\-]?\s*([^\n\r]+)", block, re.I)
    tonnage = ton_match.group(1).strip() if ton_match else ""
    star_match = re.search(r"BEE\s*Star\s*Rating\s*[:\-]?\s*(\d)", block, re.I)
    star = f"{star_match.group(1)} star" if star_match else ""
    
    if tonnage or star:
        return f"AC {tonnage} {star}".strip()
    return "BOQ"

def extract_particulars(text: str) -> Dict[str, Any]:
    # 1. Check Location
    state = "Unknown"
    for s in TARGET_STATES:
        if re.search(rf"\b{s}\b", text, re.I):
            state = s
            break
    
    if state == "Unknown":
        return {"SKIP_REASON": "Outside Target States"}

    # 2. Extract Basic Info
    bn = re.search(r"GEM/\d{4}/[A-Z]/\d+", text)
    bid_no = bn.group(0) if bn else "N/A"
    
    org_match = re.search(r"Organi[sz]ation\s*Name\s*[:\-\s]+([^\n\r]+)", text, re.I)
    org_name = org_match.group(1).strip() if org_match else "N/A"
    
    sd = re.search(r"Dated\s*[:\-\s]+([\d\-]{10})", text, re.I)
    start_date = sd.group(1) if sd else "N/A"
    
    ed = re.search(r"Bid\s*End\s*Date/Time\s*[:\-\s]*([\d\-\s:]+)", text, re.I)
    end_date = ed.group(1).strip() if ed else "N/A"
    
    qty_match = re.search(r"Total\s*Quantity\s*[:\-\s]*(\d+)", text, re.I)
    qty = int(qty_match.group(1)) if qty_match else 0

    # 3. Determine Requirement (Fridge vs AC vs BOQ)
    req = "BOQ"
    if "refrigerating" in text.lower():
        req = extract_fridge_details(text)
    elif "air conditioner" in text.lower():
        req = extract_ac_details(text)

    return {
        'Bid No': bid_no,
        'Location': state,
        'Requirement': req,
        'Organization Name': org_name,
        'Bid start date': start_date,
        'Bid end date and time': end_date,
        'Quantity': qty
    }

def main_processor():
    if not os.path.exists(BASE_DIR):
        print(f"❌ Error: Folder {BASE_DIR} not found.")
        return

    all_data = []
    print(f"🔍 Scanning PDFs in {BASE_DIR}...")

    for filename in os.listdir(BASE_DIR):
        if filename.lower().endswith('.pdf'):
            fpath = os.path.join(BASE_DIR, filename)
            try:
                reader = pypdf.PdfReader(fpath)
                full_text = ""
                for page in reader.pages:
                    full_text += page.extract_text() + "\n"
                
                bid_data = extract_particulars(full_text)
                
                if "SKIP_REASON" not in bid_data:
                    all_data.append(bid_data)
                    print(f"   ✅ Found: {bid_data['Bid No']} ({bid_data['Requirement']})")
            except Exception as e:
                print(f"   ⚠️ Error reading {filename}: {e}")

    if all_data:
        # PUSH TO MYSQL DUMP TABLE
        save_extracted_to_dump(all_data)
        print(f"\n🚀 Total {len(all_data)} bids synced to MySQL Dump Table.")
    else:
        print("\n📭 No matching bids found to sync.")

if __name__ == "__main__":
    main_processor()