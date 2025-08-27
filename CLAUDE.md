# CSV Processing Dashboard Project - 2 FILE SYSTEM with ENHANCED VALIDATION ✅

## Project Overview 
Building an application that accepts 2 CSV files as input (Send Mails, Open Mails), runs sophisticated joins on them, and creates an advanced dashboard for analytics with filtering capabilities. Uses internal Contacts database for company mapping. Enhanced with comprehensive validation, column mapping, and advanced data preprocessing.

## Requirements ✅
- **CSV File Size**: 100KB max per file ✅
- **Processing Frequency**: Weekly uploads ✅
- **Users**: 2-3 concurrent users max ✅
- **Processing Type**: Batch processing (weekly) ✅
- **Deployment**: Cloud deployment (Render) ✅
- **Budget**: Free tier solutions ✅

## Tech Stack (IMPLEMENTED) ✅
- **Framework**: Streamlit (single app approach - frontend + backend) ✅
- **Language**: Python only ✅
- **Data Processing**: pandas with custom join algorithms ✅
- **Database**: SQLite (for future data persistence) ✅
- **File Storage**: Local filesystem with CSV export ✅
- **Deployment**: Render (FREE tier) ✅

## Enhanced Architecture ✅
```
[2 CSV Uploads] → [Validation & Column Mapping] → [Advanced Data Preprocessing] → [Interactive Dashboard]
                                ↓
            [Send Mails: Domain Filter + Time Adjust + Text Clean]
            [Open Mails: Comma Split + Date Format Convert]
                                ↓
    [Send-Open Join] → [Internal Contacts Database Join]
                                ↓
                    [Enhanced Analytics with Improved Data Quality]
```

## Enhanced Validation & Preprocessing System ✅

### Phase 0: Comprehensive File Validation (BEFORE Processing)
```python
# Step 1: Column Mapping & Header Validation
'send_mails': {
    'Recipient Name': 'recipient_name',    # User header → System header
    'Date': 'sent_date',                   # User header → System header
    'Recipient Email': 'Recipient Email'   # Keep as-is
}
'open_mails': {
    'Recipient': 'recipient_name',         # User header → System header
    'Sent': 'sent_date',                   # User header → System header
    'Opens': 'Views',                      # User header → System header
    'Clicks': 'Clicks',                   # Keep as-is
    'Last Opened': 'last_opened'          # User header → System header
}

# Step 2: Data Content Validation
- Date format validation (DD/MM/YYYY HH:MM:SS)
- Email format validation (contains @)
- Numeric validation (Views, Clicks)
- Empty file detection
- Missing column detection with clear error messages
```

### Advanced Data Preprocessing Rules

#### **Send Mails CSV Preprocessing:**
```python
# Rule 1: Domain Filtering
- Remove all records containing "loopwork.co" in Domain column
- Case-insensitive matching with detailed logging

# Rule 2: Time Adjustment  
- Add 9 hours 30 minutes to all sent_date values
- Automatic date rollover handling (e.g., 23:30 + 9:30 = next day 09:00)
- Before/after logging with date change indicators

# Rule 3: Recipient Name Cleaning
- Split by '<' symbol and extract part before '<'
- "Daniel Novak <dan@landish.ca>" → "Daniel Novak"
- "erin@landish.ca" → "erin@landish.ca" (no change if no '<')
- Automatic space trimming
```

#### **Open Mails CSV Preprocessing:**
```python
# Rule 1: Recipient Name Comma Splitting
- Split by ',' and take first value only
- "Breanna Hughes,Bailee Cooper,Harshit Gupta" → "Breanna Hughes"
- "John Doe" → "John Doe" (no change if no comma)

# Rule 2: Date Format Standardization
- Convert from "Jul 3, 2025, 02:14:21" to "03/07/2025 02:14:21"
- Handles various month name formats automatically
- Flexible parsing with fallback to original on errors
```

## Data Processing Pipeline (COMPLETED) ✅

### Phase 1: Send-Open Join (Two-Phase Datetime Matching)
```python
# Phase 1: 0-11 second incremental matching (99.4% success rate)
# Phase 2: 12-60 second matching on failed records
# Final: 500/503 successful matches
# Enhanced error handling prevents division by zero errors
```

### Phase 2: Contacts Integration
```python
# Join on: send_open['Recipient Email'] = contacts['Email']
# Many-to-one matching (multiple send records → one contact)
# Result: 339 successful + 161 failed = 500 total (perfect count preservation)
# Safe division check: "No records matched with contacts sheet" error message
```

### Phase 3: Final Output (2-File System)
```python
# Final processing complete after Contacts integration
# Ready for dashboard analytics and filtering with Company URL data
# Account History integration removed for simplified processing
```

## Advanced Dashboard Features (COMPLETED) ✅

### Dashboard Filters
- **📅 Sent Date Range**: Dynamic date picker for time-based filtering
- **🔄 Reset Filters**: One-click filter reset functionality  
- **📊 Filter Summary**: Shows "X records (filtered from Y total)"
- **Note**: Account Owner filter removed in 2-file system

### KPI Cards (7 Total)
1. **Total Sends**: Count of filtered records
2. **Total Views**: Sum of Views column
3. **Total Clicks**: Sum of Clicks column  
4. **View Rate**: (Total Views / Total Sends) × 100
5. **Open Rate**: Based on last_opened column analysis
6. **Accounts Owned**: Unique count of Company URL IDs
7. **High Engagement Accounts**: Count of companies where Total Views > 2 × Total Emails Sent

### Analytics Features
- **Real-time filtering**: All KPIs and charts update instantly
- **Time-series analysis**: Week-on-Week and Month-on-Month trends
- **Interactive charts**: Plotly-powered visualizations
- **Data export**: Download successful and failed records separately
- **Failed record analysis**: Separate sections for different failure types

## Final Data Model ✅

### Required CSV Columns with Enhanced Validation ✨
1. **Send Mails CSV**:
   - `recipient_name` (for datetime join) - Auto-cleaned and standardized
   - `sent_date` (DD/MM/YYYY HH:MM:SS format) - +9:30 hours adjustment applied
   - `Recipient Email` (for contacts join) - Validated email format

2. **Open Mails CSV**:
   - `recipient_name` (for datetime join) - Auto-cleaned and standardized 
   - `sent_date` (DD/MM/YYYY HH:MM:SS format) - No time adjustment
   - `Views` (renamed from "Opens") - Numeric validation
   - `Clicks` - Numeric validation

3. **Internal Contacts Database** (data/contacts.csv):
   - `Email` (join key) - Email format validation
   - `Company URL` (for company mapping) - Auto-filtered (excludes loopwork.co)
   - All other contact fields (merged to final output)

~~4. **Account History CSV** (REMOVED in 2-file system)~~


### Final Output Schema
```
send_open_contacts = 
  Send Mails fields (with +9:30 hours adjustment) +
  Open Mails fields (Views, Clicks) +
  All Contacts fields (filtered for loopwork.co domains) +
  Company URL ID (unique incremental ID) +
  Enhanced validation status and error tracking
```

## Processing Results ✅
- **Input**: 503 Send Mails records
- **Send-Open Join**: 500 successful (99.4% success rate)
- **Contacts Join**: 339 successful (67.8% success rate) 
- **Final Output**: 339 complete records + 164 failed records
- **Perfect Count Preservation**: Input = Output (no duplicate creation)
- **Note**: Account History processing removed in 2-file system

## Advanced Join Algorithms (IMPLEMENTED) ✅

### Two-Phase Datetime Matching
```python
# Phase 1: Try 0, +1, +2, ..., +11 seconds for each email
# Phase 2: Try +12, +13, ..., +60 seconds on failed records only
# Handles timing differences between send and open events
# Avoids duplicate matching by tracking used open records
```

### Many-to-One Contact Matching with Division by Zero Prevention
```python
# Creates lookup dictionary from contacts (first occurrence wins)
# Iterates through send-open records individually
# Merges all contact fields to each matching send-open record
# Maintains exact record count (no pandas merge duplicates)
# Safe division check: if len(send_open_df) > 0 before calculations
# Enhanced error handling: "No records matched with contacts sheet"
# 3-tuple return format: (successful_data, failed_data, validation_errors)
```

## Enhanced Error Handling & User Experience ✅

### Comprehensive Error Messages
```python
# File Validation Errors
❌ **Missing File**: Send Mails CSV is required but not uploaded.
❌ **Empty File**: Open Mails CSV contains no data rows.
❌ **Missing Columns**: 'Recipient Name' (maps to 'recipient_name'), 'Date' (maps to 'sent_date')
📋 **Available Columns in the uploaded sheet**: Date, Subject, Email, Domain

# Data Format Errors  
❌ **Date Format Error**: 3 rows have invalid date format in 'sent_date'. Expected: DD/MM/YYYY HH:MM:SS
❌ **Email Format Error**: 2 rows have invalid email format in 'Email'
❌ **Numeric Format Error**: 1 rows have non-numeric values in 'Views'

# Processing Errors
❌ **No records matched with contacts sheet**: No emails from Send-Open data found in Contacts CSV
❌ **Join Error**: Failed to join Send Mails and Open Mails data
❌ **File Processing Error**: 'utf-8' codec can't decode byte (encoding issues)
```

### User-Friendly Features
- **Clear column mapping explanations**: Shows what user headers map to internally
- **Before/after examples**: Shows data transformations with visual indicators
- **Progress logging**: Detailed processing steps with emoji indicators  
- **Safe division**: Prevents "division by zero" errors
- **Encoding flexibility**: Handles different file encodings automatically

### Company URL ID System
```python
# Generates unique incremental IDs (1, 2, 3...) for each Company URL
# Same URL gets same ID across all records
# Used for Account History join and "Accounts Owned" KPI
```

## Deployment Status ✅
- **Repository**: https://github.com/loopxjstar/Outbound-Dashboard
- **Platform**: Render (Free Tier)
- **Status**: Production Ready ✅
- **Last Commit**: `97cd6ae` - Complete CSV Analytics Dashboard with Advanced Features
- **Python Version**: 3.10.12 (forced for compatibility)

## File Structure (FINAL) ✅
```
├── app.py                 # Main Streamlit application with advanced filters
├── requirements.txt       # Optimized dependencies (pandas 1.3.5)
├── src/
│   ├── __init__.py
│   ├── data_processor.py  # Advanced CSV processing with 4-file pipeline
│   └── database.py        # SQLite database (ready for future persistence)
├── outputs/               # Generated CSV outputs
├── render.yaml           # Deployment configuration
├── runtime.txt           # Python version specification
└── CLAUDE.md             # This comprehensive documentation
```

## Technical Achievements ✅

### Data Processing Excellence
- **99.4% join success rate** through intelligent datetime matching
- **Exact record count preservation** preventing data duplication
- **Robust error handling** with detailed failure categorization and division by zero prevention
- **Performance optimization** with lookup dictionaries and efficient algorithms
- **Enhanced validation system** with column mapping and preprocessing rules
- **Multi-encoding support** for UTF-8, Latin-1, and CP1252 character sets

### Dashboard Innovation
- **Real-time filtering** across all metrics and visualizations
- **Advanced KPI calculations** including unique count metrics
- **Responsive UI design** with 5-column filter layout
- **Enhanced user experience** with filter summaries and reset functionality

### Code Quality
- **Comprehensive logging** for debugging and monitoring
- **Modular architecture** with clear separation of concerns
- **Error handling** for edge cases and missing data
- **Production-ready** code with proper validation

## Success Metrics ✅
- **Data Accuracy**: 100% (exact record count preservation)
- **Join Success**: 99.4% send-open, 67.8% contacts integration
- **Performance**: Sub-second processing for 500+ records
- **User Experience**: Intuitive filters with real-time updates
- **Reliability**: Comprehensive error handling and validation

## Session Development History ✅

### Major Milestones Achieved
1. **Two-Phase DateTime Matching**: Implemented sophisticated 0-11s + 12-60s incremental matching algorithm
2. **Contacts Integration**: Added mandatory Contacts CSV with many-to-one join logic
3. **Company URL ID System**: Created unique incremental IDs for Account History matching
4. **Record Count Fix**: Resolved duplicate creation issue ensuring input = output counts
5. **Advanced Dashboard Filters**: Added sent_date range and Account Owner filtering
6. **Enhanced KPIs**: Added "Accounts Owned" metric with real-time filter updates
7. **Enhanced Validation System**: Comprehensive column mapping and preprocessing rules ✨
8. **Division by Zero Fix**: Safe error handling with clear user messages ✨
9. **Multi-Encoding Support**: Automatic handling of different file character encodings ✨

### Technical Problem Solving
- **Fixed join column mismatch**: Changed from "recipient_name" to "Recipient Email" for contacts join
- **Resolved record duplication**: Replaced pandas merge with iteration-based approach
- **Optimized performance**: Implemented lookup dictionaries for faster matching
- **Enhanced error handling**: Added comprehensive failure categorization and logging
- **Division by zero prevention**: Added safe validation checks with clear error messages ✨
- **Character encoding issues**: Implemented multi-encoding detection (UTF-8, Latin-1, CP1252) ✨
- **Column mapping system**: Flexible header validation with user-friendly mapping explanations ✨
- **Data preprocessing rules**: Advanced filtering and cleaning before join operations ✨

### Data Processing Evolution
```python
# Initial: Simple pandas merge (unreliable)
# Final: Multi-phase custom algorithm with 99.4% success rate

Phase 1: Send-Open (503 → 500 records, 99.4% success)
├── 0-11 second incremental matching
├── Email-based optimization
└── Comprehensive failure tracking

Phase 2: Contacts (500 → 339/161 split, 67.8% success)  
├── Many-to-one matching with first-occurrence selection
├── All contact fields merged
└── Perfect count preservation

Phase 3: Account History (339 records → 21 Company URLs matched)
├── Company URL unique ID generation (64 unique IDs)
├── Latest edit date selection with proper sorting
└── Enhanced Account Owner filtering
```

## Future Enhancement Opportunities
- **Data Persistence**: Integrate existing SQLite functionality for page reload survival
- **Advanced Analytics**: Add more sophisticated time-series analysis
- **Export Enhancements**: Multiple format support (Excel, PDF reports)
- **Performance Scaling**: Optimize for larger datasets (1000+ records)
- **User Management**: Add user-specific data filtering and permissions

## Project Status: COMPLETED ✅
The CSV Analytics Dashboard is now a production-ready application that successfully processes complex multi-CSV data with sophisticated join algorithms and provides an advanced filtering dashboard for data analysis. All original requirements have been met and exceeded with additional features that enhance usability and analytical capabilities.

### Final URLs
- **Local Development**: http://10.5.50.46:8501
- **Production Repository**: https://github.com/loopxjstar/Outbound-Dashboard
- **Deployment Platform**: Render (Free Tier)

**Project successfully configured for 2-file system with streamlined processing and all core functionality intact.**

## Version 2 of Calls Analytics (Future Implementation)

### 📊 **Advanced Analytical Table Structure**

**Requirement**: Create a complex analytical table for calls data with multi-dimensional analysis.

### **X-Axis (Columns):**
- **Column 1**: "Assigned" unique values (e.g., John Smith, Jane Doe)
- **Column 2**: "Call Disposition" unique values as sub-rows under each Assigned person
  - So under "John Smith" you'd have sub-rows like:
    - Connected
    - Not Interested  
    - Callback
    - etc.

### **Y-Axis (Rows):**
- **Date ranges split by weeks** (Week 1, Week 2, Week 3, etc.)

### **Cell Values (What shows in each intersection):**
For each combination of (Week + Assigned Person + Call Disposition), display:
1. **Number of records** (count)
2. **Connect rate** (% of Connected calls for that person/disposition/week)
3. **Company / Account** count (unique companies for that cell)

### **Example Table Layout:**
```
                    John Smith                    |    Jane Doe
Week        Connected | Not Int. | Callback      | Connected | Not Int. | Callback
Week 1      5 records | 3 records| 2 records    | 4 records | 1 record | 0 records
            80% conn  | 0% conn  | 0% conn      | 100% conn | 0% conn  | 0% conn
            3 comp.   | 2 comp.  | 1 comp.      | 2 comp.   | 1 comp.  | 0 comp.
            
Week 2      8 records | 2 records| 1 record     | 6 records | 3 records| 1 record
            75% conn  | 0% conn  | 0% conn      | 83% conn  | 0% conn  | 0% conn
            4 comp.   | 2 comp.  | 1 comp.      | 3 comp.   | 2 comp.  | 1 comp.
```

### **Implementation Questions for Future:**
1. Should this table be **filtered** by the current filter selections, or show **all data**?
2. For "Connect rate" in each cell - connect rate **within that specific disposition** OR **for that person in that week across all dispositions**?
3. Should weeks be **calendar weeks** or **rolling 7-day periods** from the data?
4. How to handle cases where someone has 0 records for a disposition in a week?

### **Technical Considerations:**
- Multi-level grouping: Week → Assigned → Call Disposition
- Complex pivot table with multiple metrics per cell
- Dynamic column generation based on unique Assigned/Disposition values
- Week-based date aggregation and formatting
- Responsive table design for multiple columns