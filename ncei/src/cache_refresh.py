#!/usr/bin/env python
# -*- coding: utf-8 -*-

""":Mod: cache_refresh

:Synopsis:

:Author:
    servilla
  
:Created:
    3/15/16
"""

import logging
from datetime import datetime, timezone

from ncei_content_cache import ContentCache
from ncei_csw import iter_csw_records, download_iso_xml
import settings


logger = logging.getLogger('cache_refresh')


def _build_pid(sid, modified):
    text = str(modified).strip()
    if text.endswith('Z'):
        text = text[:-1] + '+00:00'
    dt = datetime.fromisoformat(text)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    suffix = dt.astimezone(timezone.utc).strftime('%Y%m%dT%H%M%SZ')
    return '{0}_{1}'.format(sid, suffix)


def main():

    cache = ContentCache(settings.CACHE_PATH, settings.CACHE_DB)
    entries = []

    for record in iter_csw_records(
            page_size=settings.CSW_PAGE_SIZE,
            max_entries=settings.CSW_MAX_ENTRIES):
        sid = record['sid']
        date_modified = record['date_modified']
        pid = _build_pid(sid, date_modified)
        sci_metadata = download_iso_xml(sid)
        entries.append({
            'pid': pid,
            'sid': sid,
            'sci_metadata': sci_metadata,
            'date_modified': date_modified,
        })

    logger.info('Refreshing cache with %d records at %s', len(entries), datetime.utcnow().isoformat())
    cache.refresh(entries)

    return 0


if __name__ == "__main__":
    main()