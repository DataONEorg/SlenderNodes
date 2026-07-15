#!/usr/bin/env python
# -*- coding: utf-8 -*-

import tempfile
import unittest
from datetime import datetime, timezone

from ncei_content_cache import ContentCache


class TestContentCache(unittest.TestCase):

    def test_refresh_and_list_new_since(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            cache = ContentCache(tmp_dir, 'cache.sqlite')
            entries = [
                {
                    'pid': 'sid:1_20260101T000001Z',
                    'sid': 'sid:1',
                    'sci_metadata': b'<xml>v1</xml>',
                    'date_modified': '2026-01-01T00:00:01Z',
                },
                {
                    'pid': 'sid:1_20260102T000001Z',
                    'sid': 'sid:1',
                    'sci_metadata': b'<xml>v2</xml>',
                    'date_modified': '2026-01-02T00:00:01Z',
                },
            ]
            cache.refresh(entries)

            since = datetime(2026, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
            new_records = list(cache.listNewSince(since))

            self.assertEqual(len(new_records), 1)
            self.assertEqual(new_records[0]['pid'], 'sid:1_20260102T000001Z')

    def test_get_predecessor_pid(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            cache = ContentCache(tmp_dir, 'cache.sqlite')
            cache.refresh([
                {
                    'pid': 'sid:2_20260101T000001Z',
                    'sid': 'sid:2',
                    'sci_metadata': b'<xml>a</xml>',
                    'date_modified': '2026-01-01T00:00:01Z',
                },
                {
                    'pid': 'sid:2_20260103T000001Z',
                    'sid': 'sid:2',
                    'sci_metadata': b'<xml>b</xml>',
                    'date_modified': '2026-01-03T00:00:01Z',
                },
            ])

            predecessor = cache.getPredecessorPID('sid:2', '2026-01-03T00:00:01Z')
            self.assertEqual(predecessor, 'sid:2_20260101T000001Z')

            none_predecessor = cache.getPredecessorPID('sid:2', '2026-01-01T00:00:01Z')
            self.assertIsNone(none_predecessor)


if __name__ == '__main__':
    unittest.main()
