"""
This diagnostic script lists all available records from the OAIPMH service
identified in mnconfig.yaml.
"""

import logging
import yaml

import importlib
pmh_adapter = importlib.import_module("oai-pmh_adapter_figshare")


def main():
    logging.basicConfig(level=logging.INFO)
    with open('mnconfig.yaml') as f:
        mn_config_dict = yaml.load(f, Loader=yaml.SafeLoader)
    for node_dict in mn_config_dict:
        logging.info('NodeID: {}'.format(node_dict['node_id']))
        logging.info('OAI-PMH BaseURL: {}'.format(node_dict['oaipmh_base_url']))
        logging.info('GMN BaseURL: {}'.format(node_dict['node_base_url']))
        harvester = pmh_adapter.OAIPMHHarvester(node_dict)

        counter = 0
        records = []
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
                counter += 1
                logging.debug('OAI-PMH record #: %s', counter)
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
                records.append((sid, pid, record_date_iso,))
                if counter % 10 == 0:
                    logging.info("Retrieved %s records", counter)
        logging.info("Retrieved %s records", len(records))
        records.sort(key=lambda v: v[2])
        n = 0
        for row in records:
            print(f"{n} {row[0]}  {row[1]}  {row[2]}")
            n += 1

if __name__ == "__main__":
    main()