# Reddit Data Flow & Attribute Extraction

This document explains how data is fetched from Reddit, which raw attributes are received, and which specific features we keep for AI processing.

## 1. The Fetch Phase (Raw Data)
When the application hits Reddit's `.json` endpoints, it receives a massive JSON object with hundreds of attributes per post.

### Full List of Raw Attributes Received:
Reddit sends over 100 attributes per post. Here is the complete list of what we receive in the `data` block:

| Category | Attributes |
| :--- | :--- |
| **Identity** | `id`, `name`, `author`, `author_fullname`, `subreddit`, `subreddit_id`, `subreddit_name_prefixed` |
| **Content** | `title`, `selftext`, `selftext_html`, `url`, `permalink`, `domain`, `is_self`, `is_video`, `is_meta`, `is_original_content`, `thumbnail`, `thumbnail_width`, `thumbnail_height`, `media`, `secure_media`, `media_embed`, `secure_media_embed`, `preview`, `post_hint` |
| **Engagement** | `score`, `ups`, `downs`, `upvote_ratio`, `num_comments`, `num_crossposts`, `total_awards_received`, `gilded`, `gildings`, `all_awardings`, `awarders` |
| **Status/Flags** | `archived`, `pinned`, `stickied`, `locked`, `spoiler`, `over_18`, `quarantine`, `hidden`, `saved`, `clicked`, `visited`, `edited`, `author_premium`, `author_patreon_flair`, `is_robot_indexable`, `is_crosspostable`, `can_gild`, `can_mod_post` |
| **Timing** | `created`, `created_utc`, `approved_at_utc`, `banned_at_utc` |
| **Flair** | `link_flair_text`, `link_flair_type`, `link_flair_richtext`, `link_flair_template_id`, `link_flair_text_color`, `link_flair_background_color`, `link_flair_css_class`, `author_flair_text`, `author_flair_type`, `author_flair_richtext`, `author_flair_template_id`, `author_flair_text_color`, `author_flair_background_color`, `author_flair_css_class` |
| **Moderation** | `approved_by`, `banned_by`, `removed_by`, `removed_by_category`, `mod_note`, `mod_reason_title`, `mod_reason_by`, `mod_reports`, `user_reports`, `num_reports`, `report_reasons`, `removal_reason`, `distinguished`, `treatment_tags` |
| **Settings** | `suggested_sort`, `allow_live_comments`, `contest_mode`, `send_replies`, `subreddit_type`, `subreddit_subscribers`, `wls`, `pwls`, `category`, `discussion_type`, `view_count`, `likes` |

*Note: While we receive all of the above, we immediately filter them down to just 7 features to save memory and AI processing costs.*

---

## 2. The Extraction & Filtering Phase
In the `app/services/reddit/fetch_posts.py` file, we filter these hundreds of attributes down to just **7 critical features**. These are stored in our `RawPost` model.

### Features We Keep:
1.  **`post_id`** (from `id`): Unique identifier for tracking.
2.  **`title`**: Essential for the AI to understand the topic.
3.  **`content`** (from `selftext`): The primary text analyzed for "High Quality" signals.
4.  **`score`**: Used by AI as a "Popularity Signal."
5.  **`url`** (from `permalink`): Used to create the final clickable link in reports.
6.  **`subreddit`**: Provides context for the financial discussion.
7.  **`comments`**: Fetched in a separate step (see below).

---

## 3. The Comment Fetching Process
Comments are **not** part of the initial post fetch. They require a second step:

1.  **Identify Permalink**: We take the `permalink` from the post data.
2.  **Request JSON**: We add `.json` to that link (e.g., `.../comments/xyz123.json`).
3.  **Extract Body**: From the resulting complex JSON, we navigate to the second object in the array and extract the **`body`** attribute of each child.
4.  **AI Analysis**: These comment bodies are what the AI uses to identify "Incomplete Discussions" or "Debates."

---

## 4. Final AI Payload
By filtering the data this way, we reduce a **50KB** raw Reddit post down to a **~2KB** clean object. This ensures the AI stays fast, avoids "hallucinations" caused by irrelevant metadata, and stays within token limits.
