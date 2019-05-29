"""
_______________________________________________________________________________

d1_client_manager.py puts all the code managing GMN through API
calls and the DataONE python library into one place. It was written
as part of an OAI-PMH based adapter, but can be incorporated into
any adapter implementation.

Last tested on dataone.libclient version 2.4.0
_______________________________________________________________________________

"""

import datetime
try:
    import StringIO
except ImportError:
    from io import StringIO
import logging
import hashlib
import sys

# D1.
import d1_common.types.dataoneTypes_v2_0 as v2
import d1_common.const
import d1_client.mnclient_2_0
import d1_common.checksum
import d1_common.types.dataoneTypes_v2_0 as dataoneTypes


def _generate_system_metadata(scimeta_bytes, native_identifier_sid,
                              record_date, symeta_settings_dict):
    """
    :param scimeta_bytes: Bytes of the node's original metadata document.
    :param native_identifier_sid: Node's system identifier for this object,
    which becomes the series ID.
    :param record_date: Date metadata document was created/modified in the
    source system. Becomes dateUploaded.
    :param sysmeta_settings_dict: A dict containing node-specific system
    metadata properties that will apply to all science metadata documents
    loaded into GMN.

    This function generates a system metadata document for describing
    the science metadata record being loaded. Some of the fields,
    such as checksum and size, are based off the bytes of the science
    metadata object itself. Other system metadata fields are passed
    to D1ClientManager in a dict which is configured in the main
    adapter program.  Note that the checksum is assigned as an
    arbitrary version identifier to accommodate the source system's
    mutable content represented in the target system's immutable
    content standard.
    """
    sys_meta = v2.systemMetadata()
    sys_meta.seriesId = native_identifier_sid

    sys_meta.formatId = symeta_settings_dict['formatId_custom']
    sys_meta.size = len(scimeta_bytes)

    digest = hashlib.md5(scimeta_bytes).hexdigest()
    sys_meta.checksum = dataoneTypes.checksum(digest)

    sys_meta.checksum.algorithm = 'MD5'
    sys_meta.identifier = sys_meta.checksum.value()
    sys_meta.dateUploaded = record_date
    sys_meta.dateSysMetadataModified = datetime.datetime.now()
    sys_meta.rightsHolder = symeta_settings_dict['rightsholder']
    sys_meta.submitter = symeta_settings_dict['submitter']
    sys_meta.authoritativeMemberNode = symeta_settings_dict['authoritativeMN']
    sys_meta.originMemberNode = symeta_settings_dict['originMN']
    sys_meta.accessPolicy = _generate_public_access_policy()
    return sys_meta


def _generate_public_access_policy():
    """
    This function generates an access policy which is needed as
    part of system metadata for describing a science metadata object.
    In an adapter-based implementation, the ability to modify records
    is managed by the native repository, not GMN, and any changes
    in the native repository simple cascade down to GMN. This means
    it is unnecessary to set specific access policies for individual
    records. Therefore, a generic public read-only access policy
    is generated and assigned as part of system metadata to every
    record as it is loaded.
    """
    accessPolicy = v2.AccessPolicy()
    accessRule = v2.AccessRule()
    accessRule.subject.append(d1_common.const.SUBJECT_PUBLIC)
    permission = v2.Permission('read')
    accessRule.permission.append(permission)
    accessPolicy.append(accessRule)
    return accessPolicy


class D1ClientManager:
    # Initialize the client manager with an instance of a member node client
    def __init__(self, gmn_baseurl, auth_cert, auth_cert_key,
                 sysmeta_settings_dict):
        """
        :param gmn_baseurl: The base URL configured for the Generic Member Node
        installation.
        :param auth_cert: Certificate used for authenticating with
        the GMN server to make changes. If the adapter script is
        being run in standalone mode during development, then this
        might be a certificate generated by the GMN server's local
        CA which was setup during installation of GMN. However, if
        this GMN instance has been registered with a DataONE
        Coordinating Node environment, then the certificate provided
        by DataONE should be used for authenticating with GMN.
        :param auth_cert_key: Also used for authentication. Similarly
        to the certificate described above, either a locally generated
        certificate key or a DataONE provided key will be used,
        depending on whether this node is still in development or
        is registered.
        :param sysmeta_settings_dict: System metadata settings which
        apply to every object loaded into GMN are configured in the
        main script, and then passed within a dict to be used while
        creating and updating objects.
         """

        self.client = d1_client.mnclient_2_0.MemberNodeClient_2_0(
            gmn_baseurl,
            cert_pem_path=auth_cert,
            cert_key_path=auth_cert_key,
            timeout=120.0,
            # uncomment verify_tls=False if using a self-signed SSL certificate
            # or comment if not.
            # verify_tls=False
            )
        self.sysmeta_settings_dict = sysmeta_settings_dict

    def get_last_harvest_time(self):
        """
        A function which checks the member node to see the most
        recently modified/created date of any object in GMN.  Assumes
        GMN is returning listobjects response in order of oldest to
        newest. This datetime can then be used as the opening timeslice
        for harvesting new data.

        :return: Returns either the datesysmetadatamodified property
        date of the most recent object in GMN, or returns an arbitrary
        start time to capture everything if no data in GMN yet.
        """
        try:
            objcount = self.client.listObjects(start=0, count=0).total
            if objcount > 0:
                obj = self.client.listObjects(start=objcount - 1, count=1)
                fmt = '%Y-%m-%dT%H:%M:%SZ'
                return obj.objectInfo[0].dateSysMetadataModified.strftime(fmt)
            else:
                # if 0 objects are returned, then this is the first ever
                # harvester run so grab EVERYTHING.
                return '1900-01-01T00:00:00Z'
        except Exception as e:
            m = 'Fail to get last harvested time. Exiting program prematurely.'
            logging.error(m)
            logging.error(e)
            # print e
            sys.exit(1)

    def check_if_identifier_exists(self, native_identifier_sid):
        """
        The main adapter script uses this function to determine if
        a science metadata record retrieved in an OAI-PMH harvest
        already exists in GMN.

        :param native_identifier_sid: The native repository's system
        identifier for a record harvested in an OAI-PMH query, which
        is implemented as the DataONE seriesId.

        :return: True if found or False if not (or a failed message
        if the check didn't work for some reason).
        """
        checkExistsDict = {}
        try:
            sys_meta = self.client.getSystemMetadata(native_identifier_sid)
        except d1_common.types.exceptions.NotFound:
            checkExistsDict['outcome'] = 'no'
            return checkExistsDict
        except Exception as e:
            msg = (
                'Failed to check if {} exists - '
                'record was not processed correctly'
            )
            msg = msg.format(native_identifier_sid)
            logging.error(msg)
            logging.error(e)
            checkExistsDict['outcome'] = 'failed'
            return checkExistsDict
        else:
            checkExistsDict = dict(
                outcome='yes',
                record_date=sys_meta.dateUploaded,
                current_version_id=sys_meta.identifier.value()
            )
            return checkExistsDict

    def load_science_metadata(self, sci_metadata_bytes, native_identifier_sid,
                              record_date):
        """
        Loads a new science metadata record into GMN using the .create() method
        from the Member Node API.

        :param sci_metadata_bytes: The bytes of the science metadata record as
        a utf-encoded string.
        :param native_identifier_sid: The unique identifier of the metadata
        record in the native repository.
        :param record_date: The datestamp parsed from the OAI-PMH record. This
        becomes the dateUploaded in GMN.
        :return: True if the object successfully created or False if not. This
        allows the main program to track the number of successfully created
        objects.
        """
        try:
            system_metadata = _generate_system_metadata(
                sci_metadata_bytes,
                native_identifier_sid,
                record_date,
                self.sysmeta_settings_dict
            )

        except Exception as e:
            msg = (
                'Failed to generate system metadata. Unable to create SID: '
                '{sid}'
            )
            logging.error(msg.format(sid=native_identifier_sid))
            logging.error(e)
            return False
        try:
            self.client.create(system_metadata.identifier.value(),
                               StringIO.StringIO(sci_metadata_bytes),
                               system_metadata)
        except Exception as e:
            msg = 'Failed to create object with SID: ' + native_identifier_sid
            logging.error(msg)
            logging.error(e)
            return False
        else:
            return True

    def update_science_metadata(self, sci_metadata_bytes,
                                native_identifier_sid, record_date,
                                old_version_pid):
        """
        When a record is harvested from an OAI-PMH query whose
        native repository identifier already exists as a seriesId
        in GMN, then it is understood that the record has been
        modified in the native repository. The .update() API method
        is called to obsolete the old version of the science metadata
        in GMN, and load the changed record as a new object. The
        .update() method automates setting the obsoletes / obsoleted
        by properties of both old and new objects in order to encode
        the relationship between the two, so there is no need to
        explicitly assign them.

        :param sci_metadata_bytes: The bytes of the new version of
        the science metadata record as a utf-encoded string.
        :param native_identifier_sid: The identifier of the record
        in its native repository which is implemented as the seriesId
        property in GMN.
        :param record_date: The datestamp parsed from the OAI-PMH
        record. This becomes the dateUploaded in GMN. If the
        dateUploaded of the most current version of the record in
        GMN is the same as the datestamp of the record from the
        OAI-PMH harvest, then the record hasn't really been modified.
        If the datestamp from the harvest IS different, this means
        something about the record as changed and it should be
        processed as an update in GMN.  The evaluation of whether
        or not a record has changed is done in the main adapter
        program when it calls
         .check_if_identifier_exists() from d1_client_manager.
        :param old_version_pid: The pid for the existing version
        of the pid that about to be updated.
        :return: True if the object successfully updated or False
        if not. This allows the main program to track the number
        of updated objects in a given run.
        """
        try:
            new_version_system_metadata = _generate_system_metadata(
                sci_metadata_bytes,
                native_identifier_sid,
                record_date,
                self.sysmeta_settings_dict
            )
            self.client.update(old_version_pid,
                               StringIO.StringIO(sci_metadata_bytes),
                               new_version_system_metadata.identifier.value(),
                               new_version_system_metadata)
        except Exception as e:
            msg = 'Failed to UPDATE object with SID: {sid} / PID: {pid}'
            msg = msg.format(identifier=native_identifier_sid,
                             pid=old_version_pid)
            logging.error(msg)
            logging.error(e)
            return False
        else:
            return True

    def archive_science_metadata(self, current_version_pid):
        """
        This function is called by the main adapter script to archive
        an existing object in GMN.When GMN is first populated,
        records which already have deleted status in the native
        repository will not be harvested from the repository into
        GMN. By contrast, once a record has already been created
        into GMN, if it later becomes deleted, then the record will
        be archived in GMN.

        :param current_version_pid: The GMN unique identifier (pid)
        of the science metadata record to be archived.
        :return: True if the object successfully archived or False if not. This
        allows the main program to track the number of archived objects in a
        given run.

        """

        try:
            self.client.archive(current_version_pid)
        except Exception as e:
            msg = 'Failed to ARCHIVE object PID: ' + current_version_pid
            logging.error(msg)
            logging.error(e)
            return False
        else:
            return True
