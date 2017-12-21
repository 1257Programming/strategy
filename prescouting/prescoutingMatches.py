"""Given an event key, this program returns matches to prescout for each team attending that event as a dict.
   Format: {1257: [match1, match2, match3, match4], 7521: [match1, match2, match3, match4], ...} or
           {1257: [match2, match2], 7521: [match1, match2], ...}"""

import json, datetime, requests
# Create session for all TBA requests
s = requests.Session()
# Try to read authKey from tbaAuth.txt
try:
    authKey = open("tbaAuth.txt", "r").read()
    s.headers.update({'X-TBA-Auth-Key': authKey})
# Exit program if tbaAuth.txt does not exist
except FileNotFoundError:
    print("[ERROR]: Auth key not found. Please include your auth key in a text file named tbaAuth.txt in the same directory as this file.")
    exit()

# Makes a TBA request, returns content of request as json
def tbaRequest(query):
    r = s.get("http://www.thebluealliance.com/api/v3/" + query)
    return json.loads(r.text)

# If event is in the future, or if event type is undefined, offseason, or preseason, return that it is not suitable for scouting
isScoutable = lambda eventType, eventDate: not (eventType < 0 or eventType > 5 or eventDate > datetime.date.today())

# Makes sure that the event key entered is valid
eventKeyInvalid = True
while(eventKeyInvalid):
    eventKeyInvalid = False
    # Input event key
    eventKey = input("Enter event key: ")
    # Make a list teamKeys with all teams attending the specified event
    eventTeamsReq = tbaRequest("event/" + eventKey + "/teams")
    teamKeys = []
    # If event key is invalid, print error message and re-enter event key
    try:
        for e in eventTeamsReq:
            teamKeys.append(e["key"])
    except TypeError:
        eventKeyInvalid = True
        print("[ERROR]: This event doesn't exist. Try again.")

# Input how many matches to prescout per team (can only be 2 or 4)
numToScoutInvalid = True
while(numToScoutInvalid):
    numToScoutInvalid = False
    try:
        numToScout = int(input("How many matches to prescout per team? (2 or 4): "))
        if(not(numToScout == 2 or numToScout == 4)):
            numToScoutInvalid = True
    except TypeError:
        numToScoutInvalid = True
    if(numToScoutInvalid):
        print("[ERROR]: Matches to scout must be either 2 or 4. Try again.")

# Initialize eventsToScout variable, which holds the team number and event key of latest scoutable event
eventsToScout = {}
# For each team, add its latest scoutable event to eventsToScout
for t in teamKeys:
    # Print status message
    print("[STATUS]: Finding latest scoutable event for " + t)
    # Request containing all events for that team in that year
    teamEventsReq = tbaRequest("team/" + t + "/events/" + eventKey[:4] + "/simple")
    # Initialize latestEvent variable, which holds event key and start date
    latestEvent = {"key": "", "date": datetime.date(1, 1, 1)}
    # Loop through each event to find the latest scoutable event
    for e in teamEventsReq:
        # Retrieves start date as string
        dateString = e["start_date"]
        # Stores event as dict, which holds event key and start date (as datetime.date object)
        currentEvent = {"key": e["key"], "date": datetime.date(int(dateString[:4]), int(dateString[5:7]), int(dateString[8:10]))}
        # If currentEvent occurs after latestEvent and is suitable for scouting, update latestEvent to currentEvent
        if(currentEvent["date"] > latestEvent["date"] and isScoutable(e["event_type"], currentEvent["date"])):
            latestEvent = currentEvent
    # Add their latest scoutable event to eventsToScout
    eventsToScout[t] = latestEvent["key"]

# Initialize matchesToScout variable, which will hold the result
matchesToScout = {}
# Loop through each team to choose which matches to scout
for t, e in eventsToScout.items():
    print("[STATUS]: Choosing matches for " + t)
    # Get a list of their matches from TBA
    matchReq = tbaRequest("team/" + t + "/event/" + e + "/matches")
    # Initialize matchList to hold a list of match keys
    matchList = []
    # If the match has videos, add it to matchList
    for match in matchReq:
        try:
            if(match["videos"] != []):
                matchList.append(match["key"])
        except TypeError:
            pass
    # Initialize allMatches, which represents each match with a number (to help with sorting)
    allMatches = {"qm": {}, "qf": {}, "sf": {}, "f": {}}
    # Add every match in the TBA request to allMatches
    for m in matchList:
        # Remove the event data from the match key
        matchID = m.split("_")[1]
        # If the match is from quals, add it to allMatches["qm"]
        if(matchID[0:2] == "qm"):
            allMatches["qm"][int(matchID[2:])] = m
        # If the match is from quarters, add it to allMatches["qf"]
        elif(matchID[0:2] == "qf"):
            allMatches["qf"][10*int(matchID[2]) + int(matchID[4:])] = m
        # If the match is from semis, add it to allMatches["sf"]
        elif(matchID[0:2] == "sf"):
            allMatches["sf"][10*int(matchID[2]) + int(matchID[4:])] = m
        # If the match is from finals, add it to allMatches["f"]
        elif(matchID[0:2] == "f"):
            allMatches["f"][10*int(matchID[1]) + int(matchID[3:])] = m
    # Sort each of the components of allMatches to create ordered lists of every match type (in number form)
    sortedQM = sorted(allMatches["qm"])
    sortedQF = sorted(allMatches["qf"])
    sortedSF = sorted(allMatches["sf"])
    sortedF = sorted(allMatches["f"])
    # Initialize a list matchesToScout[t] to hold chosen matches
    matchesToScout[t] = []
    # If scouting two matches, choose one playoffs match (if possible) and the rest quals
    if(numToScout == 2):
        # If a finals match is available, then choose it
        try:
            matchesToScout[t].append(allMatches["f"][sortedF.pop()])
        except IndexError:
            pass
        # If a semis match is available and no playoffs have been chosen, then choose it
        if(len(matchesToScout[t]) < 1):
            try:
                matchesToScout[t].append(allMatches["sf"][sortedSF.pop()])
            except IndexError:
                pass
        # If a quarters match is available and no playoffs have been chosen, then choose it
        if(len(matchesToScout[t]) < 1):
            try:
                matchesToScout[t].append(allMatches["qf"][sortedQF.pop()])
            except IndexError:
                pass
        # Keep choosing quals until two matches have been chosen
        while(len(matchesToScout[t]) < 2 and len(sortedQM) > 0):
            matchesToScout[t].append(allMatches["qm"][sortedQM.pop()])
    # If scouting four matches, choose two playoffs matches (from different levels if possible) and the rest quals
    else:
        # If a finals match is available, then choose it
        try:
            matchesToScout[t].append(allMatches["f"][sortedF.pop()])
        except IndexError:
            pass
        # If a semis match is available, then choose it
        try:
            matchesToScout[t].append(allMatches["sf"][sortedSF.pop()])
        except IndexError:
            pass
        # Keep choosing quarteres until two playoffs matches have been chosen
        while(len(matchesToScout[t]) < 2 and len(sortedQF) > 0):
            matchesToScout[t].append(allMatches["qf"][sortedQF.pop()])
        # Keep choosing quals until four matches have been chosen
        while(len(matchesToScout[t]) < 4 and len(sortedQM) > 0):
            matchesToScout[t].append(allMatches["qm"][sortedQM.pop()])
print(matchesToScout)
