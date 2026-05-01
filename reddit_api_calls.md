# Reddit API Calls List

Here is the exhaustive list of raw Reddit API endpoints our application calls. This covers the 5 configured subreddits across all 5 categories (`hot`, `new`, `top`, `rising`, `best`). 

**Base URL**: `https://www.reddit.com`
**Default Parameters**: `limit=10`, `raw_json=1` (prevents HTML encoding)
**Additional Parameter for 'top'**: `t=day` (fetches top posts from the last 24 hours)

---

## 1. r/MutualfundsIndia
* **Hot**: `https://www.reddit.com/r/MutualfundsIndia/hot.json?limit=10&raw_json=1`
* **New**: `https://www.reddit.com/r/MutualfundsIndia/new.json?limit=10&raw_json=1`
* **Top (Day)**: `https://www.reddit.com/r/MutualfundsIndia/top.json?limit=10&raw_json=1&t=day`
* **Rising**: `https://www.reddit.com/r/MutualfundsIndia/rising.json?limit=10&raw_json=1`
* **Best**: `https://www.reddit.com/r/MutualfundsIndia/best.json?limit=10&raw_json=1`

## 2. r/personalfinanceindia
* **Hot**: `https://www.reddit.com/r/personalfinanceindia/hot.json?limit=10&raw_json=1`
* **New**: `https://www.reddit.com/r/personalfinanceindia/new.json?limit=10&raw_json=1`
* **Top (Day)**: `https://www.reddit.com/r/personalfinanceindia/top.json?limit=10&raw_json=1&t=day`
* **Rising**: `https://www.reddit.com/r/personalfinanceindia/rising.json?limit=10&raw_json=1`
* **Best**: `https://www.reddit.com/r/personalfinanceindia/best.json?limit=10&raw_json=1`

## 3. r/IndiaInvestments
* **Hot**: `https://www.reddit.com/r/IndiaInvestments/hot.json?limit=10&raw_json=1`
* **New**: `https://www.reddit.com/r/IndiaInvestments/new.json?limit=10&raw_json=1`
* **Top (Day)**: `https://www.reddit.com/r/IndiaInvestments/top.json?limit=10&raw_json=1&t=day`
* **Rising**: `https://www.reddit.com/r/IndiaInvestments/rising.json?limit=10&raw_json=1`
* **Best**: `https://www.reddit.com/r/IndiaInvestments/best.json?limit=10&raw_json=1`

## 4. r/FIREIndia
* **Hot**: `https://www.reddit.com/r/FIREIndia/hot.json?limit=10&raw_json=1`
* **New**: `https://www.reddit.com/r/FIREIndia/new.json?limit=10&raw_json=1`
* **Top (Day)**: `https://www.reddit.com/r/FIREIndia/top.json?limit=10&raw_json=1&t=day`
* **Rising**: `https://www.reddit.com/r/FIREIndia/rising.json?limit=10&raw_json=1`
* **Best**: `https://www.reddit.com/r/FIREIndia/best.json?limit=10&raw_json=1`

## 5. r/fatFIREIndia
* **Hot**: `https://www.reddit.com/r/fatFIREIndia/hot.json?limit=10&raw_json=1`
* **New**: `https://www.reddit.com/r/fatFIREIndia/new.json?limit=10&raw_json=1`
* **Top (Day)**: `https://www.reddit.com/r/fatFIREIndia/top.json?limit=10&raw_json=1&t=day`
* **Rising**: `https://www.reddit.com/r/fatFIREIndia/rising.json?limit=10&raw_json=1`
* **Best**: `https://www.reddit.com/r/fatFIREIndia/best.json?limit=10&raw_json=1`

---

## Comments API Call Structure
For every unique post fetched from the above endpoints, the application makes an additional call to fetch its comment thread.

**Structure**: `https://www.reddit.com/r/{subreddit}/comments/{post_id}.json?raw_json=1`

**Example** (for a post with ID `1d3mxyz` in `MutualfundsIndia`):
* `https://www.reddit.com/r/MutualfundsIndia/comments/1d3mxyz.json?raw_json=1`
