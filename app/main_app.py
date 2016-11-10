import requests
import pandas as pd
import sys
import hashlib
import pdb
from datetime import datetime, timedelta
from copy import deepcopy

def valid_budget(date_str,value,period_start_str,period_end_str,currency,default_currency):
    #Try to parse the date string. If failure, invalid budget.
    try:
        date = datetime.strptime(date_str,'%Y-%m-%d')
    except ValueError:
        return False
    
    #If value is None, or zero, or blank, invalid budget
    if value is None or value==0 or value=="":
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
    
    #If the budget line is longer than 1 year, invalid
    if period_end-period_start>timedelta(365):
        return False

    #If the end is before the beginning, invalid.
    if period_end<period_start:
        return False
    
    #If currency is None or blank, and default_currency is None or blank, then invalid budget
    if currency is None or currency=="":
        if default_currency is None or default_currency=="":
            return False
    
    return True

def oipa_url_getter(url, filename):
    """
    High level method for extracting activity budgets from OIPA
	Serialize to CSV file with 3 columns: iati-identifier, url, hash
	hash will be empty, initially.
    """
    
    # Build the request
    r = requests.get(url)
    current_count=0
    valid_count=0
    
    invalid_urls = ['null','None',None]
    while r.json()['next'] not in invalid_urls:

        # extract activity URLs and store in the list
        for activity in r.json()['results']:
            current_count = current_count + 1
            # Exclude automatically if all of the reporters are secondary
            # Unfortunately, it's the only attribute we can exclude before delving deeper
            secondary_flags = [org['secondary_reporter'] for org in activity['reporting_organisations']]
            if sum(secondary_flags) == len(secondary_flags):
                next
                
            #Exclude invalid IATI identifiers
            try:
                org_code = [org['organisation']['organisation_identifier'] for org in activity['reporting_organisations']][0]
            except (KeyError,IndexError,TypeError):
                org_code = ""
            try:
                identifier = activity['iati_identifier']
            except (KeyError,IndexError,TypeError):
                identifier = ""
    
            if identifier[:len(org_code)]!=org_code:
                next
                
            extraction = extract_activity(activity)
            
            if extraction:
                valid_count = valid_count + 1
                for budget_item in extraction:
                    budget_item['oipa-activity-url'] = activity['url']
                df = pd.DataFrame(extraction)
                now = datetime.now()
                if valid_count==1:
                    df.to_csv(filename,index=False,sep="|")
                else:
                    df.to_csv(filename,mode="a",header=False,index=False,sep="|")
    
        total = r.json()['count']
        sys.stdout.write('%d percent complete | %d of %d\r' % (current_count / total * 100.000, current_count, total))
        sys.stdout.flush()
        
        r = requests.get(r.json()['next'])

    return(True) # TODO: exit the loop and notify that the process has run

    
def extract_activity(activity):
    """
    Method for returning attributes given activity URL
    """

    dates = {}
    if len(activity['activity_dates'])>0:
        planned_start = [date['iso_date'] for date in activity['activity_dates'] if date['type']['code']=='1']
        actual_start = [date['iso_date'] for date in activity['activity_dates'] if date['type']['code']=='2']
        planned_end = [date['iso_date'] for date in activity['activity_dates'] if date['type']['code']=='3']
        actual_end = [date['iso_date'] for date in activity['activity_dates'] if date['type']['code']=='4']
            
        #Parse any available dates, ensuring real ISO
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
            
    #Is there a default currency?
    try:
        default_currency = [org['organisation']['default_currency'] for org in activity['reporting_organisations']][0]
    except (KeyError,IndexError,TypeError):
        default_currency = ""

    try:
        value = activity['aggregations']['activity']['budget_value']
    except (KeyError,IndexError,TypeError):
        value = None
    
    if value is not None:
        #Activity level results
        result = {}
        
        result['iati-activity_default-currency'] = default_currency
        
        if 'activity_actual_start' in dates:
            result['activity-date_start'] = dates['activity_actual_start'].strftime('%Y-%m-%d')
        elif 'activity_planned_start' in dates:
            result['activity-date_start'] = dates['activity_planned_start'].strftime('%Y-%m-%d')
        else:
            result['activity-date_start'] = ""
            
        if 'activity_actual_end' in dates:
            result['activity-date_end'] = dates['activity_actual_end'].strftime('%Y-%m-%d')
        elif 'activity_planned_end' in dates:
            result['activity-date_end'] = dates['activity_planned_end'].strftime('%Y-%m-%d')
        else:
            result['activity-date_end'] = ""

        try:
            result['iati-identifier'] = str(activity['iati_identifier'])
        except (KeyError,IndexError,TypeError):
            result['iati-identifier'] = ""
            
        try:
            reporting_codes = ";".join([str(org['organisation']['organisation_identifier']) for org in activity['reporting_organisations']])
        except (KeyError,IndexError,TypeError):
            reporting_codes = ""
        result['reporting-org_ref'] = reporting_codes
        
        try:
            reporting_names = ";".join([str(org['organisation']['primary_name']) for org in activity['reporting_organisations']])
        except (KeyError,IndexError,TypeError):
            reporting_names = ""
        result['reporting-org_name'] = reporting_names
        
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
        result['implementing-org_name'] = participating_names
            
        try:
            participating_codes = ";".join([str(org['ref']) for org in activity['participating_organisations'] if org['role']['name']=="Implementing"])
        except (KeyError,IndexError,TypeError):
            participating_codes = ""
        result['implementing-org_ref'] = participating_codes
        
        try:
            recipient_country_names = [country['country']['name'] for country in activity['recipient_countries']]
        except (KeyError,IndexError,TypeError):
            recipient_country_names = []
        try:
            recipient_country_codes = [country['country']['code'] for country in activity['recipient_countries']]
        except (KeyError,IndexError,TypeError):
            recipient_country_codes = []
        try:
            recipient_country_percentages = [country['percentage'] for country in activity['recipient_countries']]
        except (KeyError,IndexError,TypeError):
            recipient_country_percentages = []
        
        try:
            recipient_region_names = [region['region']['name'] for region in activity['recipient_regions']]
        except (KeyError,IndexError,TypeError):
            recipient_region_names = []
        try:
            recipient_region_codes = [region['region']['code'] for region in activity['recipient_regions']]
        except (KeyError,IndexError,TypeError):
            recipient_region_codes = []
        try:
            recipient_region_percentages = [region['percentage'] for region in activity['recipient_regions']]
        except (KeyError,IndexError,TypeError):
            recipient_region_percentages = []
            
        if len(recipient_country_names+recipient_region_names)==1:
            recipient_names_concat = recipient_country_names+recipient_region_names
            recipient_names = recipient_names_concat[0]
            recipient_codes_concat = recipient_country_codes+recipient_region_codes
            recipient_codes = recipient_codes_concat[0]
            recipient_percentages="100"
        elif len(recipient_country_names+recipient_region_names)==0:
            recipient_names = ""
            recipient_codes = ""
            recipient_percentages = ""
        elif len(recipient_country_names+recipient_region_names)>1:
            recipient_percentages_concat = [percentage for percentage in recipient_country_percentages+recipient_region_percentages if percentage is not None]
            if sum(recipient_percentages_concat)>110 or sum(recipient_percentages_concat)<90:
                #Just go with the countries
                recipient_names = ";".join(recipient_country_names)
                recipient_codes = ";".join(recipient_country_codes)
                recipient_percentages = ";".join([str(perc) for perc in recipient_country_percentages])
            else:
                recipient_percentages = ";".join(recipient_percentages_concat)
                recipient_names_concat = recipient_country_names+recipient_region_names
                recipient_names = ";".join(recipient_names_concat)
                recipient_codes_concat = recipient_country_codes+recipient_region_codes
                recipient_codes = ";".join(recipient_codes_concat)
            
        result['recipient_name'] = recipient_names
        result['recipient_code'] = recipient_codes
        result['recipient_percentage'] = recipient_percentages
        
        
        #If vocabulary is null, DAC is assumed
        try:
            sector_sum = sum([float(sector['percentage']) for sector in activity['sectors'] if sector['vocabulary']['code'] in ['1','2',"",None]])
            if sector_sum<90 or sector_sum>110:
                data_error_flag="99880"
                data_error_flag_percentage="100"
            else:
                data_error_flag=False
        except (KeyError,IndexError,TypeError):
            data_error_flag="99880"
            data_error_flag_percentage="100"
        
        try:
            sector_codes = ";".join([str(sector['sector']['code']) for sector in activity['sectors'] if sector['vocabulary']['code'] in ['1','2']])
        except (KeyError,IndexError,TypeError):
            sector_codes = ""
        if data_error_flag:
            result['sector_code'] = data_error_flag
        else:
            result['sector_code'] = sector_codes
        try:
            sector_percentages = ";".join([str(sector['percentage']) for sector in activity['sectors'] if sector['vocabulary']['code'] in ['1','2']])
        except (KeyError,IndexError,TypeError):
            sector_percentages = ""
        if data_error_flag:
            result['sector_percentage'] = data_error_flag_percentage
        else:
            result['sector_percentage'] = sector_percentages
            
        #Again, no test case for this, so it needs testing
        #DAC is vocab 1 or blank
        try:
            policy_marker_codes = ";".join([str(marker['code']) for marker in activity['policy_markers'] if marker['vocabulary'] in ['1',None]])
        except (KeyError,IndexError,TypeError):
            policy_marker_codes = ""
        result['policy-marker_code'] = policy_marker_codes
        try:
            policy_marker_sig = ";".join([str(marker['significance']) for marker in activity['policy_markers'] if marker['vocabulary'] in ['1',None]])
        except (KeyError,IndexError,TypeError):
            policy_marker_sig = ""
        result['policy-marker_significance'] = policy_marker_sig
        
        try:
            result['collaboration-type_code'] = str(activity['collaboration_type']['code'])
        except (KeyError,IndexError,TypeError):
            result['collaboration-type_code'] = ""
            
        try:
            result['default-flow-type'] = str(activity['default_flow_type']['code'])
        except (KeyError,IndexError,TypeError):
            result['default-flow-type'] = ""
            
        try:
            result['default-finance-type'] = str(activity['default_finance_type']['code'])
        except (KeyError,IndexError,TypeError):
            result['default-finance-type'] = ""
            
        try:
            result['default-aid-type'] = str(activity['default_aid_type']['code'])
        except (KeyError,IndexError,TypeError):
            result['default-aid-type'] = ""
            
        try:
            result['default-tied-status'] = str(activity['default_tied_status']['code'])
        except (KeyError,IndexError,TypeError):
            result['default-tied-status'] = ""
            
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
         
        results = []
        for i in range(0,len(budget_values)):
            try:
                budget_date = budget_dates[i]
            except IndexError:
                budget_date = ""
            try:
                budget_value = budget_values[i]
            except IndexError:
                budget_value = ""
            try:
                budget_period_start = budget_period_starts[i]
            except IndexError:
                budget_period_start = ""
            try:
                budget_period_end = budget_period_ends[i]
            except IndexError:
                budget_period_end = ""
            try:
                budget_currency = budget_currencies[i]
            except IndexError:
                budget_currency = ""
            budget_valid = valid_budget(budget_date,budget_value,budget_period_start,budget_period_end,budget_currency,default_currency)
            if budget_valid:
                budget_item = deepcopy(result)
                budget_item['budget_value_value-date'] = budget_date
                budget_item['budget_value'] = budget_value
                budget_item['budget_period-start_iso-date'] = budget_period_start
                budget_item['budget_period-end_iso-date'] = budget_period_end
                if budget_currency == "":
                    budget_item['budget_value_currency'] = default_currency
                else:
                    budget_item['budget_value_currency'] = budget_currency
                results.append(budget_item)
        if len(results)>0:
            return results
        else:
            return False
    else:
        return False

"""
# Current Diagnostic method calls

base_url = 'https://www.oipa.nl/api/activities/?format=json'

activities_urls = oipa_recursive_url_getter(base_url)

print(generate_md5('hello'))
"""
