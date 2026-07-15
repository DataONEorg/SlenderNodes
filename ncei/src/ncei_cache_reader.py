#!/usr/bin/env python
# -*- coding: utf-8 -*-

""":Mod: ncei_cache_reader

:Synopsis:

:Author:
    servilla
  
:Created:
    3/13/16
"""

import logging
import hashlib
from datetime import datetime, timezone

from d1_common.types import dataoneTypes as d1_types

from ncei_content_cache import ContentCache
import settings
import scimeta_bundle


logger = logging.getLogger('ncei_cache_reader')


def _parse_datetime(value):
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


def _build_public_access_policy():
    access_policy = d1_types.AccessPolicy()
    access_rule = d1_types.AccessRule()
    access_rule.subject.append('public')
    access_rule.permission.append(d1_types.Permission('read'))
    access_policy.append(access_rule)
    return access_policy


def _generate_sysmeta(scimeta_bytes, pid, sid, uploaded_date):
    sys_meta = d1_types.systemMetadata()
    sys_meta.seriesId = sid
    sys_meta.identifier = pid
    sys_meta.formatId = settings.SCIMETA_FORMAT_ID
    sys_meta.size = len(scimeta_bytes)
    checksum = d1_types.checksum(hashlib.md5(scimeta_bytes).hexdigest())
    checksum.algorithm = 'MD5'
    sys_meta.checksum = checksum
    sys_meta.dateUploaded = uploaded_date
    sys_meta.dateSysMetadataModified = datetime.utcnow()
    sys_meta.rightsHolder = settings.SCIMETA_RIGHTS_HOLDER
    sys_meta.submitter = settings.SCIMETA_SUBMITTER
    sys_meta.authoritativeMemberNode = settings.SCIMETA_AUTHORITATIVE_MEMBER_NODE
    sys_meta.originMemberNode = settings.SCIMETA_ORIGIN_MEMBER_NODE
    sys_meta.accessPolicy = _build_public_access_policy()
    return sys_meta


def main():

    f = open(settings.CACHE_REFRESH_FILE, 'r')
    cache_refresh_date = f.readline().strip()
    f.close()

    cnt = 0
    logger.info('Beginning cache read for new content since: {0}'.format(cache_refresh_date))
    cache = ContentCache(settings.CACHE_PATH, settings.CACHE_DB)
    for record in cache.listNewSince(_parse_datetime(cache_refresh_date)):
        try:
            pid = record['pid']
            sid = record['sid']
            sci_metadata = record['sci_metadata']
            date_modified = record['date_modified']
            uploaded_date = _parse_datetime(date_modified)
            sci_sysmeta = _generate_sysmeta(sci_metadata, pid, sid, uploaded_date)
            smb = scimeta_bundle.Scimeta_Bundle(pid, sci_metadata, sci_sysmeta)
            predecessor = cache.getPredecessorPID(sid, date_modified)
            cache_refresh_date = date_modified
            logger.info('Adding PID-SID "{0}-{1}" with date "{2}"'.format(pid, sid, date_modified))
            if  predecessor is None:
                smb.gmn_create()
                cnt += 1
            else:
                smb.gmn_update(predecessor)
                cnt += 1
        except Exception as e:
            logger.error("Unknown fromIteratorEntry error: {0}".format(str(e)))

    logger.info('Ending cache read for new content up to: {0}'.format(cache_refresh_date))
    f = open(settings.CACHE_REFRESH_FILE, 'w')
    f.write(cache_refresh_date)
    f.close()

    return 0


if __name__ == "__main__":
    main()