import requests
import pandas as pd
import sys
import hashlib
import pdb
from datetime import datetime, timedelta

def generate_md5(data):
    """
    Method to generate a (nearly) unique hash for a given chunk of data.
    """
    data = data.encode('UTF-8')
    hash_md5 = hashlib.md5()
    hash_md5.update(data)
    return hash_md5.hexdigest()

def oipa_recursive_url_getter(url, url_list=[]):
    """
    High level method for extracting activity budgets from OIPA
	Serialize to CSV file with 3 columns: iati-identifier, url, hash
	hash will be empty, initially.
    """

    # Build the request
    r = requests.get(url)

    # extract activity URLs and store in the list
    for activity in r.json()['results']:
        # Exclude automatically if all of the reporters are secondary
        # Unfortunately, it's the only attribute we can exclude before delving deeper
        secondary_flags = [org['secondary_reporter'] for org in activity['reporting_organisations']]
        if sum(secondary_flags) == len(secondary_flags):
            next
        
        extract_activity(activity['url'])
        # TODO: push out to method which appends to a csv file the IATI identifier,
        # URL, and has a column for the hash value which is null unless it's already present.
        # It should overwrite if there is a collision on either the identifier given the URL or the URL
        # given the identifier
        url_list.append(activity['url'])

	# TODO: get the current count from the CSV file
    current_count = len(url_list)
    total = r.json()['count']
    sys.stdout.write('%d percent complete | %d of %d\r' % (current_count / total * 100.000, current_count, total))
    sys.stdout.flush()

    if r.json()['next'] == 'null':
        return(url_list) # TODO: exit the loop and notify that the process has run

    # if there are more pages, then recurse into the next page
    else:
        return(oipa_recursive_url_getter(r.json()['next'], url_list))
    
def extract_activity(url):
    """
    Method for returning attributes given activity URL
    """

    # Build the request
    r = requests.get(url)
    activity = r.json()
    
    valid = True
    
    if len(activity['activity_dates'])>0:
        planned_start = [date['iso_date'] for date in activity['activity_dates'] if date['type']['code']=='1']
        actual_start = [date['iso_date'] for date in activity['activity_dates'] if date['type']['code']=='2']
        planned_end = [date['iso_date'] for date in activity['activity_dates'] if date['type']['code']=='3']
        actual_end = [date['iso_date'] for date in activity['activity_dates'] if date['type']['code']=='4']
        
        #Missing either a start or an end, therefore invalid
        if len(planned_start+actual_start)<1 or len(planned_end+actual_end)<1:
            valid = valid and False
            
        #Parse any available dates
        dates = {}
        if len(planned_start)>0:
            try:
                parsed_planned_start = datetime.strptime(planned_start[0],'%Y-%m-%d')
                dates['planned_start'] = parsed_planned_start
            except ValueError:
                valid = valid and False
        if len(actual_start)>0:
            try:
                parsed_actual_start = datetime.strptime(actual_start[0],'%Y-%m-%d')
                dates['actual_start'] = parsed_actual_start
            except ValueError:
                valid = valid and False
        if len(planned_end)>0:
            try:
                parsed_planned_end = datetime.strptime(planned_end[0],'%Y-%m-%d')
                dates['planned_end'] = parsed_planned_end
            except ValueError:
                valid = valid and False
        if len(actual_end)>0:
            try:
                parsed_actual_end = datetime.strptime(actual_end[0],'%Y-%m-%d')
                dates['actual_end'] = parsed_actual_end
            except ValueError:
                valid = valid and False
        
        #If the timedelta is greater than 365 days, it's invalid
        #Or if start is greater than end
        if 'planned_start' in dates and 'planned_end' in dates:
            if dates['planned_end']-dates['planned_start']>timedelta(365):
                valid = valid and False
            if dates['planned_end']<dates['planned_start']:
                valid = valid and False
        
        if 'actual_start' in dates and 'actual_end' in dates:
            if dates['actual_end']-dates['actual_start']>timedelta(365):
                valid = valid and False
            if dates['actual_end']<dates['actual_start']:
                valid = valid and False
    #Missing any date, therefore invalid
    else:
        valid = valid and False
    
    #Is there a default or budget currency?
    currency = ""
    default_currencies = [org['organisation']['default_currency'] for org in activity['reporting_organisations']]
    if activity['aggregations']['activity']['budget_currency'] is None:
        if len(default_currencies)>0:
            currency = default_currencies[0]
        else:
            valid = valid and False
    else:
        currency = activity['aggregations']['activity']['budget_currency']
        
    value = activity['aggregations']['activity']['budget_value']
    if value is None or value<=0:
        valid = valid and False
    
    pdb.set_trace()

"""
# Current Diagnostic method calls

base_url = 'https://www.oipa.nl/api/activities/?format=json'

activities_urls = oipa_recursive_url_getter(base_url)

print(generate_md5('hello'))
"""
