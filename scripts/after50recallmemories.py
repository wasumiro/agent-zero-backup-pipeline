#!/usr/bin/env python3
import os
import logging

log_dir = '/a0/usr/workdir/logs'
os.makedirs(log_dir, exist_ok=True)
log_file = os.path.join(log_dir, 'backup.log')
logging.basicConfig(filename=log_file, level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')
logging.info('Memory recall extension disabled (stub)')
