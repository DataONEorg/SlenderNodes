#!/usr/bin/env python

# Requires PyYAML: pip install pyyaml
# No OAI-PMH support for deleted records, so no record archival functionality

import datetime
import io
import logging
import requests
import xml.etree.ElementTree as ET
import yaml
import os
import sys

import d1_common.types.exceptions

import d1_client.mnclient_2_0
import d1_common.checksum
import d1_common.const
import d1_common.types.dataoneTypes_v2_0 as v2
import d1_common.date_time

# Set a unique User Agent string here. This User Agent should also be blocked from
# creating READ events in GMN. See GMN's `settings.py` for more information.
USER_AGENT = 'DataONE OAI-PMH Adapter/{}'.format(d1_common.const.USER_AGENT)
# Set VERIFY_TLS to False to disable validation of GMN's server side
# certificate. Use when connecting to a test instance of GMN that is using a
# self-signed cert.
VERIFY_TLS = True

SUMMARY_REPORT_FILE = "oaipmh-summary.csv" # track aggregate daily updates info in a csv-formatted log file


def main():
  logging.basicConfig(
    filename='oaipmh.log',
    format='%(asctime)s %(levelname)-8s %(message)s', level=logging.INFO
  )

  with open('mnconfig.yaml') as f:
    mn_config_dict = yaml.load(f, Loader=yaml.SafeLoader)

  try:
    harvest_oai_pmh(mn_config_dict)
  except Exception as e:
    logging.error(
      'Adapter exited due to fatal error. error="{}"'.format(str(e))
    )
    raise
  

def harvest_oai_pmh(mn_config_dict):
  counter_dict = {
    'records': 0,
    'created': 0,
    'updated': 0,
    'already_harvested': 0,
    'minor_revision_not_updated': 0,
    'errors': 0,
  }

  for node_dict in mn_config_dict:
    logging.info('=' * 80)
    logging.info('NodeID: {}'.format(node_dict['node_id']))
    logging.info('OAI-PMH BaseURL: {}'.format(node_dict['oaipmh_base_url']))
    logging.info('GMN BaseURL: {}'.format(node_dict['node_base_url']))

    gmn_client = GMMClient(node_dict)
    node_dict['last_harvest_time'] = gmn_client.get_last_harvest_time()
    harvester = OAIPMHHarvester(node_dict)


    while True:
      try:
        record_list = harvester.get_records()
      except (d1_common.types.exceptions.DataONEException, AdapterError) as e:
        logging.error('get_records() failed. error="{}"'.format(str(e)))
        break

      if not record_list:
        logging.info('Harvesting completed successfully')
        break

      for record_el in record_list:
        counter_dict['records'] += 1
        logging.info('-' * 80)
        logging.info('OAI-PMH record #: ' + str(counter_dict['records']))
        try:
          process_record(record_el, node_dict, counter_dict, gmn_client)
        except (d1_common.types.exceptions.DataONEException, AdapterError) as e:
          logging.error('Record not processed: {}'.format(str(e)))
          counter_dict['errors'] += 1

  logging.info('-' * 80)
  logging.info('Checked OAI-PMH records: {}'.format(counter_dict['records']))
  logging.info(
    'New records: {}'.
    format(counter_dict['created'] + counter_dict['updated'])
  )
  logging.info('Created SciObj: {}'.format(counter_dict['created']))
  logging.info('Updated SciObj: {}'.format(counter_dict['updated']))
  logging.info('Already harvested: {}'.format(counter_dict['already_harvested']))
  logging.info('Minor revisions not updated: {}'.format(counter_dict['minor_revision_not_updated']))
  logging.info('Errors: {}'.format(counter_dict['errors']))

  summary_report(counter_dict, SUMMARY_REPORT_FILE)


def process_record(record_el, node_dict, counter_dict, gmn_client):
  try:
    pid, sid, record_datetime, scimeta_pyxb = parse_record(record_el, node_dict)
  except Exception as e:
    raise AdapterError(
      'Unable to parse record. error="{}" record="{}"'.format(
        str(e), str(record_el)
      )
    )

  logging.info('PID: {}'.format(pid))
  logging.info('SID: {}'.format(sid))

  try:
    gmn_client.create_or_update_if_new(pid, sid, record_datetime, scimeta_pyxb, counter_dict)
  except (d1_common.types.exceptions.DataONEException, AdapterError) as e:
    raise AdapterError(
      'create_or_update() failed. sid="{}" pid="{}" error="{}"'.format(
        sid, pid, str(e)
      )
    )


def parse_record(record_el, node_dict):
  pid = (
    record_el.find('{http://www.openarchives.org/OAI/2.0/}metadata')
    .find('{http://www.openarchives.org/OAI/2.0/oai_dc/}dc')
    .find('{http://purl.org/dc/elements/1.1/}identifier').text
  )
  sid = (
    record_el.find('{http://www.openarchives.org/OAI/2.0/}header')
    .find('{http://www.openarchives.org/OAI/2.0/}identifier').text
  )

  record_date_iso = (
    record_el.find('{http://www.openarchives.org/OAI/2.0/}header')
    .find('{http://www.openarchives.org/OAI/2.0/}datestamp').text
  )
  record_datetime = d1_common.date_time.dt_from_iso8601_str(record_date_iso)
  scimeta_pyxb = ET.tostring(
    record_el.find('{http://www.openarchives.org/OAI/2.0/}metadata')
    .find(node_dict['sci_md_xml_element'])
  )
  return pid,sid, record_datetime, scimeta_pyxb

def summary_report(counter_dict, file_name):
  if os.path.exists(file_name):
    with open(file_name, 'a') as summary_log:
      write_to_summary(summary_log, counter_dict)

  else:
    with open(file_name, 'w') as summary_log:
      summary_log.write("date,records,created,updated,already_harvested, minor_revision_not_updated, errors\n")
      write_to_summary(summary_log, counter_dict)

def write_to_summary(summary_log, counter_dict):
  writestring = str(datetime.datetime.now()) + "," + \
    str(counter_dict['records']) + "," + str(counter_dict['created']) + "," + \
    str(counter_dict['updated']) + "," + str(counter_dict['already_harvested']) + "," + \
    str(counter_dict['minor_revision_not_updated']) + "," +  str(counter_dict['errors']) + "\n"
  summary_log.write(writestring)

# ------------------------------------------------------------------------------


class OAIPMHHarvester:
  def __init__(self, node_dict):
    self.node_dict = node_dict
    self.resume_token = None
    self.is_last_page = False

  def get_records(self):
    if self.is_last_page:
      return

    if self.resume_token:
      params = {
        'verb': 'ListRecords',
        'resumptionToken': self.resume_token,
      }
      self.resume_token = None
    else:
      # It is an option to uncomment this version and comment out harvest based timeslice params
      # params = {'verb': 'ListRecords',
      #          'metadataPrefix': 'iso19139',
      #          'from': '2000-01-01T00:00:00Z',
      #          'until': '2018-01-31T23:59:59Z'}

      params = {
        'verb': 'ListRecords',
        'metadataPrefix': self.node_dict['oaipmh_md_prefix'],
        'set': self.node_dict['oaipmh_set'],
        'from': self.node_dict['last_harvest_time']
      }
    headers = {
      'User-Agent': USER_AGENT,
      'From': self.node_dict['dataone_contact_email'],
    }
    try:
      response = requests.get(
        url=self.node_dict['oaipmh_base_url'], params=params, headers=headers
      )
    except requests.RequestException as e:
      raise AdapterError(str(e))
    root_el = ET.fromstring(response.content)
    record_list = root_el.find(
      '{http://www.openarchives.org/OAI/2.0/}ListRecords'
    )
    if record_list is None:
      raise AdapterError(
        'Unexpected response from GET request. response_body="{}"'.format(
          response.content
        )
      )
    resume_token = record_list.find(
      '{http://www.openarchives.org/OAI/2.0/}resumptionToken'
    )
    if resume_token is not None:
      self.resume_token = resume_token.text
      # Exclude resume_token from list of records to process
      record_list.remove(resume_token)
    else:
      self.is_last_page = True
    return record_list

# ------------------------------------------------------------------------------

class GMMClient:
  def __init__(self, node_dict):
    self.node_dict = node_dict
    self.client = d1_client.mnclient_2_0.MemberNodeClient_2_0(
      node_dict['node_base_url'],
      cert_pem_path=node_dict['cert_path'],
      cert_key_path=node_dict['cert_key_path'],
      timeout=120.0,
      verify_tls=VERIFY_TLS,
    )

  def get_last_harvest_time(self):
    """A function which checks the member node to see the most recently modified/created date of any object in GMN.
    Assumes GMN is returning listobjects response in order of oldest to newest. This datetime can then be used as the
    opening timeslice for harvesting new data.
    :return: Returns either the datesysmetadatamodified property date of the most recent object in GMN, or returns an arbitrary start time to capture everything if no data in GMN yet."""
    try:
      objcount = self.client.listObjects(start=0, count=0).total
      if objcount > 0:
        obj = self.client.listObjects(start=objcount - 1, count=1)
        return obj.objectInfo[0].dateSysMetadataModified.strftime('%Y-%m-%dT%H:%M:%SZ')
      else: # if 0 objects are returned, then this is the first ever harvester run so grab EVERYTHING.
        return '1900-01-01T00:00:00Z'
    except Exception as e:
      logging.error('Fail to get last harvested time. Exiting program prematurely.')
      logging.error(e)
      # print e
      sys.exit(1)

  def create_or_update_if_new(self, pid, sid, record_datetime, scimeta, counter_dict):
    d1_head_sysmeta_pyxb = self.get_pid(sid) # is this sid in use ?
    if d1_head_sysmeta_pyxb is None:  # if not, we can assume the pid does not exist either since they are coupled
      logging.info('Record has unused SID. Adding start of new chain')
      self.create_new_sciobj(scimeta, pid, sid, record_datetime)
      counter_dict['created'] += 1

    else:
      pid_sysmeta_pyxb = self.get_pid(pid) # confirm if pid already exists
      if pid_sysmeta_pyxb is None: # if SID already exists but the PID is new,then the PID is an update to the SID chain
        logging.info('Record has existing SID. Adding new head on existing chain')
        self.update_science_metadata(scimeta, pid, sid, record_datetime,
                                     d1_head_sysmeta_pyxb.identifier.value())
        counter_dict['updated'] += 1
        return
      else: # if both SID and PID already exist
        if pid_sysmeta_pyxb.dateUploaded == record_datetime: # and if the date hasn't changed, then was already harvested
          logging.info('Record already harvested')
          counter_dict['already_harvested'] += 1
          return
        else:  # otherwise if there's a new date, then the reason it showed up in oai-pmh harvest was a minor
          logging.info('Minor revision ignored due to lack of new identifier.')
          counter_dict['minor_revision_not_updated'] += 1  # revision that did not result in a doi/PID change.
          return


  def get_pid(self, did):
    """
    - If {did} is existing SID, return sysmeta of head of chain
    - If {did} is existing PID, return its sysmeta
    - If {did} is unused, return None
    """
    try:
      sysmeta_pyxb = self.client.getSystemMetadata(did)
    except d1_common.types.exceptions.NotFound:
      return None
    else:
      return sysmeta_pyxb

  def create_new_sciobj(self, scimeta_str, pid, sid, record_datetime):
    sysmeta_pyxb = self._generate_sysmeta(
      scimeta_str, pid, sid, record_datetime
    )
    self.client.create(
      sysmeta_pyxb.identifier.value(), io.BytesIO(scimeta_str), sysmeta_pyxb
    )

  def update_science_metadata(
      self, scimeta_str, new_pid, sid, record_datetime, old_pid
  ):
    sysmeta_pyxb = self._generate_sysmeta(
      scimeta_str, new_pid, sid, record_datetime
    )
    self.client.update(
      pid=old_pid, obj=io.BytesIO(scimeta_str),
      newPid=sysmeta_pyxb.identifier.value(), sysmeta_pyxb=sysmeta_pyxb
    )

  def _generate_sysmeta(self, scimeta_str, pid, sid, record_datetime):
    sysmeta_pyxb = v2.systemMetadata()
    sysmeta_pyxb.seriesId = sid
    sysmeta_pyxb.formatId = self.node_dict['sci_md_formatId']
    sysmeta_pyxb.size = len(scimeta_str)
    sysmeta_pyxb.checksum = d1_common.checksum.create_checksum_object_from_bytes(
      scimeta_str
    )
    sysmeta_pyxb.identifier = pid
    # sysmeta_pyxb.dateUploaded = datetime.datetime.strptime(record_datetime, "%Y-%m-%dT%H:%M:%SZ")
    sysmeta_pyxb.dateUploaded = record_datetime
    sysmeta_pyxb.dateSysMetadataModified = datetime.datetime.now()
    sysmeta_pyxb.rightsHolder = self.node_dict['rightsholder']
    sysmeta_pyxb.submitter = self.node_dict['submitter']
    sysmeta_pyxb.authoritativeMemberNode = self.node_dict['authoritativeMN']
    sysmeta_pyxb.originMemberNode = self.node_dict['originMN']
    # Access policies for SlenderNode design pattern default to public read only
    accessPolicy = v2.AccessPolicy()
    accessRule = v2.AccessRule()
    accessRule.subject.append(d1_common.const.SUBJECT_PUBLIC)
    permission = v2.Permission('read')
    accessRule.permission.append(permission)
    accessPolicy.append(accessRule)
    sysmeta_pyxb.accessPolicy = accessPolicy
    return sysmeta_pyxb


class AdapterError(Exception):
  pass


if __name__ == '__main__':
  main()
