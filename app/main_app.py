import requests
import pandas as pd
import sys
import hashlib
import pdb
from datetime import datetime, timedelta

def valid_budget(date_str,value,period_start_str,period_end_str,currency,default_currency):
    #Try to parse the date string. If failure, invalid budget.
    try:
        date = datetime.strptime(date_str,'%Y-%m-%d')
    except ValueError:
        return False
    
    #If value is None, or zero or less, invalid budget
    if value is None or value<=0:
        return False
    
    #Try to parse the period start date string. If failure, invalid budget.
    try:
        period_start = datetime.strptime(period_start_str,'%Y-%m-%d')
    except ValueError:
        return False
    
    #Try to parse the period end date string. If failure, invalid budget.
    try:
        period_end = datetime.strptime(period_end_str,'%Y-%m-%d')
    except ValueError:
        return False
    
    #If currency is None or blank, and default_currency is None or blank, then invalid budget
    if currency is None or currency=="":
        if default_currency is None or default_currency=="":
            return False
    
    return True

def generate_md5(data):
    """
    Method to generate a (nearly) unique hash for a given chunk of data.
    """
    data = data.encode('UTF-8')
    hash_md5 = hashlib.md5()
    hash_md5.update(data)
    return hash_md5.hexdigest()

def oipa_recursive_url_getter(url, filename, current_count=0, valid_count=0):
    """
    High level method for extracting activity budgets from OIPA
	Serialize to CSV file with 3 columns: iati-identifier, url, hash
	hash will be empty, initially.
    """
    
    # Build the request
    r = requests.get(url)

    # extract activity URLs and store in the list
    for activity in r.json()['results']:
        current_count = current_count + 1
        # Exclude automatically if all of the reporters are secondary
        # Unfortunately, it's the only attribute we can exclude before delving deeper
        secondary_flags = [org['secondary_reporter'] for org in activity['reporting_organisations']]
        if sum(secondary_flags) == len(secondary_flags):
            next
        
        extraction = extract_activity(activity['url'])
        if extraction:
            valid_count = valid_count + 1
            extraction['url'] = activity['url']
            extraction_hash = generate_md5(str(extraction))
            extraction['hash'] = extraction_hash
            df = pd.DataFrame([extraction])
            now = datetime.now()
            if valid_count==1:
                df.to_csv(filename,index=False,sep="|")
            else:
                df.to_csv(filename,mode="a",header=False,index=False,sep="|")

    total = r.json()['count']
    sys.stdout.write('%d percent complete | %d of %d\r' % (current_count / total * 100.000, current_count, total))
    sys.stdout.flush()

    if r.json()['next'] == 'null':
        return(True) # TODO: exit the loop and notify that the process has run

    # if there are more pages, then recurse into the next page
    else:
        return(oipa_recursive_url_getter(r.json()['next'], filename, current_count, valid_count))
    
def extract_activity(url):
    """
    Method for returning attributes given activity URL
    """

    # Build the request
    r = requests.get(url)
    activity = r.json()

    if len(activity['activity_dates'])>0:
        planned_start = [date['iso_date'] for date in activity['activity_dates'] if date['type']['code']=='1']
        actual_start = [date['iso_date'] for date in activity['activity_dates'] if date['type']['code']=='2']
        planned_end = [date['iso_date'] for date in activity['activity_dates'] if date['type']['code']=='3']
        actual_end = [date['iso_date'] for date in activity['activity_dates'] if date['type']['code']=='4']
            
        #Parse any available dates
        dates = {}
        if len(planned_start)>0:
            try:
                parsed_planned_start = datetime.strptime(planned_start[0],'%Y-%m-%d')
                dates['activity_planned_start'] = parsed_planned_start
            except ValueError:
                pass
        if len(actual_start)>0:
            try:
                parsed_actual_start = datetime.strptime(actual_start[0],'%Y-%m-%d')
                dates['activity_actual_start'] = parsed_actual_start
            except ValueError:
                pass
        if len(planned_end)>0:
            try:
                parsed_planned_end = datetime.strptime(planned_end[0],'%Y-%m-%d')
                dates['activity_planned_end'] = parsed_planned_end
            except ValueError:
                pass
        if len(actual_end)>0:
            try:
                parsed_actual_end = datetime.strptime(actual_end[0],'%Y-%m-%d')
                dates['activity_actual_end'] = parsed_actual_end
            except ValueError:
                pass
        
        #If the timedelta is greater than 365 days, it's invalid
        #Or if start is greater than end
        # if 'planned_start' in dates and 'planned_end' in dates:
        #     if dates['planned_end']-dates['planned_start']>timedelta(365):
        #         valid = valid and False
        #     if dates['planned_end']<dates['planned_start']:
        #         valid = valid and False
        # 
        # if 'actual_start' in dates and 'actual_end' in dates:
        #     if dates['actual_end']-dates['actual_start']>timedelta(365):
        #         valid = valid and False
        #     if dates['actual_end']<dates['actual_start']:
        #         valid = valid and False
        #         
        # if 'actual_start' in dates and 'actual_end' not in dates and 'planned_end' in dates:
        #     if dates['planned_end']-dates['actual_start']>timedelta(365):
        #         valid = valid and False
        #     if dates['planned_end']<dates['actual_start']:
        #         valid = valid and False
    
    #Is there a default or budget currency?
    currency = ""
    default_currencies = [org['organisation']['default_currency'] for org in activity['reporting_organisations']]
    if activity['aggregations']['activity']['budget_currency'] is None:
        if len(default_currencies)>0:
            currency = default_currencies[0]
    else:
        currency = activity['aggregations']['activity']['budget_currency']
        
    value = activity['aggregations']['activity']['budget_value']
    
    if value is None or value<=0:
        #Activity level results
        result = {}
        all_date_keys = ['activity_planned_start','activity_actual_start','activity_planned_end','activity_actual_end']
        for key in all_date_keys:
            if key not in dates:
                result[key] = ""
            else:
                result[key] = dates[key].strftime('%Y-%m-%d')
        result['currency'] = currency
        result['total_value'] = value
        try:
            result['iati_identifier'] = str(activity['iati_identifier'])
        except (KeyError,IndexError,TypeError):
            result['iati_identifier'] = ""
            
        try:
            reporting_codes = ";".join([str(org['organisation']['organisation_identifier']) for org in activity['reporting_organisations']])
        except (KeyError,IndexError,TypeError):
            reporting_codes = ""
        result['reporting_org_codes'] = reporting_codes
        
        try:
            reporting_names = ";".join([str(org['organisation']['primary_name']) for org in activity['reporting_organisations']])
        except (KeyError,IndexError,TypeError):
            reporting_names = ""
        result['reporting_org_names'] = reporting_names
        
        try:
            #Try and grab the English title
            titles = [str(narrative['text']) for narrative in activity['title']['narratives'] if narrative['language']['code']=='en']
            #If it doesn't exist
            if len(titles)<=0:
                #Just take the first one
                title = str(activity['title']['narratives'][0]['text'])
            else:
                title = titles[0]
            result['title'] = title
        except (KeyError,IndexError,TypeError):
            result['title'] = ""
            
        try:
            participating_names = ";".join([str(org['narratives'][0]['text']) for org in activity['participating_organisations'] if org['role']['name']=="Implementing"])
        except (KeyError,IndexError,TypeError):
            participating_names = ""
        result['participating_org_names'] = participating_names
            
        try:
            participating_codes = ";".join([str(org['ref']) for org in activity['participating_organisations'] if org['role']['name']=="Implementing"])
        except (KeyError,IndexError,TypeError):
            participating_codes = ""
        result['participating_org_codes'] = participating_codes
        
        try:
            recipient_countries = ";".join([str(country['country']['name']) for country in activity['recipient_countries']])
        except (KeyError,IndexError,TypeError):
            recipient_countries = ""
        result['recipient_countries'] = recipient_countries
        try:
            recipient_country_percentages = ";".join([str(country['percentage']) for country in activity['recipient_countries']])
        except (KeyError,IndexError,TypeError):
            recipient_country_percentages = ""
        result['recipient_country_percentages'] = recipient_country_percentages
            
        #Flying a little blind here because I'm having trouble finding an example with a region
        try:
            # if len(activity['recipient_regions'])>0:
            #     pdb.set_trace()
            recipient_regions = ";".join([str(region['region']['name']) for region in activity['recipient_regions']])
        except (KeyError,IndexError,TypeError):
            recipient_regions = ""
        result['recipient_regions'] = recipient_regions
        try:
            recipient_region_percentages = ";".join([str(region['percentage']) for region in activity['recipient_regions']])
        except (KeyError,IndexError,TypeError):
            recipient_region_percentages = ""
        result['recipient_region_percentages'] = recipient_region_percentages
        
        #At the moment, no way to compare percentages unless we introduce a region-lookup by country code
        
        try:
            sector_sum = sum([float(sector['percentage']) for sector in activity['sectors'] if sector['vocabulary']['code'] in ['1','2']])
            if sector_sum<90 or sector_sum>110:
                data_error_flag="99880"
                data_error_flag_percentage="None"
            else:
                data_error_flag=False
        except (KeyError,IndexError,TypeError):
            data_error_flag="99880"
            data_error_flag_percentage="None"
        
        try:
            sector_codes = ";".join([str(sector['sector']['code']) for sector in activity['sectors'] if sector['vocabulary']['code'] in ['1','2']])
        except (KeyError,IndexError,TypeError):
            sector_codes = ""
        if data_error_flag:
            result['sector_codes'] = ";".join([sector_codes,data_error_flag])
        else:
            result['sector_codes'] = sector_codes
        try:
            sector_percentages = ";".join([str(sector['percentage']) for sector in activity['sectors'] if sector['vocabulary']['code'] in ['1','2']])
        except (KeyError,IndexError,TypeError):
            sector_percentages = ""
        if data_error_flag:
            result['sector_percentages'] = ";".join([sector_percentages,data_error_flag_percentage])
        else:
            result['sector_percentages'] = sector_percentages
            
        #Again, no test case for this, so it needs testing
        try:
            # if len(activity['policy_markers'])>0:
            #     pdb.set_trace()
            policy_marker_vocabularies = ";".join([str(marker['vocabulary']) for marker in activity['policy_markers']])
        except (KeyError,IndexError,TypeError):
            policy_marker_vocabularies = ""
        result['policy_marker_vocabularies'] = policy_marker_vocabularies
        try:
            policy_marker_codes = ";".join([str(marker['code']) for marker in activity['policy_markers']])
        except (KeyError,IndexError,TypeError):
            policy_marker_codes = ""
        result['policy_marker_codes'] = policy_marker_codes
        try:
            policy_marker_sig = ";".join([str(marker['significance']) for marker in activity['policy_markers']])
        except (KeyError,IndexError,TypeError):
            policy_marker_sig = ""
        result['policy_marker_sig'] = policy_marker_sig
        
        try:
            result['collaboration_type'] = str(activity['collaboration_type']['code'])
        except (KeyError,IndexError,TypeError):
            result['collaboration_type'] = ""
            
        try:
            result['default_flow_type'] = str(activity['default_flow_type']['code'])
        except (KeyError,IndexError,TypeError):
            result['default_flow_type'] = ""
            
        try:
            result['default_finance_type'] = str(activity['default_finance_type']['code'])
        except (KeyError,IndexError,TypeError):
            result['default_finance_type'] = ""
            
        try:
            result['default_aid_type'] = str(activity['default_aid_type']['code'])
        except (KeyError,IndexError,TypeError):
            result['default_aid_type'] = ""
            
        try:
            result['default_tied_status'] = str(activity['default_tied_status']['code'])
        except (KeyError,IndexError,TypeError):
            result['default_tied_status'] = ""
            
        #Budget level results
        try:
            budget_values = [item['value']['value'] for item in activity['budgets']]
        except (KeyError,IndexError,TypeError):
            budget_values = []
        try:
            budget_dates = [item['value']['date'] for item in activity['budgets']]
        except (KeyError,IndexError,TypeError):
            budget_dates = []
        try:
            budget_currencies = [item['value']['currency']['code'] for item in activity['budgets']]
        except (KeyError,IndexError,TypeError):
            budget_currencies = []
        try:
            budget_period_ends = [item['period_end'] for item in activity['budgets']]
        except (KeyError,IndexError,TypeError):
            budget_period_ends = []
        try:
            budget_period_starts = [item['period_start'] for item in activity['budgets']]
        except (KeyError,IndexError,TypeError):
            budget_period_starts = []
        try:
            budget_types = [item['type']['code'] for item in activity['budgets']]
        except (KeyError,IndexError,TypeError):
            budget_types = []
         
        data_lengths = [len(budget_values),len(budget_dates),len(budget_currencies),len(budget_period_ends),len(budget_period_starts),len(budget_types)]    
        results = []
        for i in range(0,max(data_lengths)):
            budget_item = result.deepcopy()

        return results
    else:
        return False

"""
# Current Diagnostic method calls

base_url = 'https://www.oipa.nl/api/activities/?format=json'

activities_urls = oipa_recursive_url_getter(base_url)

print(generate_md5('hello'))
"""
