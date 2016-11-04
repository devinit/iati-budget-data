Below is a proposed methodology for including IATI budgets in the Development Data Hub. Before implementation, @rory09 will run a pilot using a previously procured IATI dataset. The output of this pilot would be a dataset which is apt for the analysis team to start running pivot tables and actual _analysis_ on (as opposed to sanitation/cleaning).

###  Proposed Architecture

* A script will retrieve all valid activity budget items from the OIPA Data Store and store these as a mirror in DDW
* DDW will write transforms to produce aggregates by year, publisher, recipient country and sector
* __[A process (tba) will extract organisation and organisation-country budget aggregates from organisation files for loading into DDW]__
	
### Access to Activity Data

* @bill-anderson will share a spreadsheet derrived from the Data Store as something to play with. This is a selection of all governments and multilaterals only. As of yesterday (according to the Datastore) there were 954,525 rows of data.
* @rory09 to write some pseudocode based on the logic in this mail for extracting this data from OIPA that we can get @akmiller01 to turn it into a proper script for @dw8547 to run
* Removing invalid activity budget data (in this order):
  * Exclude all rows with budget/value ≥ 0, or is missing
  * Exclude all rows with (budget/period-end – budget/period-start) > 366 days
  * Exclude all rows with invalid reporting-org-id
  * In each row strip out all sector codes that are not valid CRS codes, and associated percentages and then:
    * Exclude all rows with no valid CRS sector codes
    * Exclude all rows with more than one CRS sector code if a similar number of percentages are not found
    * Exclude all rows where percentages don’t add up to between 98 and 102 (though we should experiment with thresholds)
  * Exclude all rows with invalid country codes
  * Exclude all rows with more than one country if a similar number of percentages are not found
  * Exclude all rows where country percentages don’t add up to between 98 and 102 (smilarly to the above)
  * Exclude all rows with invalid date or number formats
* Count and record the number of excluded rows for each of these tests. (And record iati-identifiers??)
	
### Aggregating Activity Data – Step One

* Create a new ‘normalised’ mirror table where each row is exploded into multiple rows so that in the new table each row contains one country and one sector
* Calculate the value for the new row by splitting the original value by country percentage and then by sector percentage (NB this is NOT an IATI rule, but we need to avoid double counting somehow)

### Aggregating Activity Data – Step Two (Using the ‘normalised’ table)

* Convert period-start to year and use this as Year
* Extract publisher id and name from iati-identifier and match to DDW id
  * __[Not resolved. How to handle publishers that do not have DDW ids]__
* Check that country codes and sector codes are valid in DDW reference tables and flag and exclude discrepancies
* Create an aggregate table where each row has a unique multi-part key comprising year-country-sector-publisher
	
### Organisation-Level Data

*  __[This section of the methodology is yet to be proposed by Bill]__