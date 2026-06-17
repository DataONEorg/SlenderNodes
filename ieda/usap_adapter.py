#!/usr/bin/env python
# -*- coding: utf-8 -*-

# This work was created by participants in the DataONE project, and is
# jointly copyrighted by participating institutions in DataONE. For
# more information on DataONE, see our web site at http://dataone.org.
#
#   Copyright 2009-2017 DataONE
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""USAP Slender Node Adapter

Sitemap: https://www.usap-dc.org/view/dataset/sitemap.xml

The links on the sitemap pages get dataset landing pages that have the SDO
JSON-LD scripts in the html header.

Note that there's no ability to support archival in this approach (unless one
attempts to track when a record identifier used to appear but no longer does).

USAP is no longer being served by IEDA, so we have changed the way the adapter
gets USAP data by breaking the existing IEDA adapter into a separate USAP
adapter.
"""
import datetime
import io
import logging
import os
import pprint
import requests
import sys
import xml.etree.ElementTree as ET

import d1_client.mnclient_2_0
import d1_common.checksum
import d1_common.const
import d1_common.date_time
import d1_common.system_metadata
import d1_common.types.dataoneTypes_v2_0 as v2
import d1_common.types.exceptions
import d1_common.wrap.access_policy
import d1_common.xml

import d1_client
import schema_org
import d1_common.util
import d1_common.url

from usap_config import *

SCIMETA_FORMAT_ID = 'http://www.isotc211.org/2005/gmd'

NS_DICT = {
    'gmd': 'http://www.isotc211.org/2005/gmd',
    'gco': 'http://www.isotc211.org/2005/gco',
}


def main():
    d1_common.util.log_setup()

    for sitemap_idx, site_dict in enumerate(SITEMAP_LIST):
        try:
            proc_sitemap(sitemap_idx, len(SITEMAP_LIST), site_dict)
        except Exception:
            logging.exception(
                'Unable to process sitemap. site_dict={}'.format(site_dict))


def proc_sitemap(sitemap_idx, sitemap_count, site_dict):
    logging.info('#' * 100)
    logging.info('Processing site. idx={}/{}. site_dict={}'.format(
        sitemap_idx + 1, sitemap_count, pprint.pformat(site_dict))
    )

    sitemap_url = d1_common.url.joinPathElements(SITEMAP_ROOT, site_dict['sitemap'])
    gmn_base_url = d1_common.url.joinPathElements(GMN_BASE_URL, site_dict['gmn_path'])
    cert_pem_path = os.path.join(CERT_PATH_ROOT, site_dict['cert_pem_path'])
    cert_key_path = os.path.join(CERT_PATH_ROOT, site_dict['cert_key_path'])

    logging.info('sitemap_url="{}"'.format(sitemap_url))
    logging.info('gmn_base_url="{}"'.format(gmn_base_url))
    logging.info('cert_pem_path="{}"'.format(cert_pem_path))
    logging.info('cert_key_path="{}"'.format(cert_key_path))

    resource_list = schema_org.load_resources_from_sitemap(sitemap_url)

    logging.info('Found resources: {}'.format(len(resource_list)))

    gmn_client = create_gmn_client(gmn_base_url, cert_pem_path, cert_key_path)

    for resource_idx, resource_dict in enumerate(resource_list):
        try:
            proc_resource(resource_idx, len(resource_list), resource_dict, gmn_client)
        except Exception:
            logging.exception(
                'Unable to process resource. resource_idx={}'.format(resource_idx))


def proc_resource(resource_idx, resource_count, resource_dict, gmn_client):
    logging.info('-' * 100)
    logging.info('Processing resource. idx={}/{}. resource_dict={}'.format(
        resource_idx + 1, resource_count, pprint.pformat(resource_dict))
    )

    entry_dict = schema_org.load_schema_org(resource_dict)

    result_dict = {
        **resource_dict,
        **entry_dict,
    }

    # {
    #   'date_modified': '2018-01-25T15:55:08-05:00',
    #   'id': 'doi:10.7265/N5F47M23',
    #   'metadata_format': None,
    #   'metadata_url': 'http://get.iedadata.org/metadata/iso/usap/609539iso.xml',
    #   'url': 'http://get.iedadata.org/metadata/iso/609539'
    # }

    logging.info('result_dict={}'.format(pprint.pformat(result_dict)))

    if 'error' in result_dict:
        logging.error(
            'error="{}" url="{}"'.format(result_dict['error'], result_dict['url'])
        )
        return

    sid = result_dict['id']
    pid = result_dict['url']

    logging.info('schema.org. sid="{}" pid="{}"'.format(sid, pid))

    if is_in_gmn(gmn_client, pid):
        logging.info('Skipped. Already in GMN. sid="{}" pid="{}"'.format(sid, pid))
        return

    scimeta_xml_bytes = download_scimeta_xml(result_dict['metadata_url'])

    pid_sysmeta_pyxb = generate_system_metadata(scimeta_xml_bytes, pid, sid)

    logging.info('pid_sysmeta_pyxb:')
    logging.info(d1_common.xml.serialize_to_xml_str(pid_sysmeta_pyxb))

    head_sysmeta_pyxb = get_sysmeta(gmn_client, sid)

    if head_sysmeta_pyxb:
        logging.info('head_sysmeta_pyxb:')
        logging.info(d1_common.xml.serialize_to_xml_str(head_sysmeta_pyxb))

        head_pid = head_sysmeta_pyxb.identifier.value()
        logging.info(
            'SID already exists on GMN. Adding to chain. head_pid="{}"'
                .format(head_pid)
        )
        # print('1'*100)
        gmn_client.update(
            head_pid, io.BytesIO(scimeta_xml_bytes), pid, pid_sysmeta_pyxb
        )
        # print('2'*100)
    else:
        # print('3'*100)
        logging.info(
            'SID does not exist on GMN. Starting new chain. pid="{}"'.format(pid)
        )
        gmn_client.create(pid, io.BytesIO(scimeta_xml_bytes), pid_sysmeta_pyxb)
        # print('4'*100)


def download_scimeta_xml(scimeta_url):
    try:
        return requests.get(scimeta_url).content
    except requests.HTTPError as e:
        raise AdapterException(
            'Unable to download SciMeta. error="{}"'.format(str(e))
        )


def parse_doi(iso_xml):
    """Get the DOI from an ISO XML doc"""
    tree = ET.parse(iso_xml)
    root = tree.getroot()
    doi_el = root.findall(
        '.gmd:identificationInfo/gmd:MD_DataIdentification/gmd:citation/'
        'gmd:CI_Citation/gmd:identifier/gmd:MD_Identifier/gmd:code/'
        'gco:CharacterString', NS_DICT
    )[0]
    return doi_el.text.strip()


def create_gmn_client(gmn_base_url, cert_pem_path, cert_key_path):
    return d1_client.mnclient_2_0.MemberNodeClient_2_0(
        base_url=gmn_base_url,
        cert_pem_path=cert_pem_path,
        cert_key_path=cert_key_path,
        # retries=1,
    )


def is_in_gmn(gmn_client, did):
    try:
        gmn_client.getSystemMetadata(did)
    except d1_common.types.exceptions.NotFound:
        return False
    return True


def get_sysmeta(gmn_client, sid):
    try:
        return gmn_client.getSystemMetadata(sid)
    except d1_common.types.exceptions.NotFound:
        return None


def generate_system_metadata(scimeta_bytes, pid, sid):
    sysmeta_pyxb = v2.systemMetadata()
    sysmeta_pyxb.seriesId = sid
    sysmeta_pyxb.formatId = SCIMETA_FORMAT_ID
    sysmeta_pyxb.size = len(scimeta_bytes)
    sysmeta_pyxb.checksum = d1_common.checksum.create_checksum_object_from_stream(
        io.BytesIO(scimeta_bytes))
    sysmeta_pyxb.identifier = pid
    sysmeta_pyxb.dateUploaded = d1_common.date_time.utc_now()
    sysmeta_pyxb.dateSysMetadataModified = datetime.datetime.now()
    sysmeta_pyxb.rightsHolder = SCIMETA_RIGHTS_HOLDER
    sysmeta_pyxb.submitter = SCIMETA_SUBMITTER
    sysmeta_pyxb.authoritativeMemberNode = SCIMETA_AUTHORITATIVE_MEMBER_NODE
    sysmeta_pyxb.originMemberNode = SCIMETA_AUTHORITATIVE_MEMBER_NODE
    sysmeta_pyxb.accessPolicy = v2.AccessPolicy()

    with d1_common.wrap.access_policy.wrap_sysmeta_pyxb(sysmeta_pyxb) as ap:
        ap.clear()
        ap.add_public_read()

    return sysmeta_pyxb


class AdapterException(Exception):
    pass


if __name__ == '__main__':
    sys.exit(main())
