# Football Fixtures App

A modern web application that displays Premier League fixtures using FastAPI backend and Vite React frontend.

## Project Structure

```
Football/
├── main.py              # FastAPI backend
├── frontend/            # Vite React frontend
│   ├── src/
│   │   ├── App.tsx     # Main React component
│   │   └── index.css   # Tailwind CSS styles
│   └── package.json
└── README.md
```

## Setup Instructions

### Backend Setup

1. Install Python dependencies:
   ```bash
   pip install fastapi uvicorn requests
   ```

2. Set up your API Football key:
   ```bash
   export API_FOOTBALL_KEY="your_api_key_here"
   ```

3. Run the FastAPI server:
   ```bash
   uvicorn main:app --reload
   ```

The backend will be available at `http://localhost:8000`

### Frontend Setup

1. Navigate to the frontend directory:
   ```bash
   cd frontend
   ```

2. Install dependencies:
   ```bash
   npm install
   ```

3. Start the development server:
   ```bash
   npm run dev
   ```

The frontend will be available at `http://localhost:5173`

## Features

- Displays Premier League Round 1 fixtures
- Shows match details including teams, venue, date, and status
- Responsive design with Tailwind CSS
- Loading and error states
- Real-time data from API-Football
- Fast development with Vite

## API Endpoints

- `GET /round1` - Returns Premier League Round 1 fixtures

## Technologies Used

- **Backend**: FastAPI, Python
- **Frontend**: Vite, React, TypeScript, Tailwind CSS
- **API**: API-Football (v3) # Soccer-Calendar
