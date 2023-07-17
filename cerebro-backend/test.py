import requests
from pprint import pprint

output = requests.get('http://localhost:8000/evie-2ups-status' )
pprint(output.text)