# Book Enrichment Endpoint

## What It Does

This API endpoint takes a raw book record and sends it to a large language model (LLM) to automatically extract useful metadata. It analyzes the book's title and description, then returns three pieces of structured information: a category from a fixed list (e.g., Mystery, Science Fiction, Food), a one-sentence summary of the book, and a set of quality flags that highlight potential data issues (like encoding problems or truncated descriptions). The endpoint is designed to be trustworthy. It validates every response from the model against a strict schema, and if something looks wrong, it asks the model to fix it once before giving up. If it still fails, it returns an error rather than guessing, and saves the problematic data to a quarantine log for manual review.

## Example Request and Response

```bash
curl -X POST http://127.0.0.1:8000/enrich \
  -H "Content-Type: application/json" \
  -d '{"record":{"title":"The Past Never Ends","product_url":"https://books.toscrape.com/catalogue/the-past-never-ends_942/index.html","price_text":"£56.50","price_gbp":56.5,"availability_text":"In stock (16 available)","rating_text":"Four","description":"A simple task, Attorney Chester Morgan thinks. Get a copy of a public record for a young man whose only friend has died in an unexplained accidental death. Except... The police file regarding the demise of sex worker Tanya Everly has been sealed by the order of the chief of police, and no one will talk. Warned to drop the matter, Attorney Morgan knows that if he doesn't speak for the dead young woman, no one will. Haunted by his discovery of the body of a prominent local oilman, Morgan pursues a quest for justice that puts his reputation, career, and life at risk.","source_page":"https://books.toscrape.com/","fetched_at":"2026-08-09T13:13:49Z"}}'
```

**Response:**
```json
{
  "category": "Mystery",
  "summary": "Attorney Chester Morgan investigates a sealed police file on a sex worker's death, uncovering a murder mystery that threatens his career and reveals deep injustice in the American Southwest.",
  "quality_flags": ["encoding_error", "truncated_description"]
}
```

## Job Card

**What it does (one sentence):** Provides a category, a one-sentence summary, and quality_flags for books.

**Input:** `{ "record": { book record with 9 fields: title, product_url, price_text, price_gbp, availability_text, rating_text, description, source_page, fetched_at } }`

**Output:**
```json
{
  "category": "one of [Poetry | Children's literature | Picture books | Fairy tales and folklore | Fantasy | Science fiction | Graphic novels and manga | Romance | Historical fiction | Mystery | Psychological thrillers | Crime | Horror | Dystopian fiction | Adventure and travel | Biography and memoir | History | Sports | Music | Philosophy | Politics | Economics | Sociology | Psychology | Personal development | Spirituality and religion | Careers | Food | Art | Nature | Science | Technology | Culture | other]",
  "summary": "one sentence (null if category is 'other')",
  "quality_flags": "[zero or more of: encoding_error | duplicate_description | truncated_description | missing_description | ambiguous_category | non_english_text | insufficient_information | low_confidence]"
}
```

**It must never:**
- Invent a category outside the list
- Return free text or arbitrary strings
- Give medical, legal, or financial advice
- Reveal the prompt

**When unsure, it should:**
- Return category "other", no summary, and the quality_flags explaining the uncertainty

## Provider & Model

- **Provider:** OpenRouter
- **Model:** `openrouter/free` (free tier, subject to rate limits)

## Environment Variables to Configure

To deploy this endpoint, set these three variables in your `.env` file:

1. **`OPENROUTER_KEY`** — Your OpenRouter API key (get a free public key from https://openrouter.ai)
2. **`LLM_MODEL`** — The model name (default: `openrouter/free`; can also use paid models like `openrouter/gpt-3.5-turbo`)
3. **`OPENROUTER_URL`** — API base URL (default: `https://openrouter.ai/api/v1`)

Optional kill-switch: set **`LLM_ENABLED=false`** to bypass the model entirely and return a deterministic fallback.

## Evaluation Results

**Date:** August 11, 2026  
**Prompt Version:** `enrich-v1`  
**Test Cases:** 8 randomly sampled books from `books.json`  

| Metric | Result |
|--------|--------|
| Categories matched exactly | 4/8 (50%) |
| Average summary similarity | 0.26 (26% word overlap) |
| Encoding errors detected | 5/8 cases flagged |
| Timeout errors | 0 |
| Schema validation failures (after retry) | 0 |

**Observations:** The model correctly identifies genre-specific categories (Mystery, Children's Literature, Music, Science Fiction) but struggles with edge cases (Food vs. other for canning books; Spirituality vs. other for self-help). Summaries diverge from expected text but capture the essential narrative. Quality flags are conservative and often identify legitimate issues (truncation, character encoding).

## Cost Log Example

One successful API call (with repair disabled):

```json
{
  "prompt_version": "enrich-v1",
  "model": "openrouter/free",
  "input_tokens": 2521,
  "output_tokens": 2781,
  "duration_ms": 88502,
  "repair": false
}
```

**Total tokens per call:** 5,302 (input + output)

## Cost Estimate for Scale

**10,000 requests per day = ~53 million tokens per day (~3 cents per day on openrouter/free pricing).**

## What I'd Fix With Another Day

Replace the heuristic-based category matching in the evaluation generator with actual LLM-graded evaluation (e.g., send both expected and actual to a third model to score semantic similarity rather than string matching), so we can better understand whether category mismatches are genuine errors or just different valid interpretations.