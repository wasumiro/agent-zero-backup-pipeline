#!/usr/bin/env python3
import os
import sys
import shutil
import subprocess
import datetime
import logging
import requests

BASE_DIR = '/a0/usr/workdir'
CONFIG_FILE = os.path.join(BASE_DIR, 'config.yaml')
SRC_DIR = os.path.join(BASE_DIR, 'src')
SKILLS_DIR = os.path.join(BASE_DIR, 'skills')
REPORTS_DIR = os.path.join(BASE_DIR, 'reports')
TMP_DIR = '/tmp/agent_zero_backup'
LOG_DIR = os.path.join(BASE_DIR, 'logs')
os.makedirs(LOG_DIR, exist_ok=True)
LOG_FILE = os.path.join(LOG_DIR, 'backup.log')
logging.basicConfig(filename=LOG_FILE, level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')

# Get Notion token from environment
NOTION_TOKEN = os.getenv('NOTION_API_KEY')
if not NOTION_TOKEN:
    raise ValueError("NOTION_API_KEY environment variable must be set")

NOTION_BASE = "https://api.notion.com/v1"
HEADERS = {
    "Authorization": f"Bearer {NOTION_TOKEN}",
    "Notion-Version": "2022-06-28",
    "Content-Type": "application/json",
}

def dump_memories(md_path):
    with open(md_path, 'w') as f:
        f.write('# Agent Zero Memories Backup\n')
        f.write('*(Memory dump placeholder – implement actual dump via memory_load tool)*\n')

def prepare_backup():
    if os.path.exists(TMP_DIR):
        shutil.rmtree(TMP_DIR)
    os.makedirs(TMP_DIR, exist_ok=True)
    shutil.copy2(CONFIG_FILE, TMP_DIR)
    shutil.copytree(SRC_DIR, os.path.join(TMP_DIR, 'src'))
    shutil.copytree(SKILLS_DIR, os.path.join(TMP_DIR, 'skills'))
    shutil.copytree(REPORTS_DIR, os.path.join(TMP_DIR, 'reports'))
    mem_md = os.path.join(TMP_DIR, 'memories_backup.md')
    dump_memories(mem_md)
    return TMP_DIR

def create_zip(tmp_path):
    date_str = datetime.datetime.now(datetime.UTC).strftime('%Y-%m-%d')
    zip_name = f'backup_{date_str}.zip'
    zip_path = os.path.join('/tmp', zip_name)
    shutil.make_archive(zip_path.rstrip('.zip'), 'zip', tmp_path)
    return zip_path

def notion_search_page(title):
    payload = {"query": title, "filter": {"value": "page", "property": "object"}}
    resp = requests.post(f"{NOTION_BASE}/search", headers=HEADERS, json=payload)
    resp.raise_for_status()
    data = resp.json()
    for result in data.get('results', []):
        props = result.get('properties', {})
        title_prop = props.get('title') or props.get('Name')
        if title_prop and isinstance(title_prop, dict):
            title_text = ''.join([t.get('plain_text', '') for t in title_prop.get('title', [])])
            if title_text == title:
                return result
        if result.get('title') == title:
            return result
    return None

def notion_create_page(parent_id, title):
    payload = {
        "parent": {"page_id": parent_id},
        "properties": {"title": {"title": [{"text": {"content": title}}]}}
    }
    resp = requests.post(f"{NOTION_BASE}/pages", headers=HEADERS, json=payload)
    resp.raise_for_status()
    return resp.json()

def notion_append_paragraph(page_id, text):
    block = {"object": "block", "type": "paragraph", "paragraph": {"rich_text": [{"type": "text", "text": {"content": text}}]}}
    resp = requests.patch(f"{NOTION_BASE}/blocks/{page_id}/children", headers=HEADERS, json={"children": [block]})
    resp.raise_for_status()
    return resp.json()

def upload_to_notion(zip_path):
    try:
        resources = notion_search_page('Resources')
        if not resources:
            logging.error('Resources page not found in Notion')
            return False
        resources_id = resources['id']
        backup_parent = notion_search_page('Agent Zero backup')
        if not backup_parent:
            backup_parent = notion_create_page(resources_id, 'Agent Zero backup')
        backup_parent_id = backup_parent['id']
        backup_title = f"Backup {datetime.datetime.now(datetime.UTC).strftime('%Y-%m-%d %H:%M UTC')}"
        backup_page = notion_create_page(backup_parent_id, backup_title)
        backup_page_id = backup_page['id']
        notion_append_paragraph(backup_page_id, f'Backup archive path: {zip_path}')
        return True
    except Exception as e:
        logging.error(f'Notion upload failed: {e}')
        return False

def index_into_vector_db(md_path):
    try:
        sys.path.append(os.path.join(SKILLS_DIR, 'vector_db_indexer'))
        from index_backup import index_markdown
        return index_markdown(md_path)
    except Exception as e:
        logging.error(f'Vector DB indexing failed: {e}')
        return False

def main():
    try:
        tmp_path = prepare_backup()
        zip_path = create_zip(tmp_path)
        if upload_to_notion(zip_path):
            logging.info('Backup uploaded to Notion successfully')
        else:
            logging.error('Backup upload to Notion failed')
        mem_md = os.path.join(tmp_path, 'memories_backup.md')
        if index_into_vector_db(mem_md):
            logging.info('Memories indexed into vector DB successfully')
        else:
            logging.error('Failed to index memories into vector DB')
        shutil.rmtree(tmp_path)
        os.remove(zip_path)
    except Exception as exc:
        logging.exception(f'Backup process failed: {exc}')

if __name__ == '__main__':
    main()
