# Run With Docker

This project runs a Flask web app on port 5000.

## Option A: Docker Compose (recommended)

1. Build the image:
   ```bash
   docker-compose build
   ```

2. Start the container:
   ```bash
   docker-compose up -d
   ```

3. Open the app in your browser:
   - http://localhost:5000

4. View logs (optional):
   ```bash
   docker-compose logs -f
   ```

5. Stop the container:
   ```bash
   docker-compose down
   ```

## Option B: Docker CLI (no compose)

1. Build the image:
   ```bash
   docker build -t cairo-traffic .
   ```

2. Run the container:
   ```bash
   docker run --rm -p 5000:5000 \
     -e PYTHONPATH=/app/src \
     -v %cd%\data:/app/data \
     -v %cd%\models:/app/models \
     cairo-traffic
   ```

3. Open the app in your browser:
   - http://localhost:5000

## Start Locally (no Docker)

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Run the Streamlit app:
   ```bash
   python src/web/app.py
   ```

3. Open the app in your browser:
   - http://localhost:5000
