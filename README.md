# Conversational DB Agent

A full-stack, voice-enabled conversational agent that lets you query your MongoDB database using natural language. Powered by LLMs, FastAPI, and a modern analytics dashboard.

---

## 🚀 Features

- **Conversational AI**: Ask questions in plain English, get answers from your database.
- **Voice Interface**: Speak your queries and hear responses (speech-to-text and text-to-speech).
- **LLM-Powered Querying**: Uses Groq/OpenAI LLMs to translate user intent to MongoDB queries.
- **FastAPI Backend**: Robust API layer for NLP, query execution, and session management.
- **Streamlit Dashboard**: Visualizes usage, errors, and performance metrics in real time.
- **Dockerized**: Easy deployment anywhere.
- **Atlas-Ready**: Works out-of-the-box with MongoDB Atlas sample datasets.

---

## 🏗️ Project Structure

```
new_conversational-db-agent/
│
├── app.py                      # FastAPI backend entrypoint
├── dashboard/
│   └── app.py                  # Streamlit analytics dashboard
├── voice_client.py             # Voice interface client (gTTS + speech_recognition)
├── config/
│   └── settings.py             # Configuration and environment loading
├── src/
│   ├── database_manager.py     # MongoDB connection and query logic
│   ├── nlp_processor.py        # LLM prompt and query translation
│   ├── conversation_manager.py # Session and context management
│   └── world_model.py          # (Optional) World model logic
├── tests/
│   └── testmongo.py            # Example MongoDB test script
├── requirements.txt            # Python dependencies
├── Dockerfile                  # Docker build file
├── .env.example                # Example environment variables
└── README.md                   # This file
```

---

## 🏛️ Architecture Overview

```
[User: Voice/Text]
      |
      v
[Voice Client] <--> [FastAPI Backend] <--> [MongoDB Atlas]
      |                        |
      |                        v
[Streamlit Dashboard] <--- [Metrics Collection]
      |
      v
[LLM (Groq/OpenAI)]
```

- **Voice Client**: Listens to your voice, transcribes, sends to backend, and speaks responses.
- **FastAPI Backend**: Handles API requests, uses LLM to generate MongoDB queries, executes them, and returns results.
- **MongoDB Atlas**: Stores your data (sample_analytics, etc.).
- **Streamlit Dashboard**: Shows analytics, errors, and usage metrics.
- **LLM**: Translates natural language to MongoDB queries.

---

## 🗃️ Dataset

- Uses the [MongoDB Atlas Sample Datasets](https://www.mongodb.com/docs/atlas/sample-data/)
- Main collections: `customers`, `transactions`, `events`, `dashboard_metrics`
- **How to load:**  
  1. Create a free MongoDB Atlas cluster  
  2. Load the sample dataset via the Atlas UI  
  3. Use the connection string in your `.env` file

---

## 🛠️ Setup Instructions

### 1. **Clone the repository**

```sh
git clone https://github.com/yourusername/new_conversational-db-agent.git
cd new_conversational-db-agent
```

### 2. **Install dependencies**

```sh
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 3. **Environment variables**

Copy `.env.example` to `.env` and fill in your values:

```
MONGODB_URI=your-mongodb-uri
DATABASE_NAME=sample_analytics
GROQ_API_KEY=your-groq-api-key
```

### 4. **Run the backend**

```sh
uvicorn app:app --reload
```

### 5. **Run the Streamlit dashboard**

```sh
streamlit run dashboard/app.py
```

### 6. **Run the voice client**

```sh
python voice_client.py
```

### 7. **(Optional) Docker deployment**

```sh
docker build -t conversational-db-agent .
docker run -p 8000:8000 --env-file .env conversational-db-agent
```

---

## 📦 Dataset Download

- [MongoDB Atlas Sample Data Docs](https://www.mongodb.com/docs/atlas/sample-data/)
- Or use the provided `sample_analytics` collections in your Atlas cluster.

---

## 🎥 Demo Video

- [Demo Video Link (Google Drive/YouTube)](https://your-demo-link)

## Demo Images

- [Links](https://your-demo-link)

---

## 🤖 Example User Questions

- "Show all customers from California"
- "Find accounts with a limit of 10000"
- "How many transactions happened last month?"
- "What are the most common errors?"
- "List customers with active accounts"

---

## 📝 Notes

- **Voice features** require a working microphone and speakers.
- **gTTS** requires an internet connection for TTS.
- **Streamlit dashboard** provides real-time analytics and error tracking.
- **LLM API keys** (Groq/OpenAI) are required for NLP features.

---

## 📄 License

MIT

---

**For any issues or contributions, please open an issue or pull request on