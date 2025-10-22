# AI-Powered Document Management and Assistant

An intelligent, FastAPI-based system that helps you manage, summarize, search, and interact with your documents—augmented by AI. Designed for personal productivity and legal/financial awareness, with a roadmap toward Retrieval-Augmented Generation (RAG) for smarter responses.

---

## Core Features

### 📄 Document Summarization & Tagging
- Automatically summarizes uploaded documents in any language.
- Extracts and stores metadata:
  - **Institution** (e.g., bank, insurance company)
  - **Document Type** (e.g., invoice, legal, contract)
  - **Payment status**
  - **Tax relevance**
  - **Deadlines or expiration dates**

### Smart Notifications & Reminders
- Daily cron job to scan the database for upcoming or missed actions.
- Example: Alerts if a medical invoice is unpaid as the due date nears.

### AI-Powered Search & Retrieval
- Ask natural language questions about your document history.
- Context-aware search across summaries and tags.
- Detects anomalies or missing expected documents (e.g., annual statements).

### Personal Assistant Capabilities
- Calendar integration for smart reminders.
- Legal context detection: suggests rights and even drafts legal emails (e.g., flight cancellation compensation).

---

## Authentication & User Experience

- User registration and login with **JWT-based authentication**.
- Each user has a **private chatbot** and **conversation history**.
- Clean and responsive **dashboard and signup interface**.
- Frontend includes:
  - `index.html`
  - `signup.js` / `main.js`
  - Styles via `styles.css`, `submit_button.css`

---

## Tech Stack

- **Backend**: FastAPI
- **Database**: SQLite via SQLAlchemy
- **Authentication**: JWT + bcrypt
- **Templating**: Jinja2
- **Frontend**: HTML/CSS/JavaScript
- **Upcoming**: Integration with **RAG (Retrieval-Augmented Generation)** for deeper document insights

---

## Project Structure

```
AI-Powered-Document-Management-and-Assistant/
│
├── app/
│   ├── api/
│   │   └── app.py
│   ├── db/
│   │   ├── data/
│   │   └── database.py
│   ├── models/
│   │   ├── models.py
│   │   └── schemas.py
│   ├── services/
│   │   ├── auth.py
│   │   └── summarizer.py
│   └── static/
│       ├── css/
│       │   └── styles.css
│       └── js/
│           ├── main.js
│           └── signup.js
├── templates/
│   └── index.html
├── requirements.txt
└── README.md
```

---

## 📦 Requirements

Install dependencies via:

```bash
pip install -r requirements.txt
```

<details>
<summary>Click to expand dependencies</summary>

```
annotated-types==0.7.0
anyio==4.9.0
bcrypt==4.3.0
click==8.2.1
dotenv==0.9.9
fastapi==0.116.1
h11==0.16.0
idna==3.10
Jinja2==3.1.6
jose==1.0.0
MarkupSafe==3.0.2
passlib==1.7.4
pydantic==2.11.7
pydantic_core==2.33.2
python-dotenv==1.1.1
sniffio==1.3.1
SQLAlchemy==2.0.41
starlette==0.47.1
typing-inspection==0.4.1
typing_extensions==4.14.1
uvicorn==0.35.0
```

</details>

---

## 🧪 How to Run

```bash
# Activate virtual environment if not already
source venv/bin/activate

# Run the app with uvicorn
uvicorn app.api.app:app --reload
```

Access at: [http://127.0.0.1:8000](http://127.0.0.1:8000)

---

## Future Plans

- Add **vector database (e.g., FAISS / Chroma)** for document embedding.
- Integrate **RAG** with local LLM or OpenAI APIs.
- Role-based access control and admin panel.
- Deploy via Docker & CI/CD.

---

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.


pip install -r requirements.txt