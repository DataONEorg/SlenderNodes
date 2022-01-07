# README for figshare slender node

1. Select the D1 env in which to operate and an MN that is registered in the env.

2. Set VERIFY_TLS to False to disable validation of GMN's server side certificate. 
   Use when connecting to a test instance of GMN that is using a self-signed cert.

3. Set a unique User Agent string here. This User Agent should also be blocked from
   creating READ events in GMN. See GMN's `settings.py` for more information.

Records retrieved from OAI-PMH harvest for Figshare can have the following outcomes:

- Create new object in GMN (If SID is new, and thus implicitly, PID as well.)
- Update existing object in GMN (if SID exists but PID is new).
- Result in a log entry that a minor revision was not updated (If both PID and SID already exist, but the date is new).
- Be ignored entirely as already harvested (If both PID and SID exist, but date of record hasn't changed).

Logic for processing records:

![Flow Diagram](https://www.plantuml.com/plantuml/proxy?src=https://raw.githubusercontent.com/DataONEorg/SlenderNodes/master/oaipmh/figshare/README.rst)

Diagram source::

  @startuml
  start
  :parse SID, PID, date, SciMeta
  from record in OAI-PMH harvest;
  if (SID exists in GMN?) then (yes)
    if (PID exists in GMN?) then (yes)
      if (record date for PID is
          newer than date in GMN) then (yes)
          : log ignore minor
            revision event;
      else (no)
          : pass;
      endif
    else (no)
    :MN.update() +
     log update event;
    endif
  else (no)
   : MN.create() +
     log create event;
  endif
  stop
  @enduml

## Operation

The script `oai-pmh_adapter_figshare.py` needs to be run periodically to retrieve updated content 
from the source and populate the GMN instance.

The script is deployed on gmn.dataone.org under `/var/local/dataone/adapter_cary_figshare`. To run the script:

1. Become the `gmn user`
2. Navigate to `/var/local/dataone/adapter_cary_figshare`
3. Run `python oai-pmh_adapter_figshare.py`

Output is logged to `oaipmh.log`, a summary of actions is logged to `oaipmh-summary.csv`

This action should be automated with `cron` or similar.

## Code updates

The script is currently manually updated by downloading from github. This should be altered to 
enable update by pulling a tag from the repo. Implementation requires evaluation of the impacts
on other adapters manged in this repo and their corresponding deployment scenarios.

