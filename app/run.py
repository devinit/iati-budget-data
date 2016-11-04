from main_app import *

base_url = 'https://www.oipa.nl/api/activities/?format=json'

activities_urls = oipa_recursive_url_getter(base_url)

print(generate_md5('hello'))