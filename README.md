# RetailVibe 🛒✨

RetailVibe is a smart in-store shopping assistant designed for the Retail & E-commerce hackathon vertical. It leverages **Google Gemini 2.5 Flash** to transform natural language queries into structured, aisle-mapped, interactive shopping checklists — complete with cross-sell recommendations and persistent shopping history powered by **Google Cloud Firestore**.

## 🎯 Concept

Navigating a large grocery store can be overwhelming. Users often have a specific goal (e.g., "I want to bake a gluten-free lasagna for date night") but lack a clear list of exact ingredients and where to find them.

RetailVibe solves this by allowing users to simply express their intent. The AI processes it, breaks it down into required items with aisle numbers, and proactively suggests a relevant complementary item (cross-sell) to enhance the shopping experience.

## 🧠 AI Logical Decision-Making

Powered by `gemini-2.5-flash`:
1. **Intent Parsing**: Understands natural language input.
2. **Itemization**: Breaks requests (e.g., recipes, meal plans) into individual grocery items.
3. **Spatial Mapping**: Assigns logical aisle categories to optimize the physical store path.
4. **Intelligent Cross-Selling**: Recommends one highly relevant complementary item with reasoning.

## 🛠️ Architecture

| Layer | Technology |
|---|---|
| **Frontend** | Vanilla HTML/CSS/JS — glassmorphism design, WCAG-accessible |
| **Backend** | Python + Flask |
| **AI** | Google Gemini 2.5 Flash (via `google-generativeai`) |
| **History** | Google Cloud Firestore (with in-memory fallback) |
| **Secrets** | Google Cloud Secret Manager (with env var fallback) |
| **Rate Limiting** | Flask-Limiter (10 req/min per IP) |
| **Caching** | In-memory TTL cache (5-min, 128-entry) |
| **Deployment** | Docker → Google Cloud Run |

## 🚀 Setup Instructions (Local Development)

### Prerequisites
- Python 3.11+
- A Google Gemini API Key from [Google AI Studio](https://aistudio.google.com/)

### Installation

1. **Clone the repository:**
   ```bash
   git clone <your-repo-url>
   cd SLINGSHOT
   ```

2. **Create and activate a virtual environment:**
   ```bash
   python -m venv venv
   venv\Scripts\activate      # Windows
   source venv/bin/activate   # macOS / Linux
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment variables:**
   ```bash
   cp .env.example .env
   # Edit .env and set your key:
   # GEMINI_API_KEY=your_actual_api_key_here
   ```

5. **Run the application:**
   ```bash
   python app.py
   ```
   Available at `http://localhost:8080`.

### Running Tests

```bash
pytest tests/ -v
```

All tests run fully offline — Gemini and Google Cloud services are mocked automatically.

## 🐳 Deployment (Google Cloud Run)

### Using Google Secret Manager (Recommended)

```bash
# Store your API key as a secret
echo -n "YOUR_GEMINI_API_KEY" | gcloud secrets create GEMINI_API_KEY --data-file=-

# Build and deploy
gcloud builds submit --tag gcr.io/<PROJECT_ID>/retailvibe
gcloud run deploy retailvibe \
  --image gcr.io/<PROJECT_ID>/retailvibe \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --set-secrets=GEMINI_API_KEY=GEMINI_API_KEY:latest \
  --set-env-vars=GOOGLE_CLOUD_PROJECT=<PROJECT_ID>
```

### Using Environment Variables (Quick Start)

```bash
gcloud run deploy retailvibe \
  --image gcr.io/<PROJECT_ID>/retailvibe \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars GEMINI_API_KEY=your_key_here
```

### Setting up Firestore (Optional — enables persistent history)

```bash
gcloud firestore databases create --region=us-central1
```

## 📡 API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/` | Main application UI |
| `GET` | `/api/health` | Health check (for Cloud Run) |
| `GET` | `/api/history?session_id=<id>` | Fetch recent query history |
| `POST` | `/api/shopping-list` | Generate AI shopping list |

### POST `/api/shopping-list`
**Request:**
```json
{ "query": "i wanna make pasta", "session_id": "optional-session-id" }
```
**Response:**
```json
{
  "items": [
    { "name": "Spaghetti", "aisle": "Aisle 3" },
    { "name": "Tomato Sauce", "aisle": "Aisle 5" }
  ],
  "cross_sell": {
    "name": "Parmesan Cheese",
    "aisle": "Dairy",
    "reason": "The perfect finishing touch for any pasta dish."
  }
}
```

## 🔐 Security

- API key managed via **Google Cloud Secret Manager** in production
- **Never** committed to source control (`.gitignore` + `.dockerignore` enforced)
- Rate limiting: 10 requests/min per IP
- Security headers: `X-Content-Type-Options`, `X-Frame-Options`, `Referrer-Policy`
- Input sanitized and capped at 500 characters
