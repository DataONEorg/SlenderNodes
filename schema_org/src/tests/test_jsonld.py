"""
Tests for validity of schema.org JSON-LD.
"""

# Standard library imports
import importlib.resources as ir
import json
import logging
# 3rd party library imports

# Local imports
from schema_org.jsonld_validator import JSONLD_Validator
from .test_common import TestCommon

XSD_DATE_MSG = (
    "A dateModified property, if present, should conform to xsd:date or "
    "xsd:datetime patterns."
)


class TestSuite(TestCommon):

    def setUp(self):

        logging.basicConfig(format='%(asctime)s %(levelname)-8s %(message)s',
                            level=logging.DEBUG)
        self.logger = logging.getLogger(__name__)

    def test_missing_top_level_type_key(self):
        """
        SCENARIO:  The JSON-LD does not have the '@type': 'Dataset' keypair.

        EXPECTED RESULT.  A RuntimeError is issued.
        """

        content = ir.read_text('tests.data.jsonld', 'missing_dataset.json')
        j = json.loads(content)

        v = JSONLD_Validator(logger=self.logger)
        with self.assertRaises(RuntimeError):
            v.check(j)

    def test__top_level_id_missing(self):
        """
        SCENARIO:  The JSON-LD is missing the @id entry at the top
        level.

        EXPECTED RESULT.  A RuntimeError is issued.
        """
        s = """
        {
            "@context": { "@vocab": "http://schema.org/" },
            "@type": "Dataset",
            "encoding": {
                "@type": "MediaObject",
                "contentUrl": "https://somewhere.out.there.com/",
                "description": "",
                "dateModified": "2019-08-08T23:59:59"
            }
        }
        """
        j = json.loads(s)

        v = JSONLD_Validator(logger=self.logger)
        with self.assertRaises(RuntimeError):
            v.check(j)

    def test_missing_top_level_type_dataset_keypair(self):
        """
        SCENARIO:  The JSON-LD does not have the '@type': 'Dataset' keypair.

        EXPECTED RESULT.  A RuntimeError is issued.
        """

        j = {'@type': 'Book'}

        v = JSONLD_Validator(logger=self.logger)
        with self.assertRaises(RuntimeError):
            v.check(j)

    def test_dataset_type_is_camelcase(self):
        """
        SCENARIO:  The JSON-LD has "DataSet" instead of "Dataset".

        EXPECTED RESULT.  An error is logged.
        """

        j = {'@type': 'DataSet'}

        v = JSONLD_Validator(logger=self.logger)
        with self.assertRaises(RuntimeError):
            v.check(j)

    def test_missing_top_level_encoding_keyword(self):
        """
        SCENARIO:  The JSON-LD does not have the 'encoding' keyword at the
        top level.

        EXPECTED RESULT.  An error is logged.
        """
        s = """
        {
            "@context": { "@vocab": "http://schema.org/" },
            "@type": "Dataset"
        }
        """
        j = json.loads(s)

        v = JSONLD_Validator(logger=self.logger)
        with self.assertLogs(logger=v.logger, level='DEBUG') as cm:
            with self.assertRaises(RuntimeError):
                v.check(j)
            return

            expected = "JSON-LD is missing a top-level encoding keyword."
            self.assertErrorLogMessage(cm.output, expected)

    def test__encoding__missing_contentUrl_keyword(self):
        """
        SCENARIO:  The JSON-LD does not have the 'contentUrl' keyword in the
        'encoding' block.

        EXPECTED RESULT.  An error is logged.
        """
        s = """
        {
            "@context": { "@vocab": "http://schema.org/" },
            "@type": "Dataset",
            "@id": "http://dx.doi.org/10.5439/1027372",
            "identifier": "thing",
            "encoding": {
                "@type": "MediaObject",
                "description": "",
                "dateModified": "2002-04-04"
            }
        }
        """
        j = json.loads(s)

        v = JSONLD_Validator(logger=self.logger)
        with self.assertLogs(logger=v.logger, level='INFO') as cm:
            with self.assertRaises(RuntimeError):
                v.check(j)
            expected = (
                "A contentUrl must provide the location of the metadata "
                "encoding."
            )
            self.assertErrorLogMessage(cm.output, expected)

    def test__encoding__missing_description_keyword(self):
        """
        SCENARIO:  The JSON-LD does not have the 'description' keyword in the
        'encoding' block.

        EXPECTED RESULT.  An warning is logged.
        """
        s = """
        {
            "@context": { "@vocab": "http://schema.org/" },
            "@type": "Dataset",
            "@id": "http://dx.doi.org/10.5439/1027372",
            "encoding": {
                "@type": "MediaObject",
                "contentUrl": "https://somewhere.out.there.com/",
                "dateModified": "2004-02-02"
            },
            "identifier": {
                "@type": "PropertyValue",
                "value": "something"
            }
        }
        """
        j = json.loads(s)

        v = JSONLD_Validator(logger=self.logger)
        with self.assertLogs(logger=v.logger, level='INFO') as cm:
            v.check(j)
            expected = 'A description property is recommended.'
            self.assertWarningLogMessage(cm.output, expected)
            self.assertLogLevelCallCount(cm.output, level='ERROR', n=0)

    def test__encoding__missing_dateModified_keyword(self):
        """
        SCENARIO:  The JSON-LD does not have the 'dateModified' keyword in the
        'encoding' block.

        EXPECTED RESULT.  An warning is logged, as dateModified is optional.
        """
        s = """
        {
            "@context": { "@vocab": "http://schema.org/" },
            "@type": "Dataset",
            "@id": "http://dx.doi.org/10.5439/1027372",
            "identifier": "thing",
            "encoding": {
                "@type": "MediaObject",
                "contentUrl": "https://somewhere.out.there.com/",
                "description": ""
            }
        }
        """
        j = json.loads(s)

        v = JSONLD_Validator(logger=self.logger)
        with self.assertLogs(logger=v.logger, level='INFO') as cm:
            v.check(j)

            expected = (
                'A dateModified property indicating when the encoding was '
                'last updated is recommended.'
            )
            self.assertWarningLogMessage(cm.output, expected)
            self.assertErrorLogCallCount(cm.output, n=0)

    def test__encoding__dateModified_is_date(self):
        """
        SCENARIO:  The JSON-LD has the 'dateModified' keyword in the date
        format.

        EXPECTED RESULT.  No errors or warnings are logged.
        """
        s = """
        {
            "@context": { "@vocab": "http://schema.org/" },
            "@type": "Dataset",
            "@id": "http://dx.doi.org/10.5439/1027372",
            "identifier": "thing",
            "encoding": {
                "@type": "MediaObject",
                "contentUrl": "https://somewhere.out.there.com/",
                "description": "",
                "dateModified": "2019-08-02"
            }
        }
        """
        j = json.loads(s)

        v = JSONLD_Validator(logger=self.logger)
        with self.assertLogs(logger=v.logger, level='INFO') as cm:
            v.check(j)
            self.assertLogLevelCallCount(cm.output, level='ERROR', n=0)

    def test__encoding__dateModified_is_invalid_date__month_00(self):
        """
        SCENARIO:  The JSON-LD has the 'dateModified' keyword that is not in
        a valid date or datetime format.  "19" is invalid.

        EXPECTED RESULT.  A RuntimeError is raised and the error is logged.
        """
        s = """
        {
            "@context": { "@vocab": "http://schema.org/" },
            "@type": "Dataset",
            "@id": "http://dx.doi.org/10.5439/1027372",
            "identifier": "thing",
            "encoding": {
                "@type": "MediaObject",
                "contentUrl": "https://somewhere.out.there.com/",
                "description": "",
                "dateModified": "2019-00-08"
            }
        }
        """
        j = json.loads(s)

        v = JSONLD_Validator(logger=self.logger)
        with self.assertLogs(logger=v.logger, level='DEBUG') as cm:
            with self.assertRaises(RuntimeError):
                v.check(j)

            self.assertErrorLogMessage(cm.output, XSD_DATE_MSG)

    def test__encoding__dateModified_is_invalid_date__month_19(self):
        """
        SCENARIO:  The JSON-LD has the 'dateModified' keyword that is not in
        a valid date or datetime format.  "19" is invalid.

        EXPECTED RESULT.  A RuntimeError is raised and the error is logged.
        """
        s = """
        {
            "@context": { "@vocab": "http://schema.org/" },
            "@type": "Dataset",
            "@id": "http://dx.doi.org/10.5439/1027372",
            "identifier": "thing",
            "encoding": {
                "@type": "MediaObject",
                "contentUrl": "https://somewhere.out.there.com/",
                "description": "",
                "dateModified": "2019-19-08"
            }
        }
        """
        j = json.loads(s)

        v = JSONLD_Validator(logger=self.logger)
        with self.assertLogs(logger=v.logger, level='DEBUG') as cm:
            with self.assertRaises(RuntimeError):
                v.check(j)

            self.assertErrorLogMessage(cm.output, XSD_DATE_MSG)

    def test__encoding__dateModified_is_invalid_date__month_20(self):
        """
        SCENARIO:  The JSON-LD has the 'dateModified' keyword that is not in
        a valid date or datetime format.  "20" is invalid.

        EXPECTED RESULT.  A RuntimeError is raised and the error is logged.
        """
        s = """
        {
            "@context": { "@vocab": "http://schema.org/" },
            "@type": "Dataset",
            "@id": "http://dx.doi.org/10.5439/1027372",
            "identifier": "thing",
            "encoding": {
                "@type": "MediaObject",
                "contentUrl": "https://somewhere.out.there.com/",
                "description": "",
                "dateModified": "2019-20-08"
            }
        }
        """
        j = json.loads(s)

        v = JSONLD_Validator(logger=self.logger)
        with self.assertLogs(logger=v.logger, level='DEBUG') as cm:
            with self.assertRaises(RuntimeError):
                v.check(j)

            self.assertErrorLogMessage(cm.output, XSD_DATE_MSG)

    def test__encoding__dateModified_is_invalid_date__day_not_numeric(self):
        """
        SCENARIO:  The JSON-LD has the 'dateModified' keyword that is not in
        a valid date or datetime format.

        EXPECTED RESULT.  A RuntimeError is raised and the error is logged.
        """
        s = """
        {
            "@context": { "@vocab": "http://schema.org/" },
            "@type": "Dataset",
            "@id": "http://dx.doi.org/10.5439/1027372",
            "identifier": "thing",
            "encoding": {
                "@type": "MediaObject",
                "contentUrl": "https://somewhere.out.there.com/",
                "description": "",
                "dateModified": "2019-08-0A"
            }
        }
        """
        j = json.loads(s)

        v = JSONLD_Validator(logger=self.logger)
        with self.assertLogs(logger=v.logger, level='DEBUG') as cm:
            with self.assertRaises(RuntimeError):
                v.check(j)

            self.assertErrorLogMessage(cm.output, XSD_DATE_MSG)

    def test__encoding__dateModified_has_invalid_hours1(self):
        """
        SCENARIO:  The JSON-LD has the 'dateModified' keyword that is not in
        a valid date or datetime format.  A value of 29 is an invalid hour.

        EXPECTED RESULT.  A RuntimeError is raised and the error is logged.
        """
        s = """
        {
            "@context": { "@vocab": "http://schema.org/" },
            "@type": "Dataset",
            "@id": "http://dx.doi.org/10.5439/1027372",
            "identifier": "thing",
            "encoding": {
                "@type": "MediaObject",
                "contentUrl": "https://somewhere.out.there.com/",
                "description": "",
                "dateModified": "2019-08-08T29:59:59"
            }
        }
        """
        j = json.loads(s)

        v = JSONLD_Validator(logger=self.logger)
        with self.assertLogs(logger=v.logger, level='INFO') as cm:
            with self.assertRaises(RuntimeError):
                v.check(j)

            print('\n'.join(cm.output))
            self.assertErrorLogMessage(cm.output, XSD_DATE_MSG)

    def test__encoding__dateModified_has_invalid_hours2(self):
        """
        SCENARIO:  The JSON-LD has the 'dateModified' keyword that is not in
        a valid date or datetime format.  A value of 31 is an invalid hour.

        EXPECTED RESULT.  A RuntimeError is raised and the error is logged.
        """
        s = """
        {
            "@context": { "@vocab": "http://schema.org/" },
            "@type": "Dataset",
            "@id": "http://dx.doi.org/10.5439/1027372",
            "identifier": "thing",
            "encoding": {
                "@type": "MediaObject",
                "contentUrl": "https://somewhere.out.there.com/",
                "description": "",
                "dateModified": "2019-08-08T31:59:59"
            }
        }
        """
        j = json.loads(s)

        v = JSONLD_Validator(logger=self.logger)
        with self.assertLogs(logger=v.logger, level='INFO') as cm:
            with self.assertRaises(RuntimeError):
                v.check(j)

            print('\n'.join(cm.output))
            self.assertErrorLogMessage(cm.output, XSD_DATE_MSG)

    def test__encoding__dateModified_has_invalid_minutes(self):
        """
        SCENARIO:  The JSON-LD has the 'dateModified' keyword that is not in
        a valid date or datetime format.  The minutes are invalid.

        EXPECTED RESULT.  A RuntimeError is raised and the error is logged.
        """
        s = """
        {
            "@context": { "@vocab": "http://schema.org/" },
            "@type": "Dataset",
            "@id": "http://dx.doi.org/10.5439/1027372",
            "identifier": "thing",
            "encoding": {
                "@type": "MediaObject",
                "contentUrl": "https://somewhere.out.there.com/",
                "description": "",
                "dateModified": "2019-08-08T23:69:59"
            }
        }
        """
        j = json.loads(s)

        v = JSONLD_Validator(logger=self.logger)
        with self.assertLogs(logger=v.logger, level='INFO') as cm:
            with self.assertRaises(RuntimeError):
                v.check(j)

            print('\n'.join(cm.output))
            self.assertErrorLogMessage(cm.output, XSD_DATE_MSG)

    def test__encoding__dateModified_is_invalid_datetime__seconds(self):
        """
        SCENARIO:  The JSON-LD has the 'dateModified' keyword that is not in
        a valid date or datetime format.

        EXPECTED RESULT.  A RuntimeError is raised and the error is logged.
        """
        s = """
        {
            "@context": { "@vocab": "http://schema.org/" },
            "@type": "Dataset",
            "@id": "http://dx.doi.org/10.5439/1027372",
            "identifier": "thing",
            "encoding": {
                "@type": "MediaObject",
                "contentUrl": "https://somewhere.out.there.com/",
                "description": "",
                "dateModified": "2019-08-08T23:59:70"
            }
        }
        """
        j = json.loads(s)

        v = JSONLD_Validator(logger=self.logger)
        with self.assertLogs(logger=v.logger, level='INFO') as cm:
            with self.assertRaises(RuntimeError):
                v.check(j)

            print('\n'.join(cm.output))
            self.assertErrorLogMessage(cm.output, XSD_DATE_MSG)

    def test__identifier_block_missing(self):
        """
        SCENARIO:  The JSON-LD is missing the identifier section at the top
        level.

        EXPECTED RESULT.  An error is logged.
        """
        s = """
        {
            "@context": { "@vocab": "http://schema.org/" },
            "@type": "Dataset",
            "@id": "http://dx.doi.org/10.5439/1027372",
            "encoding": {
                "@type": "MediaObject",
                "contentUrl": "https://somewhere.out.there.com/",
                "description": "",
                "dateModified": "2019-08-08T23:59:59"
            }
        }
        """
        j = json.loads(s)

        v = JSONLD_Validator(logger=self.logger)
        with self.assertLogs(logger=v.logger, level='DEBUG') as cm:
            with self.assertRaises(RuntimeError):
                v.check(j)
            expected = 'A dataset must have an identifier.'
            self.assertErrorLogMessage(cm.output, expected)
