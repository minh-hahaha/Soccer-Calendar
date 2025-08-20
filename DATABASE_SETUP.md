# Database Setup for Fantasy Football Caching

This application now uses PostgreSQL to cache FPL data and analysis results, reducing API calls and improving performance.

## Prerequisites

1. **PostgreSQL** installed and running
2. **Python dependencies** installed (see requirements.txt)

## Setup Instructions

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Create Database

Create a PostgreSQL database for the application:

```sql
CREATE DATABASE fantasy_football;
```

### 3. Configure Environment

Copy the environment file and update the database URL:

```bash
cp env.example .env
```

Edit `.env` and update the `DATABASE_URL`:

```
DATABASE_URL=postgresql://username:password@localhost:5432/fantasy_football
```

### 4. Initialize Database

Run the database setup script:

```bash
cd backend
python db_manager.py setup
```

### 5. Load Initial Data

Load the initial FPL data into the database:

```bash
python db_manager.py load
```

## Database Management

The application includes a database management script (`backend/db_manager.py`) with the following commands:

### Available Commands

- **setup**: Create database tables
- **load**: Load initial FPL data
- **refresh**: Force refresh of FPL data
- **cleanup**: Remove expired cache entries
- **status**: Show current cache status

### Usage Examples

```bash
# Check cache status
python db_manager.py status

# Refresh data (useful when new gameweek starts)
python db_manager.py refresh

# Clean up old cache entries
python db_manager.py cleanup
```

## Database Schema

### Tables

1. **bootstrap_data**: Stores FPL bootstrap data (players, teams, gameweeks)
2. **fixtures_data**: Stores FPL fixtures data
3. **analysis_cache**: Caches analysis results

### Data Freshness

- **Bootstrap data**: Considered fresh for 6 hours
- **Fixtures data**: Considered fresh for 6 hours
- **Analysis cache**: Expires after 2 hours

## Benefits

1. **Reduced API Calls**: Data is cached and reused
2. **Faster Response Times**: No need to fetch data from FPL API every time
3. **Better Performance**: Analysis results are cached
4. **Data Persistence**: Data survives application restarts

## Monitoring

You can monitor the cache status using:

```bash
python db_manager.py status
```

This will show:
- Current gameweek data availability
- Data freshness status
- Number of cached analysis results
- Number of expired cache entries

## Troubleshooting

### Common Issues

1. **Database Connection Error**
   - Check if PostgreSQL is running
   - Verify DATABASE_URL in .env file
   - Ensure database exists

2. **Data Not Loading**
   - Check internet connection (needed for initial FPL API calls)
   - Verify FPL API is accessible
   - Check application logs for errors

3. **Cache Not Working**
   - Run `python db_manager.py status` to check cache state
   - Use `python db_manager.py refresh` to force data refresh

### Logs

The application logs when it uses cached data vs. fetching fresh data:

- "Using cached bootstrap data from database"
- "Using cached fixtures data from database"
- "Using cached analysis result"
- "Fetching fresh data from FPL API..."
- "Saved bootstrap data to database for gameweek X"
