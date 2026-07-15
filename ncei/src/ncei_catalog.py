#!/usr/bin/env python
# -*- coding: utf-8 -*-

""":Mod: ncei_catalog

:Synopsis:
    Iterates through the NCEI data catalog using the CSW endpoint for the
    purpose building data packages and inserting into the NCEI member node.

:Author:
    servilla
  
:Created:
    2/5/16
"""

import logging

from ncei_csw import iter_csw_records


logger = logging.getLogger('ncei_catalog')


def main():

    record_cnt = 1
    for record in iter_csw_records():
        print('{0:6d}: {1}'.format(record_cnt, record['sid']))
        record_cnt += 1

    return 0


if __name__ == "__main__":
    main()
