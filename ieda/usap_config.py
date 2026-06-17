# IEDA adapter production config

# IEDA sitemap index URL. The 'sitemap' paths below are appended to this URL.
SITEMAP_ROOT = 'https://www.usap-dc.org/view/dataset/'
GMN_BASE_URL = 'https://gmn.dataone.org/ieda'

# Absolute path to the root of the certificate storage. The certificate paths below are
# relative to this directory.
CERT_PATH_ROOT = ''

# List of sites from which metadata is extracted by the adapter.
SITEMAP_LIST = [
  {
    'sitemap': 'sitemap.xml',
    'gmn_path': 'usap',
    'cert_pem_path': 'client_cert.pem',
    'cert_key_path': 'client_key_nopassword.pem',
  },
]

# The following set the rightsholder, submitter and authoritative member node in the
# DataONE System Metadata for the generated metadata objects.
SCIMETA_RIGHTS_HOLDER = 'CN=urn:node:IEDA,DC=dataone,DC=org'
SCIMETA_SUBMITTER = 'CN=urn:node:IEDA,DC=dataone,DC=org'
SCIMETA_AUTHORITATIVE_MEMBER_NODE = 'urn:node:IEDA'
