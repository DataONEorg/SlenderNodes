"""
DATAONE adapter for ARM
"""

# Standard library imports
import re

# Local imports
from .common import CommonHarvester

SITE_NSMAP = {'sitemap': 'http://www.sitemaps.org/schemas/sitemap/0.9'}


class ARMHarvester(CommonHarvester):

    def __init__(self, **kwargs):
        super().__init__(id='arm', **kwargs)

        self.site_map = 'https://www.archive.arm.gov/metadata/adc/sitemap.xml'  # noqa: E501

    def extract_identifier(self, jsonld):
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
                f"JSON-LD '@id' element \"{jsonld['@id']}\""
            )
            self.logger.error(msg)
            raise RuntimeError(msg)
        else:
            return m.group('id')
