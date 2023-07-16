from pprint import pprint



def pollEvie2ups():

    # Method connects to DB
    # Sends get request 
    # DB returns json file like above
    # Method outputs json

    example_json = {
    "bot": "Evie2UPs",
    "components": [
        {   
            "componentName": "skyScraper1", 
            "status": "Green", 
            "info": "null"},
        {
            "componentName": "paddyScraper1",
            "status": "Orange",
            "info": "Last poll was 45 secs",
        },
        {
            "componentName": "botPoller1",
            "status": "Red",
            "info": "Missing bet365 odds",
        },
    ],
    }
    return example_json["components"]


example_json = {
    "bot": "Evie2UPs",
    "components": [
        {   
            "componentName": "skyScraper1", 
            "status": "Green", 
            "info": "null"},
        {
            "componentName": "paddyScraper1",
            "status": "Orange",
            "info": "Last poll was 45 secs",
        },
        {
            "componentName": "botPoller1",
            "status": "Red",
            "info": "Missing bet365 odds",
        },
    ],
}

for i in example_json["components"]:
    print(i['status'])