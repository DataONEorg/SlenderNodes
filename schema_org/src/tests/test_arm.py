# Standard library imports
try:
    import importlib.resources as ir
except ImportError:  # pragma:  nocover
    import importlib_resources as ir
from unittest.mock import patch

# 3rd party library imports
import requests

# local imports
from schema_org.arm import ARMHarvester
from schema_org.common import SITEMAP_RETRIEVAL_FAILURE_MESSAGE
from .test_common import TestCommon


@patch('schema_org.common.logging.getLogger')
class TestSuite(TestCommon):

    def setUp(self):
        self.site_map = 'https://www.archive.arm.gov/metadata/adc/sitemap.xml'
        self.protocol = 'https'

    def test_identifier_parsing(self, mock_logger):
        """
        SCENARIO:  The @id field from the JSON-LD must be parsed, we are
        presented with http://dx.doi.org/10.5439/1027257.

        EXPECTED RESULT:  The ID "10.5439/1027257" is returned.
        """
        jsonld = {'@id': 'http://dx.doi.org/10.5439/1027257'}
        harvester = ARMHarvester()
        identifier = harvester.extract_identifier(jsonld)

        self.assertEqual(identifier, '10.5439/1027257')

    def test_identifier_parsing_error(self, mock_logger):
        """
        SCENARIO:  The @id field from the JSON-LD must be parsed, but the given
        field is bad.

        EXPECTED RESULT:  RuntimeError and a warning is logged.
        """
        jsonld = {'@id': 'http://dx.doi.orggg/10.5439/1027257'}
        harvester = ARMHarvester()

        with self.assertRaises(RuntimeError):
            harvester.extract_identifier(jsonld)

        self.assertEqual(harvester.logger.error.call_count, 1)

    def test_bad_verbosity(self, mock_logger):
        """
        SCENARIO:  the harvester is called with a bad verbosity value.  This
        should be precluded by the command line entry point, but you never
        know.

        EXPECTED RESULT:  a TypeError is raised
        """

        with self.assertRaises(TypeError):
            ARMHarvester(verbose='WARNING2')

    def test_extraction_of_metadata_url(self, mock_logger):
        """
        SCENARIO:  Retrieve the URL of the XML metadata document given the
        JSON-LD object.

        EXPECTED RESULT:  The expected URL is retrieved.
        """
        expected = (
            'https://www.archive.arm.gov'
            '/metadata/adc/xml/nsaqcrad1longC2.c2.xml'
        )
        jsonld = {'encoding': {'contentUrl': expected}}

        harvester = ARMHarvester()
        actual = harvester.extract_metadata_url(jsonld)

        self.assertEqual(actual, expected)

    @patch('schema_org.d1_client_manager.D1ClientManager.get_last_harvest_time')  # noqa: E501
    def test_invalid_xml(self, mock_harvest_time, mock_logger):
        """
        SCENARIO:  The XML metadata document is invalid.

        EXPECTED RESULT:  The failure count goes up by one.
        """

        mock_harvest_time.return_value = '1900-01-01T00:00:00Z'

        harvester = ARMHarvester()

        # External calls to read the:
        #
        #   1) sitemap
        #   2) HTML document for record 1
        #   3) XML document for record 1
        #
        contents = [
            ir.read_binary('tests.data.arm', 'sitemap-1.xml'),
            ir.read_binary('tests.data.arm', 'nsanimfraod1michC2.c1.html'),
            ir.read_binary('tests.data.arm', 'nsanimfraod1michC2.c1.xml'),
        ]
        status_codes = [200, 200, 400]
        self.setUpRequestsMocking(harvester,
                                  contents=contents, status_codes=status_codes)

        failed_count = harvester.failed_count

        harvester.run()

        self.assertEqual(harvester.failed_count, failed_count + 1)


class TestSuite2(TestCommon):

    def setUp(self):
        self.site_map = 'https://www.archive.arm.gov/metadata/adc/sitemap.xml'
        self.protocol = 'https'

    def test_site_map_retrieval_failure(self):
        """
        SCENARIO:  a non-200 status code is returned by the site map retrieval.

        EXPECTED RESULT:  A requests HTTPError is raised and the exception is
        logged.
        """
        harvester = ARMHarvester(verbosity='INFO')
        self.setUpRequestsMocking(harvester, status_codes=[400])

        with self.assertLogs(logger=harvester.logger, level='INFO') as cm:
            with self.assertRaises(requests.HTTPError):
                harvester.get_sitemap_document(harvester.site_map)
            self.assertErrorMessage(cm.output,
                                    SITEMAP_RETRIEVAL_FAILURE_MESSAGE)
