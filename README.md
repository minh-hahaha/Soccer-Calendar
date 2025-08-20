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

# Edit .env with your API key
FD_API_KEY=your_football_data_api_key_here
```

### 2. Install Dependencies

```bash
# Install Python dependencies
pip install -r requirements.txt

# Install frontend dependencies (optional)
cd frontend && npm install
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


## API Endpoints

### Football Data (v1)
- `GET /v1/fixtures` - Get match fixtures
- `GET /v1/finished-matches` - Get completed matches
- `GET /v1/standings` - Get current league standings
- `GET /v1/teams` - Get all teams
- `GET /v1/head2head?matchId=123` - Get head-to-head stats

### Fantasy Football Agent
- `GET /fantasy/analyze` - Comprehensive fantasy analysis
- `GET /fantasy/captain-analysis` - Captain selection analysis
- `GET /fantasy/transfer-targets` - Transfer recommendations
- `GET /fantasy/market-watch` - Market insights and trends
- `GET /fantasy/differentials` - Differential pick suggestions

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
