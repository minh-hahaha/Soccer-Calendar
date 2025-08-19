#!/usr/bin/env python3
"""
Integration script to connect existing API with ML prediction service
"""

import os
import sys
import subprocess
from pathlib import Path

def run_command(command, description):
    """Run a command and handle errors"""
    print(f"🔄 {description}...")
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(f"✅ {description} completed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed: {e}")
        print(f"Error output: {e.stderr}")
        return False

def check_prerequisites():
    """Check if all prerequisites are met"""
    print("🔍 Checking prerequisites...")
    
    # Check Python version
    if sys.version_info < (3, 8):
        print("❌ Python 3.8+ required")
        return False
    
    # Check if .env file exists
    if not os.path.exists('.env'):
        print("⚠️  .env file not found. Creating from template...")
        if os.path.exists('env.example'):
            os.system('cp env.example .env')
            print("✅ Created .env file from template")
            print("📝 Please edit .env file with your API key and database settings")
        else:
            print("❌ env.example not found")
            return False
    
    # Check if API key is set
    from dotenv import load_dotenv
    load_dotenv()
    api_key = os.getenv('FD_API_KEY')
    if not api_key or api_key == 'your_football_data_api_key_here':
        print("⚠️  Please set FD_API_KEY in your .env file")
        return False
    
    print("✅ Prerequisites check passed")
    return True

def setup_database():
    """Setup database if needed"""
    print("🗄️  Setting up database...")
    
    # Check if PostgreSQL is available
    try:
        result = subprocess.run(['psql', '--version'], capture_output=True, text=True)
        print("✅ PostgreSQL found")
    except FileNotFoundError:
        print("⚠️  PostgreSQL not found. You can:")
        print("   1. Install PostgreSQL locally")
        print("   2. Use a cloud database (update DB_URI in .env)")
        print("   3. Use SQLite for development (modify config)")
        return False
    
    return True

def train_sample_model():
    """Train a sample model for testing"""
    print("🤖 Training sample ML model...")
    
    # Create artifacts directory
    os.makedirs('./artifacts', exist_ok=True)
    
    # Train model with sample data
    success = run_command(
        'python -m backend train fit --algo xgb --use-sample',
        "Training XGBoost model with sample data"
    )
    
    if success:
        print("✅ Sample model trained successfully")
        print("📊 Model saved to ./artifacts/")
    else:
        print("❌ Model training failed")
        print("💡 You can still use the API with simplified predictions")
    
    return success

def test_integration():
    """Test the integrated API"""
    print("🧪 Testing API integration...")
    
    # Start the server in background
    print("🚀 Starting API server...")
    server_process = subprocess.Popen([
        'uvicorn', 'main:app', '--host', '0.0.0.0', '--port', '8000', '--reload'
    ])
    
    try:
        import time
        import requests
        
        # Wait for server to start
        print("⏳ Waiting for server to start...")
        time.sleep(3)
        
        # Test health endpoint
        print("🔍 Testing health endpoint...")
        response = requests.get('http://localhost:8000/health')
        if response.status_code == 200:
            health_data = response.json()
            print(f"✅ Health check passed: {health_data}")
        else:
            print(f"❌ Health check failed: {response.status_code}")
        
        # Test fixtures endpoint
        print("🔍 Testing fixtures endpoint...")
        response = requests.get('http://localhost:8000/fixtures?status=SCHEDULED')
        if response.status_code == 200:
            fixtures_data = response.json()
            print(f"✅ Fixtures endpoint working: {len(fixtures_data.get('fixtures', []))} fixtures found")
        else:
            print(f"❌ Fixtures endpoint failed: {response.status_code}")
        
        # Test prediction endpoint (if model is available)
        print("🔍 Testing prediction endpoint...")
        response = requests.get('http://localhost:8000/predict?match_id=12345')
        if response.status_code == 200:
            pred_data = response.json()
            print(f"✅ Prediction endpoint working: {pred_data.get('probs', {})}")
        else:
            print(f"⚠️  Prediction endpoint: {response.status_code} - {response.text}")
        
        print("✅ Integration test completed")
        
    except Exception as e:
        print(f"❌ Integration test failed: {e}")
    
    finally:
        # Stop the server
        print("🛑 Stopping server...")
        server_process.terminate()
        server_process.wait()

def main():
    """Main integration function"""
    print("=" * 60)
    print("FOOTBALL API + ML PREDICTION INTEGRATION")
    print("=" * 60)
    
    # Check prerequisites
    if not check_prerequisites():
        print("❌ Prerequisites not met. Please fix the issues above.")
        return
    
    # Setup database
    if not setup_database():
        print("⚠️  Database setup incomplete. Continuing with simplified mode...")
    
    # Train sample model
    model_trained = train_sample_model()
    
    # Test integration
    test_integration()
    
    print("\n" + "=" * 60)
    print("INTEGRATION COMPLETE!")
    print("=" * 60)
    
    if model_trained:
        print("✅ Full ML prediction service is ready!")
        print("🚀 Start the server with: uvicorn backend.main:app --reload")
        print("📊 Access API docs at: http://localhost:8000/docs")
    else:
        print("⚠️  Simplified prediction service is ready")
        print("🚀 Start the server with: uvicorn backend.main:app --reload")
        print("📊 Access API docs at: http://localhost:8000/docs")
        print("💡 Train a full model later with: python -m backend train fit --algo xgb --use-sample")
    
    print("\n📋 Available endpoints:")
    print("   GET  /fixtures                    - Get match fixtures")
    print("   GET  /teams                       - Get teams")
    print("   GET  /standings                   - Get league standings")
    print("   GET  /head2head?matchId=123       - Get head-to-head stats")
    print("   GET  /predict?match_id=123        - Predict match outcome")
    print("   POST /batch/predict               - Predict multiple matches")
    print("   GET  /fixtures-with-predictions   - Fixtures with predictions")
    print("   GET  /health                      - Health check")

if __name__ == "__main__":
    main()
