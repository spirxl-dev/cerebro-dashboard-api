from datetime import datetime
from pprint import pprint
import os

import psycopg2


evieDBPass = os.environ.get("EvieDB") # source ~/.bash_profile
evieDBPass = evieDBPass[:5] + "`" + evieDBPass[5:]
deniseDBPass = os.environ.get("DeniseDB")


def connectToDB(user, database, subDomain, password):
    conn = psycopg2.connect(
        user=user,
        database=database,
        host=f"{subDomain}.cv8jef7zawd8.eu-west-2.rds.amazonaws.com",
        password=password,
    )

    return conn


def updateStatus(tempComponent, scrapeTimestamp, greenTimeStamp, orangeTimeStamp):
    if scrapeTimestamp >= greenTimeStamp:
        if tempComponent["status"] == "None":
            tempComponent["status"] = "Green"
    elif scrapeTimestamp >= orangeTimeStamp:
        if tempComponent["status"] != "Red":
            tempComponent["status"] = "Orange"
            tempComponent[
                "info"
            ] = f"Odds {orangeTimeStamp-greenTimeStamp} behind ideal."
    else:
        tempComponent["status"] = "Red"
        tempComponent["info"] = f"Odds {orangeTimeStamp-greenTimeStamp} behind ideal."

    return tempComponent


def runComponentCheckLoop(
    newComponentsDict,
    recentScrapesDictList,
    components,
    greenTimeStamp,
    orangeTimeStamp,
):
    for component in components:
        tempComponent = component
        for scrape in recentScrapesDictList:
            if component["operand"] == "==":
                if scrape[component["reqColumn"]] == component["value"]:
                    # relevant entry to component
                    tempComponent = updateStatus(
                        tempComponent,
                        scrape["scrape_timestamp"],
                        greenTimeStamp,
                        orangeTimeStamp,
                    )
            elif component["operand"] == ">":
                if scrape[component["reqColumn"]] > component["value"]:
                    tempComponent = updateStatus(
                        tempComponent,
                        scrape["scrape_timestamp"],
                        greenTimeStamp,
                        orangeTimeStamp,
                    )

        if tempComponent["status"] == "None":
            tempComponent["status"] = "Red"
            tempComponent["info"] = "No odds found for component"

        newComponentsDict["components"].append(tempComponent)
    return newComponentsDict


def pollEvie2ups():
    conn = connectToDB("postgres", "evie_2ups_pre", "dh-database-aws", evieDBPass)

    components = [
        {
            "name": "Today's Fixtures",
            "reqColumn": "fixt_date",
            "operand": "==",
            "value": datetime.now().date(),
            "status": "None",
            "info": "",
        },
        {
            "name": "Future Fixtures",
            "reqColumn": "fixt_date",
            "operand": ">",
            "value": datetime.now().date(),
            "status": "None",
            "info": "",
        },
        {
            "name": "Paddy Odds",
            "reqColumn": "bookie",
            "operand": "==",
            "value": "Paddy Power",
            "status": "None",
            "info": "",
        },
        {
            "name": "Bet365 Odds",
            "reqColumn": "bookie",
            "operand": "==",
            "value": "Bet365",
            "status": "None",
            "info": "",
        },
        {
            "name": "SM Odds",
            "reqColumn": "exchange",
            "operand": "==",
            "value": "Smarkets",
            "status": "None",
            "info": "",
        },
        {
            "name": "MB Odds",
            "reqColumn": "exchange",
            "operand": "==",
            "value": "Matchbook",
            "status": "None",
            "info": "",
        },
        {
            "name": "BF Odds",
            "reqColumn": "exchange",
            "operand": "==",
            "value": "Betfair",
            "status": "None",
            "info": "",
        },
    ]

    greenTimeStamp = int(datetime.utcnow().timestamp()) - 30
    orangeTimeStamp = greenTimeStamp - 30

    cur = conn.cursor()
    cur.execute(
        f"SELECT fixt_date, bookie, exchange, scrape_timestamp FROM recent_scrapes WHERE scrape_timestamp >= {orangeTimeStamp}"
    )

    allRecentScrapes = cur.fetchall()

    recentScrapesDictList = [
        {
            "fixt_date": datetime.strptime(i[0], "%d/%m/%Y").date(),
            "bookie": i[1],
            "exchange": i[2],
            "scrape_timestamp": i[3],
        }
        for i in allRecentScrapes
    ]

    newComponentsDict = {"bot": "Evie2UPs", "components": []}

    # general recent_scrapes components
    newComponentsDict = runComponentCheckLoop(
        newComponentsDict,
        recentScrapesDictList,
        components,
        greenTimeStamp,
        orangeTimeStamp,
    )

    # table specific components
    cur.execute(
        f"SELECT scrape_timestamp FROM b365_back_only_scrapes WHERE scrape_timestamp >= {orangeTimeStamp}"
    )

    allRecentScrapes = cur.fetchall()

    recentScrapesDictList = [{"scrape_timestamp": i[0]} for i in allRecentScrapes]

    components = [
        {
            "name": "Bet365 Overrides",
            "reqColumn": "scrape_timestamp",
            "operand": ">",
            "value": 0,
            "status": "None",
            "info": "",
        }
    ]
    newComponentsDict = runComponentCheckLoop(
        newComponentsDict,
        recentScrapesDictList,
        components,
        greenTimeStamp,
        orangeTimeStamp,
    )

    cur.close()
    conn.close()

    return newComponentsDict  # ["components"]


def pollEvieEW():
    conn = connectToDB("postgres", "evie_ew", "dh-database-aws", evieDBPass)

    cur = conn.cursor()
    cur.execute(
        f"SELECT meeting FROM meeting_pool WHERE date = '{datetime.now().strftime('%d/%m/%y')}' AND abandoned != 't'"
    )
    allMeetings = cur.fetchall()
    allMeetings = [i[0] for i in allMeetings]

    components = []
    allMeetingsDict = {}
    for meeting in allMeetings:
        components.append({"name": meeting, "status": "None", "info": ""})
        allMeetingsDict[meeting] = {"raceIDs": []}

    cur.execute(
        f"SELECT race_id, track, time FROM all_races WHERE date = '{datetime.now().strftime('%d/%m/%y')}'"
    )
    allRaces = cur.fetchall()

    allRacesDict = {}

    for race in allRaces:
        if race[1] in allMeetingsDict:
            allMeetingsDict[race[1]]["raceIDs"].append(race[0])

        allRacesDict[race[0]] = f"{race[2]} {race[1]}"

    allRaceIDs = [i[0] for i in allRaces]

    cur.execute(f"SELECT name FROM bookies WHERE disabled != 't'")
    allBookies = cur.fetchall()
    allBookies = [i[0] for i in allBookies]

    greenTimeStamp = int(datetime.utcnow().timestamp()) - 30
    orangeTimeStamp = greenTimeStamp - 30

    cur.execute(
        f"SELECT race_id, bookie, win_back, scrape_utctimestamp FROM oc_back_scrapes WHERE scrape_utctimestamp >= {orangeTimeStamp}"
    )
    allOCBackScrapes = cur.fetchall()
    allOCBackScrapesDict = {}
    for i in allOCBackScrapes:
        if i[0] not in allOCBackScrapesDict:
            allOCBackScrapesDict[i[0]] = {"bookies": [i[1]]}
        else:
            allOCBackScrapesDict[i[0]]["bookies"].append(i[1])
            allOCBackScrapesDict[i[0]][i[1]] = {
                "winBack": i[2],
                "scrapeTimeStamp": i[3],
            }
            # allOCBackScrapesDict[i[0]]['bookies']['] =

    newComponentsDict = {"bot": "EvieEW", "components": []}

    for component in components:
        meeting = component["name"]
        tempComponent = component
        for raceID in allMeetingsDict[meeting]["raceIDs"]:
            if raceID in allOCBackScrapesDict:
                for bookie in allBookies:
                    if bookie not in allOCBackScrapesDict[raceID]:
                        tempComponent["status"] = "Red"
                        tempComponent[
                            "info"
                        ] += f"\n{allRacesDict[raceID]} {bookie} odds missing"
                    else:
                        # for bookie in allOCBackScrapesDict[raceID]:
                        if allOCBackScrapesDict[raceID][bookie]["winBack"] <= 1:
                            tempComponent["status"] = "Red"
                            tempComponent[
                                "info"
                            ] += f"{allRacesDict[raceID]} {bookie} odds <= 1"
                        elif (
                            allOCBackScrapesDict[raceID][bookie]["scrapeTimeStamp"]
                            >= greenTimeStamp
                        ):
                            if tempComponent["status"] == "None":
                                tempComponent["status"] = "Green"
                        elif (
                            allOCBackScrapesDict[raceID][bookie]["scrapeTimeStamp"]
                            >= orangeTimeStamp
                        ):
                            if tempComponent["status"] != "Red":
                                tempComponent["status"] = "Orange"
                                tempComponent[
                                    "info"
                                ] += f"\n{allRacesDict[raceID]} {bookie} odds {orangeTimeStamp-greenTimeStamp} behind ideal."
                        else:
                            tempComponent["status"] = "Red"
                            tempComponent[
                                "info"
                            ] += f"\n{allRacesDict[raceID]} {bookie} odds {orangeTimeStamp-greenTimeStamp} behind ideal."
        newComponentsDict["components"].append(tempComponent)

    return newComponentsDict  # ["components"]


def pollDenise():
    conn = connectToDB("postgres", "postgres", "dh-new-database", deniseDBPass)


newComponentsDict = pollEvieEW()


for i in newComponentsDict["components"]:
    print(i["status"], i["info"])
