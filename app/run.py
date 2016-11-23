from main_app import *
from datetime import datetime

base_url = 'https://www.oipa.nl/api/activities/?format=json&fields=budgets,reporting_organisations,iati_identifier,url,activity_dates,aggregations,title,participating_organisations,recipient_countries,recipient_regions,sectors,policy_markers,collaboration_type,default_flow_type,default_finance_type,default_aid_type,default_tied_status'
# For some reason localhost fails on url, so we need to omit it
# base_url = 'http://172.18.0.1:8000/api/activities/?format=json&fields=budgets,reporting_organisations,iati_identifier,activity_dates,aggregations,title,participating_organisations,recipient_countries,recipient_regions,sectors,policy_markers,collaboration_type,default_flow_type,default_finance_type,default_aid_type,default_tied_status'

base_url = base_url + '&page_size=400'

base_url = base_url + '&total_hierarchy_budget_gte=0.01'

filename = "output_"+datetime.now().strftime("%Y_%m_%d")+".csv"

failed_pages = oipa_url_getter(base_url,filename)

print("Failed pages: ")
print(",".join(failed_pages))

print("\n")
print("Done.")