#!/usr/bin/env python3
import os
import logging
import numpy as np
import faiss
import hashlib

# Log configuration (same log used by backup script)
log_dir = '/a0/usr/workdir/logs'
os.makedirs(log_dir, exist_ok=True)
log_file = os.path.join(log_dir, 'backup.log')
logging.basicConfig(filename=log_file, level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')

# FAISS index location
INDEX_DIR = '/a0/usr/workdir/vec_index'
os.makedirs(INDEX_DIR, exist_ok=True)
INDEX_PATH = os.path.join(INDEX_DIR, 'faiss.index')

# Desired embedding dimension (consistent with previous OpenAI dim)
EMB_DIM = 1536


def _load_or_create_index():
    """Load an existing FAISS index or create a new flat L2 index with dimension EMB_DIM."""
    if os.path.exists(INDEX_PATH):
        try:
            index = faiss.read_index(INDEX_PATH)
            logging.info('Loaded existing FAISS index')
            return index
        except Exception as e:
            logging.error(f'Failed to load FAISS index: {e}')
    # Create a fresh flat L2 index (no training needed)
    index = faiss.IndexFlatL2(EMB_DIM)
    logging.info('Created new FAISS index')
    return index


def _save_index(index):
    """Persist the FAISS index to disk."""
    try:
        faiss.write_index(index, INDEX_PATH)
        logging.info('FAISS index saved')
    except Exception as e:
        logging.error(f'Failed to save FAISS index: {e}')

def _hash_embed(text: str) -> np.ndarray:
    """Create a deterministic 1536‑dimensional embedding from a SHA‑256 hash.
    The hash yields 32 bytes; we repeat the byte sequence to fill the vector and
    cast to float32 (0‑255 range). This is lightweight and requires no external model.
    """
    # Compute SHA‑256 hash of the text
    digest = hashlib.sha256(text.encode('utf-8')).digest()
    # Convert to a list of integers (0‑255)
    ints = list(digest)
    # Repeat the pattern to reach EMB_DIM
    repeats = (EMB_DIM + len(ints) - 1) // len(ints)
    full = (ints * repeats)[:EMB_DIM]
    vec = np.array(full, dtype=np.float32).reshape(1, EMB_DIM)
    return vec

def index_markdown(md_path):
    """Read a markdown file, embed it with the hash‑based function, and store the vector in FAISS.
    Returns True on success, False on any error.
    """
    try:
        with open(md_path, 'r', encoding='utf-8') as f:
            content = f.read()
        if not content.strip():
            logging.warning(f'Empty markdown file: {md_path}')
            return False
        emb = _hash_embed(content)
        index = _load_or_create_index()
        index.add(emb)
        _save_index(index)
        logging.info(f'Indexed {md_path} into FAISS (dim={EMB_DIM})')
        return True
    except Exception as e:
        logging.error(f'Error indexing {md_path}: {e}')
        return False
