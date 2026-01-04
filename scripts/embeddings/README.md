# Embeddings Scripts

Scripts for managing OpenAI embeddings in OpportunityRadar.

## Generate Embeddings

Generate text-embedding-3-small embeddings for opportunities in MongoDB.

### Usage

```bash
# Generate embeddings for all opportunities without embeddings
python scripts/embeddings/generate_embeddings.py

# Show statistics only
python scripts/embeddings/generate_embeddings.py --stats

# Preview without generating (dry run)
python scripts/embeddings/generate_embeddings.py --dry-run

# Force regenerate all embeddings
python scripts/embeddings/generate_embeddings.py --force

# Custom batch size (default: 50)
python scripts/embeddings/generate_embeddings.py --batch-size 100

# Limit number of opportunities to process
python scripts/embeddings/generate_embeddings.py --limit 500
```

### Environment Variables

Requires `OPENAI_API_KEY` to be set in your environment or `.env` file.

### Output

```
==================================================
Embedding Statistics
==================================================
Total opportunities:       150
With embeddings:           120 (80.0%)
Without embeddings:         30
==================================================
```

## How Embeddings Work

1. **Text Representation**: Each opportunity is converted to a text representation:
   - Title
   - Category/Type
   - Description (first 2000 chars)
   - Tags/Themes
   - Technologies
   - Industries

2. **OpenAI Embedding**: The text is sent to OpenAI's `text-embedding-3-small` model

3. **Vector Storage**: The 1536-dimensional vector is stored in MongoDB

4. **Matching**: When matching profiles to opportunities:
   - Profile embedding is compared to opportunity embeddings
   - Cosine similarity gives a score from 0-1
   - This contributes 35-40% of the overall match score

## API Endpoints

Admin endpoints for managing embeddings:

- `GET /api/v1/admin/embeddings/stats` - Get embedding statistics
- `POST /api/v1/admin/embeddings/generate` - Batch generate embeddings
- `POST /api/v1/admin/opportunities/{id}/embedding` - Generate for single opportunity
