# IEDA SlenderNode Adapter

## Overview

* The IEDA Adapter exposes metadata from compatible websites to the DataONE federation. In order to expose metadata to DataONE via this adapter, a website must provide a [sitemap](https://www.sitemaps.org) with links to landing pages for the datasets in which metadata is embedded as SDO [JSON-LD](https://json-ld.org) encoded [Schema.org](https://schema.org) compatible markup. In addition, the adapter requires a DataONE Member Node in which it has access to create objects.

* The adapter does not track identifiers that are removed, so removing the web page from which the DataONE metadata object was generated does not cause the DataONE object to be archived (deleted). Objects can be archived by calling the v1 or v2 `MNStorage.archive` or `CNStorage.archive` APIs.
 
* The adapter configuration is stored in `config.py`, which is located in the adapter's root dir. The file holds a list of sites for which the adapter will be exposing metadata to DataONE. The list may contain an arbitrary number of sites. The settings required for each site includes the site's FQDN, the corresponding DataONE Member Node BaseURL, and credentials which provide permissions for creating objects on the Member Node.

## Deployment

* Both the IEDA adapter and the corresponding GMN Member Nodes are currently hosted on `gmn.dataone.org`. The IEDA repositories are located at [get.iedadata.org](http://get.iedadata.org) and map to GMN MNs as follows:

  | iedadata.org (link to sitemap)                                |    | DataONE.org (link to MN Node)
  ----------------------------------------------------------------|----|-------------------------------------------------------------------  
  | [EarthChem](http://get.iedadata.org/sitemaps/ecl_sitemap.xml) | ➞ | [IEDA EarthChem Member Node](https://gmn.dataone.org/ieda/earthchem/v1/node)
  | [MGDL](http://get.iedadata.org/sitemaps/mgdl_sitemap.xml)     | ➞ | [IEDA MGDL Member Node](https://gmn.dataone.org/ieda/mgdl/v1/node)
  | [USAP](http://get.iedadata.org/sitemaps/usap_sitemap.xml)     | ➞ | [IEDA USAP Member Node](https://gmn.dataone.org/ieda/usap/v1/node)
  
  IEDA also provides a sitemap index which is currently not used by the adapter, located at [get.iedadata.org/sitemaps](http://get.iedadata.org/sitemaps/).

* The root dir for all files related to GMN and the adapters, is `/var/local/dataone`. It, and all files below, should be owned by the GMN user (`gmn`) and readable by the (`www-data`) group. The IEDA adapter is located at `adapter_ieda`, with the executable, `ieda_adapter.py` and configuration `config.py` in the adapter root. 
 
* It's usually best to become the `gmn` user before working in the `/var/local/dataone` tree. When opening a shell as the `gmn` user, some useful paths and aliases are printed to the terminal. These include `cdd1`, which changes working dir to the DataONE root, and `cdgmn`, which changes it to the GMN root. GMN's root dir is also in `PATH`, so the management commands can be run from anywhere.

* Apache and the adapters run as the `gmn` and `www-data` users, so for security, those should not be joined to any groups (except their own). Joining one's own user to their groups can be convenient and should be safe.

* To ease server maintenance, GMN on `gmn.dataone.org` has been set up in such a way that all hosted MNs share the same GMN installation, while being otherwise mostly independent. They share a single Apache VirtualHost configuration, located in `/etc/apache2/sites-available`, and they share the same server side certificate. They have separate GMN configurations, management commands, databases, and WSGI daemon processes. This type of configuration for GMN is documented in [Hosting multiple Member Nodes from the same GMN instance](https://dataone-python.readthedocs.io/en/latest/d1_gmn/setup/multi-hosting.html#). There are a few more MNs hosted by the same GMN installation. These are unrelated to IEDA.
  
* The GMN root (reached with `cdgmn` after becoming the `gmn` user) contains configuration files and management commands for each of the MNs. The management commands will only affect the MN indicated in the filenames. This includes "low level" commands, such as clearing the database and running database migrations. Running a management command without arguments will list all available subcommands. The 30 or so commands listed under `[app]` are custom commands implemented for GMN. They break down as follows:

    - `audit` - Checks for content, CN sync and sync of objects hosted with GMN's proxy mode
    - `diag` - Commands mainly useful during testing, deployment and troubleshooting
    - `node` - Node registration and Node document manipulation  
    - `process` - Async processing that runs as cron jobs
    - `view` - View logs and other content
    - `whitelist` - Manage permissions

* There is a separate Postgres database for each of the MNs. The databases can be accessed by running `psql` as the `gmn` or Postgres user (`sudo -u postgres psql`). `psql` can also be run via the `dbshell` management command. E.g., `manage_ieda_mgdl.py dbshell`, which has the advantage of automatically using the correct database for the given MN.

* GMN's async `MNStorage.systemMetadataChanged()` and `MNReplication.replicate()` processing is not applicable for any of the hosted nodes, so cron jobs are needed only for the adapters. The IEDA adapter should be started once per day, at which time it will iterate over the sitemap for each of the configured IEDA sites and create MN objects for any new objects.
  
  The crontab entry for the IEDA adapter launches the adapter via the wrapper, `run.sh`, and is owned by the `gmn` user. It was created with:

  ```shell
  # (crontab -u gmn -l && printf "0 4 * * * /var/local/dataone/adapter_ieda/run.sh\n") | crontab -u gmn -
  ```

  The wrapper activates the Python virtual environment that holds the dependencies for the adapter, and redirects the output to a log. The log is in the DataONE root, with filename `ieda_adapter.log` and is rotated by `logrotate`. There is a small configuration file and installer included with the adapter (`logrotate.conf` and `install_logrotate.sh`).

* GMN, `d1_python` and the adapters are all implemented in Python, and require a working Python environment to run. They run in Python environments that are owned by the `gmn` user and managed via `pyenv`. `pyenv` is modelled after similar utilities for Perl, Ruby, Java, Node, and others. It makes it trivial to builds and install specific versions of Python and create virtualenvs based on them. This allows us to have full control of dependencies and not having to touch the system version of Python. Installing dependencies into the system Python can break OS functionality, and OS updates can break user projects (by changing the dependencies). 
  
  `pyenv` also monitors changes of the working directory from the command line and activates Python environments that have been tied to different branches of the directory hierarchy. E.g., entering the IEDA adapter root with, `cdd1; cd adapter_ieda` will automatically activate the environment which holds the dependencies for the adapter. This enables the adapter to be started manually without specifying the Python version or environment to use, with just `./ieda_adapter.py`.  

  Starting `pyenv` without arguments yields a list of available subcommands.

* GMN is typically set up to run in a virtualenv called `d1_python`, and since adapters often depend only on d1_python, they are often set up to share the same environment. On `gmn.dataone.org`, the adapters are set up in a separate environment however, due to dependencies being managed by `Anaconda (conda)`, while `d1_python` uses `pip`.

* Documentation:
    - `d1_python` - https://dataone-python.readthedocs.io/en/latest/index.html
    - `GMN` - https://dataone-python.readthedocs.io/en/latest/d1_gmn/index.html
