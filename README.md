# Football API with Fantasy Football Assistant

A comprehensive REST API for football data and AI-powered Fantasy Football analysis using the football-data.org API and FPL API.

## Features

- **Fixtures**: Get match fixtures with filtering options
- **Standings**: Get current league standings
- **Teams**: Get team information
- **Head-to-Head**: Get historical match statistics between teams
- **Fantasy Football AI Agent**: Advanced analysis and recommendations
- **PostgreSQL Caching**: Efficient data caching to reduce API calls
- **Market Intelligence**: Real-time FPL market insights
- **Transfer Recommendations**: AI-powered transfer suggestions
- **Captain Analysis**: Detailed captain selection guidance
- **Differential Picks**: Low-owned players with high potential

## Quick Start

### 1. Environment Setup

```bash
# Copy environment template
cp env.example .env

# Edit .env with your API key and database configuration
FD_API_KEY=your_football_data_api_key_here
DATABASE_URL=postgresql://username:password@localhost:5432/fantasy_football
```

### 2. Install Dependencies

```bash
# Install Python dependencies
pip install -r requirements.txt

# Install frontend dependencies (optional)
cd frontend && npm install
```

### 3. Database Setup

```bash
# Create PostgreSQL database
createdb fantasy_football

# Initialize database tables
cd backend
python db_manager.py setup

# Load initial FPL data
python db_manager.py load

# Load initial football data
python db_manager.py load-football
```

### 4. Start the API

```bash
# Start the API server
make serve

# Or use uvicorn directly
uvicorn main:app --reload
```

### 5. Access the API

- **API Documentation**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health
- **Fixtures**: http://localhost:8000/v1/fixtures
- **Standings**: http://localhost:8000/v1/standings
- **Fantasy Analysis**: http://localhost:8000/fantasy/analyze
- **Fantasy Cache Status**: http://localhost:8000/fantasy/cache-status
- **Football Cache Status**: http://localhost:8000/v1/cache-status

## API Endpoints

### Football Data (v1)
- `GET /v1/fixtures` - Get match fixtures (cached)
- `GET /v1/finished-matches` - Get completed matches (cached)
- `GET /v1/standings` - Get current league standings (cached)
- `GET /v1/teams` - Get all teams (cached)
- `GET /v1/head2head?matchId=123` - Get head-to-head stats (cached)
- `GET /v1/cache-status` - Football data cache status

### Fantasy Football Agent
- `GET /fantasy/analyze` - Comprehensive fantasy analysis
- `GET /fantasy/captain-analysis` - Captain selection analysis
- `GET /fantasy/transfer-targets` - Transfer recommendations
- `GET /fantasy/market-watch` - Market insights and trends
- `GET /fantasy/differentials` - Differential pick suggestions
- `GET /fantasy/cache-status` - Database cache status
- `GET /fantasy/health` - Agent health check

## Development

### Available Commands

```bash
# Setup
make install                  # Install dependencies

# API
make serve                   # Start API server

# Development
make format                  # Format code
make lint                    # Lint code
make clean                   # Clean up generated files
```

### Environment Variables

```env
# API Configuration
FD_API_KEY=your_football_data_api_key_here
REDIS_URL=redis://localhost:6379

# Database Configuration
DATABASE_URL=postgresql://username:password@localhost:5432/fantasy_football
```

### Database Management

The application includes a database management script for setup and maintenance:

```bash
# Check cache status
cd backend && python db_manager.py status

# Refresh FPL data
cd backend && python db_manager.py refresh

# Load football data
cd backend && python db_manager.py load-football

# Clean up expired cache
cd backend && python db_manager.py cleanup
```

For detailed database setup instructions, see [DATABASE_SETUP.md](DATABASE_SETUP.md).

## Frontend

The frontend is a React application that consumes the API:

```bash
cd frontend
npm install
npm run dev
```

## Getting an API Key

1. Visit [football-data.org](https://www.football-data.org/)
2. Sign up for a free account
3. Get your API key from the dashboard
4. Add it to your `.env` file
