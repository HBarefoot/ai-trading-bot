# AI Trading Bot MVP

## Project Overview
Advanced cryptocurrency trading bot using machine learning for price prediction and automated trading strategies.

## Architecture
- **Backend**: FastAPI with PostgreSQL
- **Data**: Real-time market data collection
- **ML**: LSTM for price prediction + RL for strategy optimization
- **Frontend**: Streamlit dashboard
- **Infrastructure**: Docker containers

## Quick Start

1. **Setup Environment**
   ```bash
   docker-compose up -d
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

2. **Run Data Collection**
   ```bash
   python src/data/collector.py
   ```

3. **Start Backend**
   ```bash
   uvicorn src.backend.main:app --reload
   ```

4. **Launch Dashboard**
   ```bash
   streamlit run src/frontend/dashboard.py
   ```

## Project Structure
```
ai-trading-bot/
├── src/
│   ├── backend/        # FastAPI backend
│   ├── data/          # Data collection & processing
│   ├── ml/            # Machine learning models
│   └── frontend/      # Streamlit dashboard
├── tests/             # Test suites
├── docker/            # Docker configurations
├── config/            # Configuration files
├── data/              # Raw and processed data
└── logs/              # Application logs
```

## Development Status
See `project-status.md` for detailed progress tracking.