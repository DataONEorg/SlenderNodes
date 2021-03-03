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
"""Interact with a schema.org resource provider
"""

import logging

# import dirtyjson
import requests
import lxml.etree
import extruct.jsonld
import json
import re
import pprint

NAMESPACES = {"sm": "http://www.sitemaps.org/schemas/sitemap/0.9"}

HTML_OR_JS_COMMENTLINE = re.compile('^\s*(//.*|<!--.*-->)')


class ModifiedJsonLdExtractor(extruct.jsonld.JsonLdExtractor):
  """Add more diagnostic to the extruct json-ld extractor

  https://github.com/scrapinghub/extruct/blob/master/extruct/jsonld.py
  """

  def dump_json_error(self, script, error):
    line_no = 1
    for line in script.split("\n"):
      print("{}: {}".format(line_no, line))
      line_no += 1
    pprint.pprint(error)

  def clean_json_decode_error(self, script, error):
    logging.debug(
      "Bad char ordinal = %s at position %d", ord(script[error.pos]), error.pos
    )
    cleaned = "{}{}".format(script[:error.pos], script[error.pos + 1:])
    return cleaned

  def parse_json(self, script, max_tries=50):
    """Keep trying to parse the provided JSON, replacing bad chars in the text
    with each try.

    This was needed to parse most of the IEDA content which seems to be
    malformed.

    :param script: json text
    :param max_tries: maximum times to try fixing before giving up
    :return: parsed json or nothing
    """
    n_tries = 0
    while n_tries < max_tries:
      try:
        n_tries += 1
        logging.debug("Parse json attempt %d", n_tries)
        data = json.loads(script)
        if n_tries > 1:
          logging.warning("Used %d attempts to fix json data!", n_tries)
        return data
      except json.decoder.JSONDecodeError as e:
        if n_tries >= max_tries:
          self.dump_json_error(script, e)
          raise (e)
        script = self.clean_json_decode_error(script, e)
      except ValueError as e:
        script = HTML_OR_JS_COMMENTLINE.sub('', script)
    return None

  def _extract_items(self, node):
    script = node.xpath('string()')
    logging.info('\n~~~~\n{}\n~~~~'.format(script))
    data = self.parse_json(script)
    # data = dirtyjson.loads(script)
    if isinstance(data, list):
      return data
    elif isinstance(data, dict):
      return [data]


def load_resources_from_sitemap(sitemap):
  """
  :param sitemap: URL to sitemap XML document to process
  :return: list of {url:"", date_modified:""}
  """
  resources = []
  sitemap_xml = lxml.etree.parse(sitemap)
  urls = sitemap_xml.xpath("//sm:urlset/sm:url", namespaces=NAMESPACES)
  logging.debug("Found %d entries in sitemap %s", len(urls), sitemap)
  for url in urls:
    resource = {
      "url": url.xpath("sm:loc", namespaces=NAMESPACES)[0].text,
      "date_modified": url.xpath("sm:lastmod", namespaces=NAMESPACES)[0].text,
    }
    resources.append(resource)
  return resources


def load_schema_org(resource):
  """Load schema.org information from a specified resource URL
  :param resource: URL
  :return: dictionary of values
  """
  response = requests.get(resource["url"])
  data = []
  #extractor = ModifiedJsonLdExtractor()
  extractor = extruct.JsonLdExtractor()
  try:
    content_without_header = ''.join(response.text.splitlines()[1:])
    #data = extractor.extract(response.content)
    data = extractor.extract(content_without_header)
  except json.decoder.JSONDecodeError as e:
    logging.error(e)
    return {"error": str(e)}
  if len(data) < 1:
    return {"error": "No json-ld in resource."}
  if len(data) > 1:
    logging.warning("More than one json-ld block found. Using #0.")
  if data[0]["@type"] == "Dataset":
    entry = {
      "id": data[0]["@id"].strip(),
      "metadata_url": None,
      "metadata_format": None,
    }
    for ddownload in data[0]["distribution"]:
      if ddownload["@type"] == "DataDownload":
        if ddownload["name"] == "ISO Metadata Document":
          entry["metadata_url"] = ddownload["url"].strip()
    return entry
  return {"error": "Not a Dataset resource."}
