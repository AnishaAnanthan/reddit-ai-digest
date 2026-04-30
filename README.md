<<<<<<< HEAD
# Reddit AI Digest

FastAPI backend that fetches top Reddit finance discussions, filters low-value posts with OpenAI, ranks the best posts per subreddit, performs a final global ranking, prints the result to console, and emails the final top 3.

## What This Project Does

The pipeline currently works in these stages:

1. Fetch top daily Reddit posts from the configured subreddits.
2. Stage 1: use OpenAI to filter out noisy, low-value, or irrelevant discussions.
3. Stage 2: rank the validated posts separately for each subreddit and keep the top 3.
4. Stage 3: merge the subreddit winners and select the final top 3 overall.
5. Print the final output in the console.
6. Send the same final output by email.

## Project Structure

- `app/main.py` - FastAPI app and pipeline endpoints.
- `app/config/settings.py` - Application settings loaded from `.env`.
- `app/models/post_models.py` - Pydantic models for raw, filtered, and ranked posts.
- `app/services/reddit/` - Reddit API fetching and post normalization.
- `app/services/ai/` - OpenAI client, prompts, Stage 1 filter, Stage 2 ranking, Stage 3 ranking.
- `app/services/notifications/email_sender.py` - Gmail SMTP email sender.
- `app/utils/output_formatter.py` - Shared console/email formatting.
- `app/utils/validate_ai_output.py` - JSON validation helpers for AI responses.

## Requirements

- Python 3.11 or newer recommended.
- A Reddit-friendly internet connection.
- OpenAI API key.
- Gmail account with 2-Step Verification enabled and an App Password created.

## Setup

### 1. Clone the repository

```powershell
git clone https://github.com/Jeevan-cyber-ai/reddit-ai-agent.git
cd reddit-ai-agent
```

### 2. Create a virtual environment

Windows:

```powershell
python -m venv venv
```

macOS/Linux:

```bash
python3 -m venv venv
```

### 3. Activate the virtual environment

Windows PowerShell:

```powershell
.\venv\Scripts\activate
```

macOS/Linux:

```bash
source venv/bin/activate
```

### 4. Install dependencies

```powershell
pip install -r requirements.txt
```

### 5. Create the `.env` file

Create a `.env` file in the project root and add:

```env
OPENAI_API_KEY=your_openai_api_key
OPENAI_MODEL=gpt-4o-mini

EMAIL_USER=your_gmail_address@gmail.com
EMAIL_PASS=your_gmail_app_password
EMAIL_RECEIVER=recipient_email@gmail.com
```

Notes:

- `EMAIL_USER` and `EMAIL_RECEIVER` can be the same address if you want to send the digest to yourself.
- Use a Gmail App Password, not your normal Gmail password.

## Run the App

Start the API:

```powershell
uvicorn app.main:app --reload
```

Open Swagger UI:

```text
http://127.0.0.1:8000/docs
```

## Current Configuration

The current settings file uses these subreddits:

- `MutualfundsIndia`
- `personalfinanceindia`
- `IndiaInvestments`
- `FIREIndia`
- `fatFIREIndia`

If you want to change them, edit `app/config/settings.py`.

## API Endpoints

### GET `/raw-posts`
Returns the raw normalized Reddit posts.

### GET `/filtered-posts`
Runs Stage 1 filtering and returns only valuable posts.

### GET `/reddit-raw-json`
Returns the raw Reddit JSON payload for each configured subreddit.

### POST `/run-stage1`
Runs Stage 1 filtering only.

### POST `/run-ranking-pipeline`
Runs the full pipeline:

1. Fetch raw posts
2. Stage 1 validation/filtering
3. Per-subreddit ranking
4. Global ranking
5. Console output
6. Email delivery

This endpoint returns diagnostic fields as well:

- `stage1_count`
- `stage1_by_subreddit`
- `subreddit_rankings`
- `ranking_error_by_subreddit`
- `merged_count`
- `final_count`
- `final_top_posts`
- `final_output_text`
- `email_status`
- `email_error`

## Output Format

The final console and email content are generated from one shared formatter and look like this:

```text
Top 3 Reddit Finance Insights
================================
Generated At: 2026-04-20 12:34 UTC

Top 3 Posts:
------------

1.
Title: ...
URL: ...
Summary: ...
------------

2.
Title: ...
URL: ...
Summary: ...
------------

3.
Title: ...
URL: ...
Summary: ...
------------
```

## How To Verify It Is Working

### 1. Check that the app starts

```powershell
uvicorn app.main:app --reload
```

You should see Uvicorn running at `http://127.0.0.1:8000`.

### 2. Verify raw posts

Use Swagger or run:

```powershell
Invoke-RestMethod -Method Get -Uri "http://127.0.0.1:8000/raw-posts"
```

### 3. Verify Stage 1 filtering

Use Swagger or run:

```powershell
Invoke-RestMethod -Method Get -Uri "http://127.0.0.1:8000/filtered-posts"
```

### 4. Verify full ranking and email flow

Use Swagger or run:

```powershell
Invoke-RestMethod -Method Post -Uri "http://127.0.0.1:8000/run-ranking-pipeline" | ConvertTo-Json -Depth 8
```

Check the response for:

- `status = success`
- `final_count = 3` or fewer if there are not enough valid posts
- `final_top_posts` with `title`, `url`, `summary`
- `final_output_text` containing the formatted digest
- `email_status = sent`

## Prompt Contract

The AI prompts now use strict JSON schemas to keep the pipeline deterministic.

### Stage 1 filter output

Each item should include:

- `post_id`
- `title`
- `is_valuable`
- `category`
- `reason`

### Ranking output

Stage 2 and Stage 3 both expect:

- `top_posts`
- each entry containing `title`, `url`, and `summary`

The ranking prompts are tuned for the five supported subreddits and enforce `https://` URLs in the output.

If email fails, check `email_error`.

## Debugging Notes

### Stage 1 empty for a subreddit

Check:

- `stage1_by_subreddit`
- `ranking_error_by_subreddit`

Possible causes:

- Reddit returned no posts for that subreddit.
- Stage 1 filtered all posts out as low-value.
- AI response was invalid or empty.

### Email failure

If you see a Gmail error like `Application-specific password required`, you need:

1. 2-Step Verification enabled on the Gmail account.
2. A Gmail App Password generated in Google Account settings.
3. That App Password saved in `EMAIL_PASS` inside `.env`.

## API Endpoints & Technical Flow

This section provides a detailed breakdown of how each endpoint functions, the sequence of internal calls, and the format of the data returned.

### 1. `GET /reddit-raw-json`
**Purpose:** Fetches the direct, unparsed JSON data from Reddit for all configured subreddits. Useful for debugging and seeing what Reddit actually sends.

*   **Flow:**
    1.  `app/main.py` receives the request.
    2.  Loops through `settings.SUBREDDITS`.
    3.  Calls `reddit_get` in `app/services/reddit/reddit_client.py` for each subreddit.
    4.  Aggregates the raw JSON into a dictionary.
*   **Key Functions:**
    *   `reddit_get(path, params)`: Handles headers, `raw_json=1` flag, and rate-limiting.
*   **Output Format:**
    ```json
    {
      "status": "success",
      "total_posts_fetched": 50,
      "data": { "SubredditName": { "kind": "Listing", "data": { ... } } }
    }
    ```

### 2. `GET /raw-posts`
**Purpose:** Fetches posts and parses them into our internal Python models, but **without** any AI filtering.

*   **Flow:**
    1.  Calls `fetch_top_posts()` in `app/services/reddit/fetch_posts.py`.
    2.  `fetch_top_posts` triggers `fetch_subreddit_posts` concurrently.
    3.  `fetch_subreddit_posts` calls `reddit_get` to get the list of posts.
    4.  For each post, it calls `_process_post`, which triggers `fetch_comments_for_post`.
*   **Key Functions:**
    *   `fetch_comments_for_post(id)`: Hits the specific permalink to get the top 5 comments.
    *   `clean_comment_records()`: Normalizes and filters out noise (thanks, lol, etc.).
*   **Output Format:** A list of `RawPost` objects containing `title`, `content`, `score`, and a `comments` list.

### 3. `GET /filtered-posts`
**Purpose:** The first stage of intelligence. Fetches posts, gets comments, and asks AI to filter for "High Quality" Indian investing content.

*   **Flow:**
    1.  Fetches raw posts (same flow as `/raw-posts`).
    2.  Calls `filter_posts(raw_posts)` in `app/services/ai/stage1_filter.py`.
    3.  AI analyzes the post and the `comment_summary`.
*   **Key Functions:**
    *   `_run_stage1_batch()`: Groups posts into batches of 5 to save AI costs.
    *   `_build_stage1_post()`: Maps the AI's JSON response back into our `Stage1Post` Pydantic model.
*   **Output Format:**
    ```json
    {
      "status": "success",
      "count": 12,
      "stage1_diagnostics": { "discussion_incomplete_count": 3, ... },
      "data": [ { "title": "...", "is_valuable": true, "reason": "...", "comment_assessment": "..." } ]
    }
    ```

### 4. `POST /run-ranking-pipeline`
**Purpose:** The full end-to-end automation. This is what the scheduler runs daily. It fetches, filters, ranks twice (subreddit level, then global level), and sends an email.

*   **Flow:**
    1.  `app/main.py` -> `run_full_ranking_pipeline()` in `pipeline_service.py`.
    2.  **Stage 1**: `filter_posts()` (Filters out noise).
    3.  **Stage 2**: `rank_subreddit_posts()` (Ranks posts *within* each subreddit).
    4.  **Stage 3**: `rank_global_posts()` (Picks the absolute "Best of the Best" across all subreddits).
    5.  **Notification**: `send_results_email()` (Formats and dispatches the final report).
*   **Key Functions:**
    *   `rank_global_posts()`: Uses a specific prompt in `stage3_global_ranker.py` to compare different topics and pick the top 3-5.
    *   `format_top_posts_text()`: Converts the final objects into the readable text seen in the email.
*   **Output Format:** A summary JSON showing how many posts were processed at each stage and the status of the email delivery.

---

## Detailed Function Glossary

| Function Name | Location | Responsibility |
| :--- | :--- | :--- |
| `reddit_get` | `reddit_client.py` | Low-level HTTP requests to Reddit with retries and headers. |
| `fetch_top_posts` | `fetch_posts.py` | The "Manager" for getting raw data from all subreddits. |
| `clean_comment_text` | `clean_comments.py` | Removes URLs, junk characters, and normalizes text. |
| `filter_posts` | `stage1_filter.py` | Sends data to AI and receives the "Keep/Drop" verdict. |
| `rank_global_posts`| `stage3_global_ranker.py` | The final "Judge" that picks the most important posts for the user. |
| `send_results_email`| `email_sender.py` | Connects to SMTP (Gmail) and sends the final formatted report. |

---

## Core Function Documentation

This section provides the technical signature and responsibility for every major function in the application.

### 1. Reddit Data Layer

#### `reddit_get(path: str, params: dict)`
*   **Location:** `app/services/reddit/reddit_client.py`
*   **Description:** The base HTTP requester for Reddit. Adds `raw_json=1` and browser headers.
*   **Input:** 
    *   `path` (str): The Reddit endpoint (e.g., `"/r/IndiaInvestments/top.json"`).
    *   `params` (dict): Query parameters like `limit` and `t`.
*   **Returns:** `dict | list`: The raw JSON response from Reddit or an empty dict on error.

#### `fetch_subreddit_posts(subreddit: str)`
*   **Location:** `app/services/reddit/fetch_posts.py`
*   **Description:** Fetches and parses the top posts for a single subreddit.
*   **Input:** `subreddit` (str): The name of the subreddit.
*   **Returns:** `list[RawPost]`: A list of parsed post models with their initial top comments.

#### `fetch_comments_for_post(post_id: str, subreddit: str)`
*   **Location:** `app/services/reddit/fetch_comments.py`
*   **Description:** Retrieves the top comments for a specific post.
*   **Input:** 
    *   `post_id` (str): The Reddit ID (e.g., `1sy509g`).
    *   `subreddit` (str): The subreddit name.
*   **Returns:** `list[CommentRecord]`: A list of cleaned and normalized comment objects.

---

### 2. Processing & AI Layer

#### `clean_comment_records(raw_comments: list[dict], max_comments: int)`
*   **Location:** `app/utils/clean_comments.py`
*   **Description:** Strips noise (links, short comments, deleted posts) and ranks comments by score.
*   **Input:** 
    *   `raw_comments` (list[dict]): The raw comment data from Reddit.
    *   `max_comments` (int): Limit on how many comments to keep.
*   **Returns:** `list[CommentRecord]`: Cleaned and truncated comments ready for AI.

#### `filter_posts(posts: list[RawPost], return_diagnostics: bool)`
*   **Location:** `app/services/ai/stage1_filter.py`
*   **Description:** Sends batches of posts to AI to determine if they are high-quality Indian investing content.
*   **Input:** 
    *   `posts` (list[RawPost]): The raw posts to evaluate.
    *   `return_diagnostics` (bool): If true, also returns execution stats.
*   **Returns:** `tuple[list[Stage1Post], dict]`: The filtered posts and a diagnostic dictionary.

#### `rank_global_posts(posts: list[Stage2Post])`
*   **Location:** `app/services/ai/stage3_global_ranker.py`
*   **Description:** The final AI ranking step that compares the best posts from ALL subreddits to pick the top 5.
*   **Input:** `posts` (list[Stage2Post]): Already filtered and subreddit-ranked posts.
*   **Returns:** `list[RankedPost]`: The final top selections with summaries and clean URLs.

---

### 3. Pipeline & Notification Layer

#### `run_full_ranking_pipeline()`
*   **Location:** `app/services/pipeline_service.py`
*   **Description:** The "Orchestrator" that runs Stage 1 -> Stage 2 -> Stage 3 and triggers the email.
*   **Input:** None.
*   **Returns:** `dict`: A summary of the pipeline execution (status, counts, and errors).

#### `send_results_email(ranked_posts: list[RankedPost])`
*   **Location:** `app/services/notifications/email_sender.py`
*   **Description:** Formats the final ranked posts into an HTML/Text email and sends it via SMTP.
*   **Input:** `ranked_posts` (list[RankedPost]): The final winners from the global ranking.
*   **Returns:** `bool`: True if the email was sent successfully, False otherwise.

---

## Technical Flow Summary (Flowchart Guide)
If you are drawing a flowchart, follow this sequence:
1.  **Trigger**: User (API) or Scheduler (CRON).
2.  **Ingestion**: `fetch_top_posts` -> `reddit_get` (per subreddit).
3.  **Enrichment**: `fetch_comments_for_post` for every post found.
4.  **Cleaning**: `clean_comments.py` strips away noise.
5.  **Filtration (AI)**: `stage1_filter.py` removes low-quality/off-topic posts.
6.  **Ranking (AI)**: `stage3_global_ranker.py` picks the winners.
7.  **Output**: `email_sender.py` sends the result.

---

## License
No license has been declared yet.
