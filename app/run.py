from main_app import *
from datetime import datetime

base_url = 'https://www.oipa.nl/api/activities/?format=json&fields=budgets,reporting_organisations,iati_identifier,url,activity_dates,aggregations,title,participating_organisations,recipient_countries,recipient_regions,sectors,policy_markers,collaboration_type,default_flow_type,default_finance_type,default_aid_type,default_tied_status'

# base_url = base_url + "&reporting_organisation="
# reporters = [
#     "XM-DAC-41114",
#     "41122",
#     "SE-0",
#     "GB-GOV-1",
#     "BE-10",
#     "NO-BRC-971277882",
#     "44000",
#     "AU-5",
#     "XM-DAC-7",
#     "DAC-1601",
#     "CA-3",
#     "XI-IATI-EC_DEVCO",
#     "XI-IATI-EC_NEAR",
#     "US-1", "US-10", "US-11", "US-13", "US-18", "US-2", "US-21", "US-6", "US-7", "US-8", "US-USAGOV",
#     "XM-DAC-918-3",
#     "47122",
#     "IADB", "XI-IATI-IADB",
#     "NZ-1",
#     "GB-CHC-207544",
#     "XI-IATI-EC_ECHO",
#     "46002",
#     "GB-CHC-220949",
#     "NL-KVK-41198890", "NL-KvK-41198890",
#     "NL-KVK-41152786",
#     "NL-KVK-51756811",
#     "GB-COH-213890",
#     "NL-KVK-27108436",
#     "GB-COH-1762840",
#     "NL-KVK-41158230"
# ]
# for reporter in reporters:
#     base_url = base_url + reporter + ","

filename = "output_"+datetime.now().strftime("%Y_%m_%d")+".csv"

oipa_url_getter(base_url,filename)

print("\n")
print("Done.")