from main_app import *
from datetime import datetime

base_url = 'https://www.oipa.nl/api/activities/?format=json'

filename = "output_"+datetime.now().strftime("%Y_%m_%d")+".csv"

oipa_recursive_url_getter(base_url,filename)

print("Done.")