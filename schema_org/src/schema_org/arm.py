"""
DATAONE adapter for ARM
"""

# Standard library imports
import datetime as dt
import io
import re
import urllib.parse

# 3rd party library imports
import dateutil.parser
import dateutil.tz
import lxml.etree

# Local imports
from .common import CommonHarvester

SITE_NSMAP = {'sitemap': 'http://www.sitemaps.org/schemas/sitemap/0.9'}


class ARMHarvester(CommonHarvester):

    def __init__(self, host='localhost', port=443,
                 certificate=None, private_key=None,
                 verbosity='INFO'):
        super().__init__(host, port, certificate, private_key,
                         id='arm', verbosity=verbosity)

        self.site_map = 'https://www.archive.arm.gov/metadata/adc/sitemap.xml'  # noqa: E501

    def extract_identifier(self, doc, jsonld):
        """
        Parse the DOI from the json['@id'] value.  ARM identifiers
        look something like

            'http://dx.doi.org/10.5439/1027257'

        The DOI in this case would be '10.5439/102757'.  This will be used as
        the series identifier.

        Parameters
        ----------
        JSON-LD obj

        Returns
        -------
        The identifier substring.
        """
        pattern = r'''
            https?://dx.doi.org/(?P<id>10\.\w+/\w+)
        '''
        regex = re.compile(pattern, re.VERBOSE)
        m = regex.search(jsonld['@id'])
        if m is None:
            msg = (
                f"DOI ID parsing error, could not parse an ID out of "
                f"\"{jsonld['@id']}\""
            )
            self.logger.warning(msg)
        else:
            return m.group('id')

        # So it's not where we expected it, in the JSON-LD.  Try other
        # locations.
        try:
            elt = doc.xpath('head/meta[@name="citation_doi"]')[0]
        except IndexError:
            msg = "Alternate head/meta[@name=\"citation_doi\"] path not found"
            self.logger.warning(msg)
            raise RuntimeError(msg)
        else:
            return elt.attrib['content']


    def extract_metadata_url(self, jsonld_doc, landing_page_url):
        """
        Returns
        -------
        The URL for the metadata document.
        """
        p = urllib.parse.urlparse(landing_page_url)

        # Seems a bit dangerous.
        path = p.path.replace('html', 'xml')

        metadata_url = f"{p.scheme}://{p.netloc}{path}"
        return metadata_url

    def get_records(self, last_harvest_time):
        """
        TODO
        """
        r = self.get_site_map()

        # Get a list of URL/modification time pairs.
        doc = lxml.etree.parse(io.BytesIO(r.content))
        urls = doc.xpath('.//sitemap:loc/text()', namespaces=SITE_NSMAP)

        lastmods = doc.xpath('.//sitemap:lastmod/text()',
                             namespaces=SITE_NSMAP)

        # Parse the last modification times.  It is possible that the dates
        # have no timezone information in them, so we will assume that it is
        # UTC.
        lastmods = [dateutil.parser.parse(item) for item in lastmods]
        UTC = dateutil.tz.gettz("UTC")
        lastmods = [
            dateitem.replace(tzinfo=dateitem.tzinfo or UTC)
            for dateitem in lastmods
        ]

        z = zip(urls, lastmods)

        records = [
            (url, lastmod)
            for url, lastmod in z if lastmod >= last_harvest_time
        ]
        return records
