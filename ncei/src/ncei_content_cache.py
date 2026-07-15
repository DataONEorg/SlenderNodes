#!/usr/bin/env python
# -*- coding: utf-8 -*-

""":Mod: ncei_content_cache

:Synopsis:
    Local SQLite content cache used by NCEI adapter scripts.
"""

import os
import sqlite3
from datetime import datetime, timezone

def _normalize_datetime(value):
    if isinstance(value, datetime):
        dt = value
    else:
        text = str(value).strip()
        if text.endswith('Z'):
            text = text[:-1] + '+00:00'
        try:
            dt = datetime.fromisoformat(text)
        except ValueError:
            for fmt in ('%Y-%m-%d %H:%M:%S%z', '%Y-%m-%d %H:%M:%S', '%Y-%m-%dT%H:%M:%S'):
                try:
                    dt = datetime.strptime(text, fmt)
                    break
                except ValueError:
                    dt = None
            if dt is None:
                raise

    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')


class ContentCache(object):

    def __init__(self, cache_path, cache_db):
        if not os.path.isdir(cache_path):
            os.makedirs(cache_path)
        db_path = os.path.join(cache_path, cache_db)
        self.conn = sqlite3.connect(db_path)
        self.conn.row_factory = sqlite3.Row
        self._init_schema()

    def _init_schema(self):
        cursor = self.conn.cursor()
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS content_cache (
                pid TEXT PRIMARY KEY,
                sid TEXT NOT NULL,
                sci_metadata BLOB NOT NULL,
                date_modified TEXT NOT NULL
            )
            """
        )
        cursor.execute(
            'CREATE INDEX IF NOT EXISTS idx_content_cache_sid ON content_cache(sid)'
        )
        cursor.execute(
            'CREATE INDEX IF NOT EXISTS idx_content_cache_modified ON content_cache(date_modified)'
        )
        self.conn.commit()

    def refresh(self, entries):
        cursor = self.conn.cursor()
        for entry in entries:
            date_modified = _normalize_datetime(entry['date_modified'])
            cursor.execute(
                'INSERT OR REPLACE INTO content_cache (pid, sid, sci_metadata, date_modified) VALUES (?, ?, ?, ?)',
                (entry['pid'], entry['sid'], entry['sci_metadata'], date_modified)
            )
        self.conn.commit()

    def listNewSince(self, since_dt):
        since_text = _normalize_datetime(since_dt.isoformat())
        cursor = self.conn.cursor()
        cursor.execute(
            'SELECT pid, sid, sci_metadata, date_modified FROM content_cache WHERE date_modified > ? ORDER BY date_modified ASC',
            (since_text,)
        )
        for row in cursor.fetchall():
            yield {
                'pid': row['pid'],
                'sid': row['sid'],
                'sci_metadata': row['sci_metadata'],
                'date_modified': row['date_modified'],
            }

    def getPredecessorPID(self, sid, date_modified):
        modified_text = _normalize_datetime(date_modified)
        cursor = self.conn.cursor()
        cursor.execute(
            'SELECT pid FROM content_cache WHERE sid = ? AND date_modified < ? ORDER BY date_modified DESC LIMIT 1',
            (sid, modified_text)
        )
        row = cursor.fetchone()
        if row is None:
            return None
        return row['pid']
