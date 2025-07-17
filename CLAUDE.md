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

## Tech Stack Decision
- **Framework**: Streamlit (single app approach - frontend + backend)
- **Language**: Python only
- **Data Processing**: pandas + SQLAlchemy
- **Database**: PostgreSQL
- **File Storage**: AWS S3
- **Deployment**: Single container (Railway/Render/Streamlit Cloud)

## Architecture
```
[User Browser] → [Streamlit App] → [PostgreSQL] → [S3 Storage]
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

## Next Steps
1. Define Contact and Account CSV structures
2. Complete join logic for all 4 tables
3. Build Streamlit application
4. Set up database schema
5. Implement file upload and processing
6. Create dashboard visualizations
7. Deploy to cloud

## Questions to Resolve
1. What if same email+date has multiple opens? (SUM aggregation?)
2. How do Contact and Account CSV files join with the merged data?
3. Any field renaming requirements for final output?
4. Specific dashboard metrics and KPIs needed?