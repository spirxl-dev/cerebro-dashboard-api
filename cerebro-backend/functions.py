from datetime import datetime
from pprint import pprint
import os

import psycopg2


evieDBPass = os.environ.get("EvieDB") # run source ~/.bash_profile if complaining
evieDBPass = evieDBPass[:5] + "`" + evieDBPass[5:]
deniseDBPass = os.environ.get("DeniseDB")


def connectToDB(user, database, subDomain, password):

    conn = psycopg2.connect(user =user, database=database, host = f'{subDomain}.cv8jef7zawd8.eu-west-2.rds.amazonaws.com', password=password)

    return conn


def updateStatus(tempComponent, scrapeTimestamp, greenTimeStamp, orangeTimeStamp):
    if scrapeTimestamp >= greenTimeStamp:
        if tempComponent['status'] == "None":
            tempComponent['status'] = "Green"
    elif scrapeTimestamp >= orangeTimeStamp:
        if tempComponent['status'] != "Red":
            tempComponent['status'] = "Orange"
            tempComponent['info'] = f"Odds {orangeTimeStamp-greenTimeStamp} behind ideal."
    else:
        tempComponent['status'] = "Red"
        tempComponent['info'] = f"Odds {orangeTimeStamp-greenTimeStamp} behind ideal."

    return tempComponent



def runComponentCheckLoop(newComponentsDict, recentScrapesDictList, components, greenTimeStamp, orangeTimeStamp):   

    for component in components:
        tempComponent = component
        for scrape in recentScrapesDictList:
            if component['operand'] == "==":
                if scrape[component['reqColumn']] == component['value']:
                    #relevant entry to component
                    tempComponent = updateStatus(tempComponent, scrape['scrape_timestamp'], greenTimeStamp, orangeTimeStamp)
            elif component['operand'] == ">":
                if scrape[component['reqColumn']] > component['value']:
                    tempComponent = updateStatus(tempComponent, scrape['scrape_timestamp'], greenTimeStamp, orangeTimeStamp)


        if tempComponent['status'] == "None":
            tempComponent['status'] = "Red"
            tempComponent['info'] = "No odds found for component"

        newComponentsDict['components'].append(tempComponent)
    return newComponentsDict



def pollEvie2ups():

    conn = connectToDB('postgres', 'evie_2ups_pre', 'dh-database-aws', evieDBPass)

    components = [{"name": "Today's Fixtures", "reqColumn": "fixt_date", "operand": "==", "value": datetime.now().date(), "status": "None", "info":""},
                {"name": "Future Fixtures", "reqColumn": "fixt_date", "operand": ">", "value": datetime.now().date(), "status": "None", "info":""},
                {"name": "Paddy Odds", "reqColumn": "bookie", "operand": "==", "value": "Paddy Power", "status": "None", "info":""},
                {"name": "Bet365 Odds", "reqColumn": "bookie", "operand": "==", "value": "Bet365", "status": "None", "info":""},
                {"name": "SM Odds", "reqColumn": "exchange", "operand": "==", "value": "Smarkets", "status": "None", "info":""},
                {"name": "MB Odds", "reqColumn": "exchange", "operand": "==", "value": "Matchbook", "status": "None", "info":""},
                {"name": "BF Odds", "reqColumn": "exchange", "operand": "==", "value": "Betfair", "status": "None", "info":""}]




    greenTimeStamp = int(datetime.utcnow().timestamp()) - 30
    orangeTimeStamp = greenTimeStamp - 30


    cur = conn.cursor()
    cur.execute(f"SELECT fixt_date, bookie, exchange, scrape_timestamp FROM recent_scrapes WHERE scrape_timestamp >= {orangeTimeStamp}")

    allRecentScrapes = cur.fetchall()

    recentScrapesDictList = [{"fixt_date":datetime.strptime(i[0],"%d/%m/%Y").date(), "bookie":i[1], "exchange":i[2], "scrape_timestamp":i[3]} for i in allRecentScrapes]

    newComponentsDict = {"bot": "Evie2UPs", "components":[]}

    #general recent_scrapes components
    newComponentsDict = runComponentCheckLoop(newComponentsDict, recentScrapesDictList, components, greenTimeStamp, orangeTimeStamp)




    #table specific components
    cur.execute(f"SELECT scrape_timestamp FROM b365_back_only_scrapes WHERE scrape_timestamp >= {orangeTimeStamp}")

    allRecentScrapes = cur.fetchall()

    recentScrapesDictList = [{"scrape_timestamp":i[0]} for i in allRecentScrapes]

    components = [{"name": "Bet365 Overrides", "reqColumn": "scrape_timestamp", "operand": ">", "value": 0, "status": "None", "info":""}]
    newComponentsDict = runComponentCheckLoop(newComponentsDict, recentScrapesDictList, components, greenTimeStamp, orangeTimeStamp)


    cur.close()
    conn.close()
    
    return newComponentsDict#["components"]


def pollDenise():
    conn = connectToDB('postgres', 'postgres', 'dh-new-database', deniseDBPass)



newComponentsDict = pollEvie2ups()


for i in newComponentsDict["components"]:
    print(i['status'], i['info'])