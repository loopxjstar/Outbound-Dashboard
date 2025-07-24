# CSV Processing Dashboard Project

## Project Overview
Building an application that accepts 4 CSV files as input, runs queries on them, prepares final CSV sheets, and creates a dashboard for month-on-month and week-on-week analysis.

## Requirements
- **CSV File Size**: 100KB max per file
- **Processing Frequency**: Weekly uploads
- **Users**: 2-3 concurrent users max
- **Processing Type**: Batch processing (weekly)
- **Deployment**: Cloud (AWS)
- **Budget**: No major constraints

## Tech Stack Decision (IMPLEMENTED)
- **Framework**: Streamlit (single app approach - frontend + backend) ✅
- **Language**: Python only ✅
- **Data Processing**: pandas + SQLAlchemy ✅
- **Database**: SQLite (for development) ✅
- **File Storage**: Local filesystem + potential S3 integration
- **Deployment**: Streamlit Cloud (FREE) ✅

## Architecture (IMPLEMENTED)
```
[User Browser] → [Streamlit App] → [SQLite Database] → [Local Storage]
                      ↓
               [pandas processing]
```

## Data Model

### CSV Files Structure
1. **Send CSV** (primary table):
   - recipient_email
   - domain
   - date_sent
   - + other fields (3-5 more)

2. **Open CSV** (metrics table):
   - recipient_email
   - date_sent
   - open_count
   - clicks
   - + other fields (3-5 more)

3. **Contact CSV** (structure TBD)
4. **Account CSV** (structure TBD)

### Join Logic (Current)
```sql
SELECT s.*, o.open_count, o.clicks, o.[other_open_fields]
FROM send s
LEFT JOIN open o ON s.recipient_email = o.recipient_email 
                 AND s.date_sent = o.date_sent
```

**Implementation in pandas:**
```python
merged = send_df.merge(open_df, on=['recipient_email', 'date_sent'], how='left')
```

## Dashboard Features
- Time period selectors (Week-on-Week vs Month-on-Month)
- Date range filtering
- Interactive charts for trends
- Growth rate calculations
- KPI cards with percentage changes
- Data export functionality

## Cost Estimate
- AWS EC2 t3.micro: ~$10/month
- S3 storage: ~$1/month
- PostgreSQL RDS: ~$15/month
- **Total: ~$25/month**

## Implementation Status

### ✅ COMPLETED
1. **Project Setup**: Python dependencies, directory structure ✅
2. **Streamlit Application**: Complete app.py with dashboard ✅
3. **Data Processing**: Send + Open CSV join logic ✅
4. **Database Integration**: SQLite with data persistence ✅
5. **File Upload**: CSV upload functionality ✅
6. **Dashboard Features**: KPIs, charts, time period analysis ✅
7. **Git Repository**: Code pushed to GitHub ✅
8. **Deployment Ready**: Ready for Streamlit Cloud ✅

### 🚧 IN PROGRESS
- **Data Join Logic Enhancement**: Handling duplicate emails and mismatched dates between Send and Open CSV files
- **Alternative Deployment**: Streamlit Cloud blocked due to fair-use limits, exploring Railway/Render/Heroku

### ❌ DEPLOYMENT ISSUES
- **Streamlit Cloud**: Account blocked - "exceeded fair-use limits"
- **Error Message**: "Your account has exceeded the fair-use limits and was blocked by the system"
- **Alternative Options**: Railway (recommended), Render, Heroku, Vercel (requires rewrite)

### 🔧 CURRENT TECHNICAL CHALLENGES
- **Join Problem**: Send and Open CSV files have:
  - Duplicate recipient_email values in both files
  - date_sent fields don't exactly match between files
  - Need strategy to map open_count to all send emails

### 📋 TODO (Current Sprint)
- Implement flexible join strategies:
  - Strategy 1: Exact email+date match (current)
  - Strategy 2: Email-only join with aggregated opens (fallback)
  - Strategy 3: Closest date match within X days
  - Strategy 4: Hybrid approach with multiple fallbacks
- Deploy to alternative platform (Railway recommended)
- Test with real CSV data

### 📋 TODO (Future Enhancement)
- Contact CSV integration
- Account CSV integration
- AWS S3 file storage
- PostgreSQL database migration
- Advanced analytics features

## Deployment Information
- **Repository**: https://github.com/loopxjstar/Outbound-Dashboard
- **Branch**: main
- **Main File**: app.py
- **Deployment Platform**: Streamlit Cloud (FREE)
- **Expected URL**: https://outbound-dashboard-loopxjstar.streamlit.app/

## Application Features (IMPLEMENTED)
- ✅ CSV file upload (Send, Open, Contact, Account)
- ✅ Data validation and cleaning
- ✅ Send + Open LEFT JOIN on (email + date_sent)
- ✅ Week-on-Week and Month-on-Month analysis
- ✅ Interactive dashboard with Plotly charts
- ✅ KPI cards (Total Sends, Opens, Clicks, Open Rate)
- ✅ Date range filtering
- ✅ Data export functionality
- ✅ SQLite database storage

## Technical Architecture
```
Files Created:
├── app.py                 # Main Streamlit application
├── requirements.txt       # Python dependencies
├── src/
│   ├── __init__.py
│   ├── data_processor.py  # CSV processing logic
│   └── database.py        # SQLite database operations
├── .streamlit/
│   └── config.toml       # Streamlit configuration
├── .gitignore            # Git ignore rules
└── CLAUDE.md             # This documentation
```

## Next Steps
1. Complete Streamlit Cloud deployment
2. Test with real CSV data
3. Add Contact and Account CSV processing
4. Enhance dashboard with additional metrics

## Current Session Progress (2025-07-22)

### ✅ Major Implementation Completed
1. **Incremental DateTime Join Logic**: Successfully implemented 0-11 second matching window
2. **Application Testing**: Confirmed excellent performance with real CSV data
3. **Field Updates**: Changed "Opens" to "Views" throughout system
4. **Enhanced Dashboard**: Added 5th KPI for "Open Rate" based on last_opened column
5. **Deployment Testing**: Successfully running locally with all features

### 🎯 Final Join Strategy Implemented
**Incremental DateTime Matching** (data_processor.py:131-237):
- **Join Keys**: `recipient_name` + `sent_date` 
- **Time Window**: 0 to +11 seconds (extended from 5 seconds)
- **Date Format**: DD/MM/YYYY HH:MM:SS (e.g., "02/07/2025 19:34:57")
- **Performance Optimization**: Email-based subsets for faster lookup
- **Success Rate**: **98.2%** with 11-second window (vs 93.6% with 5-second window)

### 📊 Proven Data Processing Results
```python
# Latest Processing Results (503 send records):
✅ Successful matches: 494 (98.2%)
❌ Failed matches: 9 (1.8%)

# Match Distribution:
+1 seconds: 149 matches
+2 seconds: 229 matches (most common)
+3 seconds: 74 matches
+4 seconds: 16 matches  
+5 seconds: 3 matches
+9 seconds: 6 matches
+10 seconds: 16 matches
+11 seconds: 1 match
No matches: 9 records
```

### 🔧 Technical Implementation Details
**Input Files**: 
- `send_mails.csv` (recipient_name, sent_date, domain, etc.)
- `open_mails.csv` (recipient_name, sent_date, Views, Clicks, last_opened, etc.)

**Output Files**:
- `successful_joins_{timestamp}.csv` (494 records with "Views" column)
- `failed_records_{timestamp}.csv` (9 records with failure reasons)

**Field Mappings**:
- Input: "Opens" → Output: "Views" (renamed for clarity)
- All other fields joined as-is (excluding duplicate join keys)

### 🚀 Enhanced Dashboard Features
**5 KPI Cards**:
1. **Total Sends**: Count of successful matches
2. **Total Views**: Sum of all Views values
3. **Total Clicks**: Sum of all Clicks values  
4. **View Rate**: (Total Views ÷ Total Sends) × 100
5. **Open Rate**: Records with date/time in "last_opened" ÷ Total × 100

**Dual-Tab Interface**:
- ✅ **Successful Matches**: Analytics, charts, data export
- ❌ **Failed Records**: Failure breakdown, pie charts, manual review

### 📈 Performance Improvements Achieved
- **23 additional matches** gained by extending from 5s to 11s window
- **1.8% failure rate** (down from 6.4% originally)
- **Email-based optimization** for faster processing
- **Comprehensive logging** with time increment breakdown

## Questions Resolved ✅
1. ✅ What if same email+date has multiple opens? → SUM aggregation implemented
2. ✅ What's the typical time gap between send_date and open_date? → 2 seconds most common (229 matches)
3. ✅ Field renaming requirements? → "Opens" renamed to "Views" in output
4. ✅ Specific dashboard metrics needed? → 5 KPIs implemented with Open Rate addition
5. ✅ How to handle unmatched records? → Separate failed_records file with detailed reasons

## Remaining Future Enhancements
- Contact CSV integration (placeholder implemented)
- Account CSV integration (placeholder implemented) 
- Alternative deployment platform (Railway/Render recommended)
- AWS S3 file storage migration
- PostgreSQL database upgrade

## Application Status: ✅ PRODUCTION READY
- **Local URL**: http://localhost:8506
- **Network URL**: http://10.5.50.46:8506
- **Success Rate**: 98.2% with 11-second matching window
- **Output Quality**: High-quality joins with comprehensive failure tracking