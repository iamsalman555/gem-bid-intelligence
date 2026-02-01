import mysql.connector
import pandas as pd
from datetime import datetime

# ==============================================================================
# MYSQL CONFIGURATION - UPDATE YOUR PASSWORD LOCALLY
# ==============================================================================
DB_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "your_password",  # <--- ENTER YOUR REAL PASSWORD HERE
    "database": "gem_intelligence"
}

def setup_database():
    """Initializes the MySQL Schema and the two-table structure."""
    try:
        conn = mysql.connector.connect(
            host=DB_CONFIG["host"],
            user=DB_CONFIG["user"],
            password=DB_CONFIG["password"]
        )
        cursor = conn.cursor()
        cursor.execute(f"CREATE DATABASE IF NOT EXISTS {DB_CONFIG['database']}")
        cursor.execute(f"USE {DB_CONFIG['database']}")
        
        # Table 1: Raw Dump
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS gem_bid_dump (
                bid_no VARCHAR(50) PRIMARY KEY,
                location VARCHAR(100),
                requirement TEXT,
                organization_name VARCHAR(255),
                start_date VARCHAR(50),
                end_date_time VARCHAR(100),
                quantity INT,
                extraction_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Table 2: Cleaned Data
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS gem_bid_cleaned (
                bid_no VARCHAR(50) PRIMARY KEY,
                location VARCHAR(100),
                requirement TEXT,
                organization_name VARCHAR(255),
                start_date VARCHAR(50),
                end_date_time VARCHAR(100),
                quantity INT,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.commit()
        print("✅ Database Schema Ready.")
    except Exception as e:
        print(f"❌ Database Setup Error: {e}")
    finally:
        if 'conn' in locals() and conn.is_connected():
            cursor.close()
            conn.close()

def save_extracted_to_dump(data_list):
    """Saves raw data from extractor to MySQL."""
    if not data_list: return
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor()
        sql = """INSERT INTO gem_bid_dump 
                 (bid_no, location, requirement, organization_name, start_date, end_date_time, quantity) 
                 VALUES (%s, %s, %s, %s, %s, %s, %s)
                 ON DUPLICATE KEY UPDATE 
                 requirement=VALUES(requirement), quantity=VALUES(quantity), end_date_time=VALUES(end_date_time)"""
        for item in data_list:
            val = (item.get('Bid No'), item.get('Location'), item.get('Requirement'), 
                   item.get('Organization Name'), item.get('Bid start date'), 
                   item.get('Bid end date and time'), item.get('Quantity'))
            cursor.execute(sql, val)
        conn.commit()
        print(f"✅ {len(data_list)} records archived in gem_bid_dump.")
    except Exception as e:
        print(f"❌ Error saving to dump: {e}")
    finally:
        if 'conn' in locals() and conn.is_connected():
            cursor.close()
            conn.close()

def promote_to_cleaned():
    """Moves bids that you HAVE FIXED (non-BOQ) from DUMP to CLEANED."""
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        # This query moves everything where you have replaced 'BOQ' with real text
        sql = """
            INSERT INTO gem_bid_cleaned 
            (bid_no, location, requirement, organization_name, start_date, end_date_time, quantity)
            SELECT bid_no, location, requirement, organization_name, start_date, end_date_time, quantity 
            FROM gem_bid_dump 
            WHERE requirement NOT LIKE 'BOQ%' 
            AND requirement NOT LIKE 'SKIP%'
            ON DUPLICATE KEY UPDATE 
            requirement=VALUES(requirement), 
            end_date_time=VALUES(end_date_time),
            quantity=VALUES(quantity);
        """
        cursor.execute(sql)
        conn.commit()
        print(f"✅ Promotion logic ran. Cleaned table updated.")
    except Exception as e:
        print(f"❌ Error promoting data: {e}")
    finally:
        if 'conn' in locals() and conn.is_connected():
            cursor.close()
            conn.close()

def export_for_manager():
    """Generates the CSV file for your manager."""
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        query = "SELECT * FROM gem_bid_cleaned"
        df = pd.read_sql(query, conn)
        
        filename = f"GeM_Final_Report_{datetime.now().strftime('%Y-%m-%d')}.csv"
        df.to_csv(filename, index=False)
        print(f"✅ CSV Report generated: {filename}")
    except Exception as e:
        print(f"❌ Export Error: {e}")
    finally:
        if 'conn' in locals() and conn.is_connected():
            conn.close()

if __name__ == "__main__":
    # 1. Setup
    setup_database()
    # 2. Move your manual corrections from Dump to Cleaned
    promote_to_cleaned()
    # 3. Create the file to email to your manager
    export_for_manager()