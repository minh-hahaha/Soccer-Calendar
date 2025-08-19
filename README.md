# Football API

A simple REST API for football data using the football-data.org API.

## Features

- **Fixtures**: Get match fixtures with filtering options
- **Standings**: Get current league standings
- **Teams**: Get team information
- **Head-to-Head**: Get historical match statistics between teams

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

### 3. Start the API

```bash
# Start the API server
make serve

# Or use uvicorn directly
uvicorn backend.api.main:app --reload
```

### 4. Access the API

- **API Documentation**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health
- **Fixtures**: http://localhost:8000/fixtures
- **Standings**: http://localhost:8000/standings

## API Endpoints

### Fixtures
- `GET /fixtures` - Get match fixtures
- `GET /finished-matches` - Get completed matches

### Standings
- `GET /standings` - Get current league standings

### Teams
- `GET /teams` - Get all teams

### Head-to-Head
- `GET /head2head?matchId=123` - Get head-to-head stats

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
```

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
