#!/usr/bin/env python
# -*- coding: utf-8 -*-

""":Mod: ncei_csw

:Synopsis:
    Helpers for retrieving NCEI records from CSW and downloading ISO metadata by SID.
"""

import logging
from datetime import datetime, timezone
import xml.etree.ElementTree as ET

import requests

import settings


logger = logging.getLogger('ncei_csw')


NS = {
    'csw': 'http://www.opengis.net/cat/csw/3.0',
    'dc': 'http://purl.org/dc/elements/1.1/',
    'dct': 'http://purl.org/dc/terms/',
}


def _parse_datetime(value):
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
    return dt


def normalize_datetime_str(date_str):
    """Normalize a date string to UTC ISO 8601 with trailing Z."""
    dt = _parse_datetime(date_str)
    return dt.astimezone(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')


def parse_csw_search_results(xml_text):
    """Parse a CSW GetRecords response and return entries with pagination info."""
    root = ET.fromstring(xml_text)
    search_status = root.find('csw:SearchStatus', NS)
    default_timestamp = None
    if search_status is not None:
        default_timestamp = search_status.get('timestamp')

    search_results = root.find('csw:SearchResults', NS)
    if search_results is None:
        return [], 0

    next_record = int(search_results.get('nextRecord', '0'))
    entries = []

    for summary in search_results.findall('csw:SummaryRecord', NS):
        sid_el = summary.find('dc:identifier', NS)
        if sid_el is None or sid_el.text is None:
            continue

        sid = sid_el.text.strip()
        modified_el = summary.find('dct:modified', NS)
        modified = default_timestamp
        if modified_el is not None and modified_el.text:
            modified = modified_el.text.strip()

        if modified is None:
            # Last-resort value so downstream consumers still have ordering data.
            modified = '1970-01-01T00:00:00Z'

        entries.append({
            'sid': sid,
            'date_modified': normalize_datetime_str(modified),
        })

    return entries, next_record


def iter_csw_records(csw_url=None, start_position=1, page_size=100, max_entries=None):
    """Yield CSW records from the configured NCEI endpoint."""
    if csw_url is None:
        csw_url = settings.NCEI_CSW_URL

    count = 0
    start = int(start_position)

    while True:
        params = {
            'request': 'GetRecords',
            'service': 'CSW',
            'version': '3.0.0',
            'typeNames': 'csw:Record',
            'elementSetName': 'summary',
            'resultType': 'results',
            'startPosition': start,
            'maxRecords': page_size,
        }

        response = requests.get(csw_url, params=params, timeout=settings.HTTP_TIMEOUT)
        response.raise_for_status()
        page_entries, next_record = parse_csw_search_results(response.text)

        if not page_entries:
            break

        for record in page_entries:
            yield record
            count += 1
            if max_entries is not None and count >= max_entries:
                return

        if next_record <= start or next_record == 0:
            break
        start = next_record


def iso_url_for_sid(sid):
    return settings.NCEI_ISO_URL_TEMPLATE.format(sid=sid)


def download_iso_xml(sid):
    """Download ISO 19115 XML for an NCEI SID."""
    url = iso_url_for_sid(sid)
    response = requests.get(url, timeout=settings.HTTP_TIMEOUT)
    response.raise_for_status()
    logger.debug('Downloaded ISO for SID %s from %s', sid, url)
    return response.content
