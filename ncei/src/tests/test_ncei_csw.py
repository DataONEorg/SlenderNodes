#!/usr/bin/env python
# -*- coding: utf-8 -*-

import unittest
from unittest import mock

import ncei_csw


class _FakeResponse(object):

    def __init__(self, text='', content=b'', status_code=200):
        self.text = text
        self.content = content
        self.status_code = status_code

    def raise_for_status(self):
        if self.status_code >= 400:
            raise RuntimeError('HTTP {0}'.format(self.status_code))


class TestNCEICSW(unittest.TestCase):

    def test_parse_csw_search_results(self):
        xml_text = '''<?xml version="1.0" encoding="UTF-8"?>
<csw:GetRecordsResponse xmlns:csw="http://www.opengis.net/cat/csw/3.0"
  xmlns:dc="http://purl.org/dc/elements/1.1/"
  xmlns:dct="http://purl.org/dc/terms/">
  <csw:SearchStatus timestamp="2026-07-09T19:04:34.688Z"/>
  <csw:SearchResults numberOfRecordsMatched="2" numberOfRecordsReturned="2" nextRecord="3">
    <csw:SummaryRecord>
      <dc:identifier>gov.noaa.nodc:123</dc:identifier>
      <dct:modified>2026-07-08T01:02:03Z</dct:modified>
    </csw:SummaryRecord>
    <csw:SummaryRecord>
      <dc:identifier>gov.noaa.nodc:456</dc:identifier>
    </csw:SummaryRecord>
  </csw:SearchResults>
</csw:GetRecordsResponse>
'''
        entries, next_record = ncei_csw.parse_csw_search_results(xml_text)

        self.assertEqual(next_record, 3)
        self.assertEqual(len(entries), 2)
        self.assertEqual(entries[0]['sid'], 'gov.noaa.nodc:123')
        self.assertEqual(entries[0]['date_modified'], '2026-07-08T01:02:03Z')
        self.assertEqual(entries[1]['sid'], 'gov.noaa.nodc:456')
        self.assertEqual(entries[1]['date_modified'], '2026-07-09T19:04:34Z')

    @mock.patch('ncei_csw.requests.get')
    def test_iter_csw_records_paginates(self, mock_get):
        page_1 = '''<?xml version="1.0" encoding="UTF-8"?>
<csw:GetRecordsResponse xmlns:csw="http://www.opengis.net/cat/csw/3.0"
  xmlns:dc="http://purl.org/dc/elements/1.1/"
  xmlns:dct="http://purl.org/dc/terms/">
  <csw:SearchStatus timestamp="2026-07-09T19:04:34.688Z"/>
  <csw:SearchResults numberOfRecordsMatched="3" numberOfRecordsReturned="2" nextRecord="3">
    <csw:SummaryRecord><dc:identifier>gov.noaa.nodc:1</dc:identifier></csw:SummaryRecord>
    <csw:SummaryRecord><dc:identifier>gov.noaa.nodc:2</dc:identifier></csw:SummaryRecord>
  </csw:SearchResults>
</csw:GetRecordsResponse>
'''
        page_2 = '''<?xml version="1.0" encoding="UTF-8"?>
<csw:GetRecordsResponse xmlns:csw="http://www.opengis.net/cat/csw/3.0"
  xmlns:dc="http://purl.org/dc/elements/1.1/"
  xmlns:dct="http://purl.org/dc/terms/">
  <csw:SearchStatus timestamp="2026-07-09T19:04:35.688Z"/>
  <csw:SearchResults numberOfRecordsMatched="3" numberOfRecordsReturned="1" nextRecord="0">
    <csw:SummaryRecord><dc:identifier>gov.noaa.nodc:3</dc:identifier></csw:SummaryRecord>
  </csw:SearchResults>
</csw:GetRecordsResponse>
'''
        mock_get.side_effect = [
            _FakeResponse(text=page_1),
            _FakeResponse(text=page_2),
        ]

        records = list(ncei_csw.iter_csw_records(page_size=2, max_entries=3))
        self.assertEqual([r['sid'] for r in records], [
            'gov.noaa.nodc:1',
            'gov.noaa.nodc:2',
            'gov.noaa.nodc:3',
        ])
        self.assertEqual(mock_get.call_count, 2)

    @mock.patch('ncei_csw.requests.get')
    def test_download_iso_xml(self, mock_get):
        mock_get.return_value = _FakeResponse(content=b'<gmi:MI_Metadata/>')

        content = ncei_csw.download_iso_xml('gov.noaa.nodc:9600144')

        self.assertEqual(content, b'<gmi:MI_Metadata/>')
        called_url = mock_get.call_args[0][0]
        self.assertIn('id=gov.noaa.nodc:9600144', called_url)
        self.assertIn('view=xml', called_url)


if __name__ == '__main__':
    unittest.main()
