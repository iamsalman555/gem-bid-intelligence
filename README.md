# gem-bid-intelligence
An end-to-end automation pipeline to scrape, extract, and manage Government e-Marketplace (GeM) bid data.
📌 Overview

This project automates the tedious process of searching for and analyzing GeM bids. It uses web scraping to download bid PDFs, extracts technical specifications using Regex, and manages the data via a "Dump & Clean" MySQL architecture.

🛠️ Tech Stack

Automation: Selenium (Web Scraping)

PDF Processing: pypdf & Regular Expressions (Regex)

Database: MySQL (Two-table architecture: Raw Dump & Validated Clean)

Analysis & Reporting: Pandas

Environment: Python 3.x with Virtual Environments (venv)

🏗️ Architecture

Automation (practice_playground.py): Navigates GeM, applies filters (Sort by Latest), and downloads PDFs.

Extraction (gem_extractor.py): Parses PDF text to identify specific requirements (e.g., AC tonnage, Fridge capacity) and pushes to gem_bid_dump.

Validation (Human-in-the-Loop): Allows manual updates to "BOQ" or inconsistent bids in MySQL Workbench.

Promotion (gem_db_manager.py): Moves verified records to the gem_bid_cleaned table and exports a final CSV report.

🚀 How to Run

Clone the repository:

git clone [https://github.com/your-username/gem-bid-intelligence.git](https://github.com/your-username/gem-bid-intelligence.git)
cd gem-bid-intelligence


Set up the virtual environment:

python -m venv venv
source venv/bin/activate  # On Windows: .\venv\Scripts\activate
pip install -r requirements.txt


Configure Database:

Run the queries in setup_gem_db.sql in your MySQL Workbench.

Update your password in gem_db_manager.py.

Execute Pipeline:

Run Scraper -> Run Extractor -> (Optional) Manual Update -> Run Manager.

💡 Key Features

Smart Filtering: Targets specific states like Tamil Nadu, Maharashtra, Karnataka, etc.

Robust Regex: Handles inconsistent PDF text layouts.

Data Integrity: "Dump & Clean" pattern ensures only high-quality data reaches the final report.

📄 License

MIT License - feel free to use and modify!
