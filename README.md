# Reddit AI Agent v2 🚀

An automated intelligence agent that scans Indian financial subreddits, ranks discussions by importance using AI, and delivers a triple-daily digest.

---

## ✨ Key Features (Version 2)

### 1. 🌐 Global Ingestion
The agent scans 5 different Reddit feeds for every subreddit:
*   `hot`, `new`, `top`, `rising`, and `best`.
*   Ensures no trending topic is missed across different algorithm views.

### 2. ⏳ 24-Hour Strict Filter ("Today's Only")
Strict temporal filtering ensures you only see content from the last 24 hours.
*   Uses `created_utc` comparison to guarantee 100% accuracy.
*   Automatically deduplicates posts found in multiple categories.

### 3. 🤖 AI-Driven Composite Ranking
Powered by **GPT-5.4-mini**, the AI evaluates every post against a complex "Importance" matrix:
*   **Importance Score (0-10)**: Calculated based on signal-to-noise ratio and community momentum.
*   **Discussion Status**: Explicitly marks posts as **Complete** (Answered) or **Incomplete** (Ongoing debate).
*   **Reasoning**: Provides a brief AI justification for the rank assigned.

### 4. ⏰ Automated Triple-Daily Digest
Scheduled via `APScheduler` to run and deliver emails at:
*   **08:00 AM IST**: Morning Market Brief.
*   **12:00 PM IST**: Mid-day Sentiment Check.
*   **06:00 PM IST**: Evening Summary.

---

## 🛠 Setup & Usage

### 1. Environment Configuration (`.env`)
```env
OPENAI_API_KEY=your_key_here
OPENAI_MODEL=gpt-5.4-mini
EMAIL_USER=your_gmail@gmail.com
EMAIL_PASS=your_app_password
EMAIL_RECEIVER=email1@link.com, email2@link.com
SUBREDDITS=IndianStreetBets,IndiaInvestments,MutualfundsIndia
PIPELINE_SCHEDULE_TIME=08:00,12:00,18:00
```

### 2. Running Locally
```powershell
python -m venv venv
.\venv\Scripts\activate
pip install -r requirements.txt
.\run.bat
```

---

## 🧪 Verification & Testing
To verify the entire pipeline (Fetch -> Rank -> Email) manually, run the dedicated verification script:
```powershell
python scratch/verify_v2_pipeline.py
```

You can also use the **Live Test Endpoints** in your browser:
*   `http://localhost:8000/test/fetch`: View today's raw posts.
*   `http://localhost:8000/test/rank`: Run AI ranking and **send a test email**.
*   `http://localhost:8000/test/format`: Preview the email text format.

---

## 📊 Sample Output & Response Format

### AI JSON Schema
The AI (GPT-5.4-mini) evaluates and returns a structured JSON list:
```json
{
  "title": "ITR 1 is free and takes 30 minutes...",
  "url": "https://www.reddit.com/r/...",
  "summary": "Practical tax-filing PSA for salaried users...",
  "importance_score": 8.9,
  "reasoning": "High signal-to-noise and directly actionable...",
  "discussion_status": "Complete"
}
```

### Email Digest Format
The final email delivered to recipients follows this professional structure:
```text
1. ITR 1 is free and takes 30 minutes. Stop paying someone to file it for you.
   [Importance Score: 8.9/10.0] | [Status: Complete]
   URL: https://www.reddit.com/r/personalfinanceindia/...
   Reasoning: High signal-to-noise and directly actionable for a large share...
   Summary: Practical tax-filing PSA for salaried users eligible for ITR-1...
```

---

## 📂 Project Structure
*   `app/`: Core application logic (Reddit API, AI Services, Notifier).
*   `scratch/`: Verification scripts and research tools.
*   `run.bat`: Quick-start batch file for Windows.
