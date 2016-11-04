import requests
import pandas as pd
import sys
import hashlib

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

    # exctact activity URLs and store in the list
    for activity in r.json()['results']:

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

"""
# Current Diagnostic method calls

base_url = 'https://www.oipa.nl/api/activities/?format=json'

activities_urls = oipa_recursive_url_getter(base_url)

print(generate_md5('hello'))
"""
