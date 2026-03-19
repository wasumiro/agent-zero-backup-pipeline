# Agent Zero Backup Pipeline

Automated backup system for Agent Zero, featuring:
- Notion-based backup storage
- FAISS vector indexing for memories
- Scheduled execution support

## Components
- `scripts/backup_to_notion.py`: Main backup script using Notion API
- `scripts/after50recallmemories.py`: Memory recall extension (currently disabled)
- `skills/vector_db_indexer/index_backup.py`: FAISS indexing with hash-based embeddings

## Configuration

Set the following environment variables:
- `NOTION_API_KEY`: Your Notion API integration token

Example:
```bash
export NOTION_API_KEY="your_token_here"
python3 scripts/backup_to_notion.py
```
