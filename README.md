# Extracting IATI Budgets from OIPA

The intended result of this repository is a lightweight script which handles its own dependencies and will sit somewhere innocuous on the Data Warehouse. This script will do the following:

Use the OIPA api to:

##### 1. catalogue the iati-identifier and URL of every activity which has been successfully parsed into OIPA and store in a csv like this:

iati-identifier | url | hash
-|-|-
GB-GOV-1 | https://sampleurl.com | null

> the hash column is only useful if you want to implement the md5 hash of each activity to get a true read of whether it needs to be updated - unfortunately the `last-updated-datetime` value isn't reliable

##### 2. validate then store all of this budget data in a csv file which can then be used by the data warehouse

Below is the full psuedocode methodology for extracting the data we're interested in.

> Instructions below taken in YAML, reproduced from `full_spec.md` in `/drafting/docs/`

```yaml
Budgets for DDH
---------------

  aim: get every unique valid budget line into the data warehouse
  validating / filtering budget rows:
    provisos: leave out secondary publishers;
    elements:
      budget:
        - all fields # including value date etc.
        validation:
          - exclude any rows with invalid iso-dates
          - Exclude all rows with value == 0
          - Exclude all rows with (period-end – period-start) > 366 days
          - Exclude if period-start > period-end
          - if no currency, put defult currency in this column
          - if no currency && no default currency then exclude
      activity:
        - iati-identifier
        - reporting-org
          - code + name
        - title
        - participating-org # name + id IF Implementing, else blank, delimit with semi-colon if multiple (don't sweat this one if time constrained)
        - activity-date # start and end

        # check to see if both country and region are included. If so, check that percentages add up, if they don't, just use country
        - recipient-country
        - recipient-region
        - sector
          - if ¬CRS, include budget but leave the sector blank
          - if CRS # DAC3 or DAC5 - vocabulary must be either of these or null, and the digits must be 3 or 5 in length, otherwise blank it.
            - if single code, then fine
            - if there is a data error - put a flag in the sector code saying declaring it 99880 - 'unable to disaggregate sector'
            data error:
              - no percentages for multiple rows
              - fewer percentages than rows
              - percentages total == <90 || >110
        - policy-marker
        - collaboration-type
        - default-flow-type
        - default-finance-type
        - default-aid-type
        - default-tied-status
        - budget # see above

  presenting the data:
    - one big table
    - pipe seperated
    - `/n` delimited
    - UTF8
    - if there ecaped numbers, double escape
    - check that no pipes are accidentally escaped - if any field ends with a backslash, get rid of the backslash
    - script which sits on her server and downloads a file
```

The resulting table should be stored in a separate one to the index csv outlined above, and should be updated periodically with any activities that need updating. The timeframes for this should be agreed with the Analysis team.
