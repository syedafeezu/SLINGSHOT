# RetailVibe 🛒✨

RetailVibe is a smart in-store shopping assistant designed for the Retail & E-commerce hackathon vertical. It leverages the power of the Google Gemini API to transform natural language user queries into structured, actionable, and interactive in-store shopping lists.

## 🎯 Concept

Navigating a large grocery store can be overwhelming. Users often have a specific goal (e.g., "I want to bake a gluten-free lasagna for date night") but lack a clear list of exact ingredients and where to find them in a physical store. 

RetailVibe solves this by allowing users to simply express their intent. The AI processes the intent, breaks it down into required items, assigns simulated aisle numbers for easy navigation, and proactively suggests a highly relevant complementary item (cross-sell) to enhance the shopping experience and increase basket size for the retailer.

## 🧠 AI Logical Decision-Making

The core of RetailVibe's intelligence is powered by `gemini-1.5-flash`. The AI acts as an expert in-store shopping assistant:
1. **Intent Parsing**: Understands the user's natural language input.
2. **Itemization**: Breaks down complex requests (like recipes or event planning) into individual grocery items.
3. **Spatial Mapping**: Assigns logical, simulated aisle categories (e.g., "Produce", "Dairy", "Aisle 4") to each item to optimize the physical walking path in the store.
4. **Intelligent Cross-Selling**: Analyzes the generated list to recommend one highly relevant complementary item. For example, if the user is making a pasta dish, it might recommend a specific type of wine, garlic bread, or a specialized cheese, providing a brief reasoning for the pairing.

## 🛠️ Architecture

- **Frontend**: Lightweight, high-performance Vanilla HTML, CSS, and JS. Designed with a premium, glassmorphism aesthetic for maximum visual impact without heavy frameworks. Total footprint is minimal.
- **Backend**: Python with Flask, serving as a robust bridge between the client and the AI.
- **AI Integration**: `google-generativeai` SDK interacting with the Gemini API to produce strict, parseable JSON responses.
- **Deployment**: Containerized with Docker, optimized for Google Cloud Run.

## 🚀 Setup Instructions (Local Development)

### Prerequisites
- Python 3.9+
- A Google Gemini API Key. Get one at [Google AI Studio](https://aistudio.google.com/).

### Installation

1. **Clone the repository:**
   ```bash
   git clone <your-repo-url>
   cd SLINGSHOT
   ```

2. **Create a virtual environment (optional but recommended):**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows use: venv\Scripts\activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure Environment Variables:**
   - Copy the example environment file:
     ```bash
     cp .env.example .env
     ```
   - Open `.env` and add your Gemini API key:
     ```env
     GEMINI_API_KEY=your_actual_api_key_here
     ```

5. **Run the Application:**
   ```bash
   python app.py
   ```
   The app will be available at `http://localhost:8080` (or `5000` depending on your Flask config).

## 🐳 Deployment Steps (Google Cloud Run)

RetailVibe is designed to be deployed effortlessly on Google Cloud Run.

1. **Authenticate with Google Cloud:**
   ```bash
   gcloud auth login
   gcloud config set project <YOUR_PROJECT_ID>
   ```

2. **Submit the Docker image to Google Container Registry (or Artifact Registry):**
   ```bash
   gcloud builds submit --tag gcr.io/<YOUR_PROJECT_ID>/retailvibe
   ```

3. **Deploy to Cloud Run:**
   ```bash
   gcloud run deploy retailvibe \
     --image gcr.io/<YOUR_PROJECT_ID>/retailvibe \
     --platform managed \
     --region us-central1 \
     --allow-unauthenticated \
     --set-env-vars GEMINI_API_KEY=your_actual_api_key_here
   ```

4. **Access your live app** using the URL provided by Cloud Run!

## 🔐 Security Note
The `GEMINI_API_KEY` is kept secure via the `.env` file and is never exposed to the frontend or committed to source control (ignored via `.gitignore`).
