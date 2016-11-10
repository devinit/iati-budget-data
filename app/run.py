from main_app import *
from datetime import datetime

base_url = 'https://www.oipa.nl/api/activities/?format=json&fields=budgets,reporting_organisations,iati_identifier,url,activity_dates,aggregations,title,participating_organisations,recipient_countries,recipient_regions,sectors,policy_markers,collaboration_type,default_flow_type,default_finance_type,default_aid_type,default_tied_status&total_budget_value_gte=1&reporting_organisation='

reporters = [
    # "XM-DAC-41114",
    "GB-CHC-207544"
]
for reporter in reporters:
    base_url = base_url + reporter + ","

filename = "output_"+datetime.now().strftime("%Y_%m_%d")+".csv"

oipa_url_getter(base_url,filename)

print("\n")
print("Done.")