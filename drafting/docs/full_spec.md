# Full Spec

_Notes taken in YAML_

```yaml
Budgets for DDH
---------------

  aim: get every unique valid budget line into the data warehouse
  validating / filtering budget rows:
    provisos: leave out secondary publishers;
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
