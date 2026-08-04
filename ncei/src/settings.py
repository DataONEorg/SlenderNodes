#!/usr/bin/env python
# -*- coding: utf-8 -*-

""":Mod: settings

:Synopsis:
    Local settings for the NCEI Adapter
:Author:
    servilla
  
:Created:
    3/9/16
"""

import logging
import os


_DEFAULT_LOG_FILE = '/var/local/dataone/adapter_ncei/ncei.log'
_LOG_DIR = os.path.dirname(_DEFAULT_LOG_FILE)
if os.path.isdir(_LOG_DIR):
    _LOG_FILE = _DEFAULT_LOG_FILE
else:
    _LOG_FILE = os.path.join(os.path.dirname(__file__), 'ncei.log')

logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s %(levelname)s (%(name)s): %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S%z',
                    filename=_LOG_FILE,
                    )


MN_BASE_URL = 'https://gmn2.test.dataone.org/mnTestNCEI/mn'
CERTIFICATE_FOR_CREATE = '/var/local/dataone/certs/urn_node_NCEI/urn_node_mnTestNCEI.crt'
CERTIFICATE_FOR_CREATE_KEY = '/var/local/dataone/certs/urn_node_NCEI/private/urn_node_mnTestNCEI.key'
CACHE_PATH = '/var/local/dataone/slendernodes/ncei/content_cache'
CACHE_DB = 'cache.sqlite'
CACHE_REFRESH_FILE = '/var/local/dataone/slendernodes/ncei/src/cache_refresh.txt'
DATE_FORMAT = '%Y-%m-%d %H:%M:%S%z'

NCEI_CSW_URL = 'https://www.ncei.noaa.gov/metadata/geoportal/csw'
NCEI_ISO_URL_TEMPLATE = 'https://www.ncei.noaa.gov/access/metadata/landing-page/bin/iso?id={sid};view=xml;responseType=text/xml'
CSW_PAGE_SIZE = 100
CSW_MAX_ENTRIES = 100
HTTP_TIMEOUT = 60

SCIMETA_FORMAT_ID = 'http://www.isotc211.org/2005/gmd'
SCIMETA_RIGHTS_HOLDER = 'CN=urn:node:mnTestNCEI,DC=dataone,DC=org'
SCIMETA_SUBMITTER = 'CN=urn:node:mnTestNCEI,DC=dataone,DC=org'
SCIMETA_AUTHORITATIVE_MEMBER_NODE = 'urn:node:mnTestNCEI'
SCIMETA_ORIGIN_MEMBER_NODE = 'urn:node:mnTestNCEI'