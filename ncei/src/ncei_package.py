#!/usr/bin/env python
# -*- coding: utf-8 -*-

""":Mod: ncei_package

:Synopsis:
    Helper package to access contents of an NCEI data package

:Author:
    servilla
  
:Created:
    2/11/16
"""

import logging
from datetime import datetime, timezone

from ncei_csw import download_iso_xml


logger = logging.getLogger('ncei_package')


class Package(object):

    def __init__(self, csw_record=None):
        try:
            sid = csw_record['sid']
            date_modified = csw_record['date_modified']
            self.package = {
                'sid': sid,
                'pid': self._build_pid(sid, date_modified),
                'date_modified': date_modified,
                'science_metadata': {
                    'document': download_iso_xml(sid),
                },
            }
        except Exception as e:
            logger.error('Failed to load NCEI package - {0}'.format(str(e)))

    def _build_pid(self, sid, modified):
        text = str(modified).strip()
        if text.endswith('Z'):
            text = text[:-1] + '+00:00'
        dt = datetime.fromisoformat(text)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        suffix = dt.astimezone(timezone.utc).strftime('%Y%m%dT%H%M%SZ')
        return '{0}_{1}'.format(sid, suffix)

    def get_pid(self):
        return self.package['pid']

    def get_sid(self):
        return self.package['sid']

    def get_manifest(self):
        return []

    def get_metadata(self):
        return self.package['science_metadata']

    def get_data(self):
        return []

    def get_resource_map(self):
        return None


class Science_Metadata(Package):

    def get_document(self):
        return self.package['science_metadata']['document']

    def get_sysmeta(self):
        return None


def main():
    return 0

if __name__ == "__main__":
    main()