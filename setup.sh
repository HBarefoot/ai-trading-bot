#!/bin/bash

# AI Trading Bot Setup Script
# Run this script to set up the development environment

echo "🚀 Setting up AI Trading Bot development environment..."

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed. Please install Docker first."
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose is not installed. Please install Docker Compose first."
    exit 1
fi

# Create virtual environment
echo "📦 Creating Python virtual environment..."
python3 -m venv venv

# Activate virtual environment
echo "✅ Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo "📥 Installing Python dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# Copy environment file
if [ ! -f .env ]; then
    echo "⚙️ Creating environment file..."
    cp .env.example .env
    echo "📝 Please edit .env file with your actual API keys"
fi

# Start Docker containers
echo "🐳 Starting Docker containers..."
docker-compose up -d

# Wait for database to be ready
echo "⏳ Waiting for database to be ready..."
sleep 10

# Create data directories
echo "📁 Creating data directories..."
mkdir -p data/raw data/processed data/models logs

echo "✅ Setup complete!"
echo ""
echo "Next steps:"
echo "1. Edit .env file with your API keys"
echo "2. Run: source venv/bin/activate"
echo "3. Run: python src/data/collector.py"
echo "4. Run: uvicorn src.backend.main:app --reload"
echo "5. Run: streamlit run src/frontend/dashboard.py"
echo ""
echo "📊 Database UI: http://localhost:8080 (admin@trading.com / admin123)"
echo "🔧 API Docs: http://localhost:8000/docs"
echo "📈 Dashboard: http://localhost:8501"