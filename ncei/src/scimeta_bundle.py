#!/usr/bin/env python
# -*- coding: utf-8 -*-

""":Mod: scimeta_bundle

:Synopsis:
    To aggregate science metadata and system metadata for insertion into the
    NCEI GMN member node.

:Author:
    servilla
  
:Created:
    3/4/16
"""

import io
import logging

from d1_client import mnclient
from d1_common.types import dataoneTypes as d1_types

import settings


logger = logging.getLogger('scimeta_bundle')


def _to_stream(doc_bytes):
    return io.BytesIO(doc_bytes)



class Scimeta_Bundle(object):

    def __init__(self, pid=None, doc=None, sysmeta_xml=None):

        if not pid or not doc or not sysmeta_xml:
            raise ValueError(
                'Either "pid" or science metadata "doc" or "sysmeta_xml" is None.')

        if isinstance(doc, bytes):
            self.doc = doc
        else:
            self.doc = doc.encode('utf-8')

        if hasattr(sysmeta_xml, 'identifier'):
            self.sysmeta = sysmeta_xml
        else:
            self.sysmeta = d1_types.CreateFromDocument(sysmeta_xml)
        self.pid = pid

        if self.pid != self.sysmeta.identifier.value():
            raise ValueError(
                'PID "{0}" does not match system metadata identifier "{1}".'.format(
                    self.pid, self.sysmeta.identifier.value()))

    def get_sysmeta_binding(self):
        """Returns the pyxb XML binding for an XML system metadata document.

        :return: pyxb XML binding
        """
        return self.sysmeta

    def gmn_create(self):
        """Create a new science metadata object into the NCEI GMN

        :return: None
        """
        try:
            client = mnclient.MemberNodeClient(settings.MN_BASE_URL,
                                               cert_path=settings.CERTIFICATE_FOR_CREATE,
                                               key_path=settings.CERTIFICATE_FOR_CREATE_KEY)
            client.create(self.pid, _to_stream(self.doc), self.sysmeta)
        except UnicodeError as e:
            logger.error(
                'GMN create error for PID "{0}" in science metadata bundle: {1}'.format(
                    self.pid, e))
        except Exception as e:
            logger.error(
                'GMN create error for PID "{0}" in science metadata bundle: {1}'.format(
                    self.pid, e))

    def gmn_update(self, old_pid):
        """Update an existing science metadata object with a new science
           metadata object in the NCEI GMN - requires the previous pid to set
           obsolescence chain.

        :param old_pid: String
        :return: None
        """
        try:
            client = mnclient.MemberNodeClient(settings.MN_BASE_URL,
                                               cert_path=settings.CERTIFICATE_FOR_CREATE,
                                               key_path=settings.CERTIFICATE_FOR_CREATE_KEY)
            client.update(old_pid, _to_stream(self.doc), self.pid, self.sysmeta)
        except Exception as e:
            logger.error(
                'GMN update error for PID "{0}" in science metadata bundle: {1}'.format(
                    self.pid, e))



def main():
    return 0


if __name__ == "__main__":
    main()