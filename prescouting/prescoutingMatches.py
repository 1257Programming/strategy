"""Given an event key, this program returns matches to prescout for each team attending that event as a dict.
   Format: {1257: [match1, match2, match3, match4], 7521: [match1, match2, match3, match4], ...} or
           {1257: [match2, match2], 7521: [match1, match2], ...}"""

import json, requests
from datetime import date
year = date.today().year

# Create session for all TBA requests
s = requests.Session()
# Try to read authKey from tbaAuth.txt
try:
    authKey = open("tbaAuth.txt", "r")
    s.headers.update({'X-TBA-Auth-Key': authKey.read().strip()})
    authKey.close()
# Exit program if tbaAuth.txt does not exist
except FileNotFoundError:
    print("Error: TBA API authorization key not found. Please include your key in a text file named tbaAuth.txt in the same directory as this file.")
    exit()

# Makes a TBA request, returns content of request as json if possible, returns 1 if there's an error
def tba_request(query):
    try:
        return json.loads(s.get("http://www.thebluealliance.com/api/v3/" + query).text)
    except:
        return 1

mode = ""

raw_districts = tba_request("districts/" + str(year))
district_key_list = [district["abbreviation"] for district in raw_districts]
event_codes = tba_request("events/" + str(year) + "/keys")

# If event is in the future, or if event type is undefined, offseason, or preseason, return that it is not suitable for scouting
def is_scoutable(event_type, event_date):
    return not (event_type < 0 or event_type > 6 or event_date > date.today())

def tba_date_to_obj(string):
    return date(int(string[:4]), int(string[5:7]), int(string[8:10]))

def is_team(team):
    info = tba_request("team/frc" + team + "/simple")
    if "key" in info:
        return True

while True:
    print("Enter\n1. an event key (only letters, no year) to select a specific event,\n2. a district name to get a list of all upcoming events for the district, or\n3. a comma-separated list of team numbers for which you want matches.")
    key_input = input().lower().strip()
    if key_input in district_key_list:
        mode = "district"
        break
    elif key_input.isdigit() or "," in key_input:
        mode = "csv"
        break
    elif (str(year) + key_input) in event_codes or key_input in event_codes:
        mode = "code"
        break
    else:
        print("\nError: input invalid. Try again.\n")

# Makes sure that the district key entered is valid
if mode == "district":
    print("\n" + key_input.upper() + " events:")
    district_events = tba_request("district/" + str(year) + key_input + "/events")
    district_events = sorted(district_events, key = lambda x: tba_date_to_obj(x["start_date"]))
    for event_item in tuple(enumerate(district_events)):
        print(f"{event_item[0] + 1}: {event_item[1]['short_name']}")
    print("\nEnter the number next to the event you want to select: ", end = "")
    while True:
        try:
            event_selected = int(input().strip())
            if event_selected > 0:
                event_key = district_events[event_selected - 1]["key"]
                break
            else:
                print("\nError: input invalid. Try again: ", end = "")
        except:
            print("\nError: input invalid. Try again: ", end = "")

if mode == "code":
    if key_input not in event_codes:
        event_key = str(year) + key_input
    else:
        event_key = key_input

if mode == "district" or mode == "code":
    # Makes a list teams with all teams attending the specified event
    event_teams = tba_request("event/" + event_key + "/teams")
    teams = []
    for team in event_teams:
        teams.append(team["team_number"])

if mode == "csv":
    teams = key_input.strip(", ").split(",")
    teams = [team.strip() for team in teams]
    for team in teams[:]:
        if not is_team(team):
            if team != "":
                input(f"\nWarning: it appears that team {team} does not exist, so they will not be scouted. Press [enter] to continue.")
            teams.remove(team)

teams = sorted(teams, key = int)

print("\nHow many matches to prescout per team? (2 or 4): ", end = "")
# Input how many matches to prescout per team (can only be 2 or 4)
while True:
    try:
        num_to_scout = int(input().strip())
        if num_to_scout == 2 or num_to_scout == 4:
            break
        else:
            print("\nError: matches to prescout must be either 2 or 4. Try again: ", end = "")
    except:
        print("\nError: matches to prescout must be either 2 or 4. Try again: ", end = "")

print("\nOnly matches with video on TBA? Y/N: ", end = "")
while True:
    video = input().lower().strip()
    if video == "y" or video == "yes":
        video = True
        break
    elif video == "n" or video == "no":
        video = False
        break
    else:
        print("\nError: matches with video must be Y/N. Try again: ", end = "")

# Initialize scouting_events variable, which holds the team number and event key of latest scoutable event
scouting_events = {}
# For each team, add its latest scoutable event to scouting_events
for team in teams:
    team_events = tba_request("team/frc" + str(team) + "/events/" + str(year) + "/simple") # Retrieves list of team's events for season
    team_events = sorted(team_events, key = lambda x: tba_date_to_obj(x["start_date"])) # Sorts by start date
    event_index = 0
    for event in reversed(team_events): # For each potential event (going by most recent), use that event if it's scoutable 
        if is_scoutable(event["event_type"], tba_date_to_obj(event["start_date"])):
            scouting_events[team] = event["key"]
            break
    if team not in scouting_events:
        scouting_events[team] = None

# Initialize scouting_matches variable, which will hold the result
scouting_matches = {}
# Loop through each team to choose which matches to scout
for team, event in scouting_events.items():
    if event == None:
        scouting_matches[team] = ["No event", []]
        continue
    # Get a list of their matches from TBA
    matches = tba_request("team/frc" + str(team) + "/event/" + event + "/matches")
    # Initialize match_list to hold a list of match keys
    match_list = []
    # If the match has videos, add it to match_list
    for match in matches:
        if video:
            try:
                if len(match["videos"]) > 0:
                    match_list.append(match)
            except TypeError:
                pass
        elif not video:
            match_list.append(match)
    # Initialize team_matches, which represents each match with a number (to help with sorting)
    team_matches = {"qm": [], "qf": [], "sf": [], "f": []}
    # Add every match in the TBA request to team_matches
    for match in match_list:
        team_matches[match["comp_level"]].append(match)
    # Sort each of the components of team_matches to create ordered lists of every match type (in number form)
    for comp_level in team_matches:
        team_matches[comp_level] = sorted(team_matches[comp_level], key = lambda x: x["match_number"])
    # Initialize a list scouting_matches[team] to hold chosen matches
    scouting_matches[team] = ["", []]
    # If scouting two matches, choose one playoffs match (if possible) and the rest quals
    scouting_matches[team][0] = event
    if num_to_scout == 2:
        # If a finals match is available, then choose it
        if len(team_matches["f"]) > 0:
            scouting_matches[team][1].append(team_matches["f"].pop()["key"].split("_")[1])
        # If a semis match is available and no playoffs have been chosen, then choose it
        elif len(team_matches["sf"]) > 0:
            scouting_matches[team][1].append(team_matches["sf"].pop()["key"].split("_")[1])
        # If a quarters match is available and no playoffs have been chosen, then choose it
        elif len(team_matches["qf"]) > 0:
            scouting_matches[team][1].append(team_matches["qf"].pop()["key"].split("_")[1])
        # Keep choosing quals until two matches have been chosen
        while(len(scouting_matches[team][1]) < 2 and len(team_matches["qm"]) > 0):
            scouting_matches[team][1].append(team_matches["qm"].pop()["key"].split("_")[1])
    # If scouting four matches, choose two playoffs matches (from different levels if possible) and the rest quals
    else:
        # If a finals match is available, then choose it
        if len(team_matches["f"]) > 0:
            scouting_matches[team][1].append(team_matches["f"].pop()["key"].split("_")[1])
        # If a semis match is available, then choose it
        if len(team_matches["sf"]) > 0:
            scouting_matches[team][1].append(team_matches["sf"].pop()["key"].split("_")[1])
        # Keep choosing quarters until two playoffs matches have been chosen
        while(len(scouting_matches[team][1]) < 2 and len(team_matches["qf"]) > 0):
            scouting_matches[team][1].append(team_matches["qf"].pop()["key"].split("_")[1])
        # Keep choosing quals until four matches have been chosen
        while(len(scouting_matches[team][1]) < 4 and len(team_matches["qm"]) > 0):
            scouting_matches[team][1].append(team_matches["qm"].pop()["key"].split("_")[1])

output = open("output.txt","w")
output.write("team;event;[matches]")
for team in scouting_matches:
    output.write(f"\n{team};{scouting_matches[team][0]};{scouting_matches[team][1]}")
output.close()
print("\nDone, check output.txt for your prescouting matches. Thank you, and have a nice day!", end = "")