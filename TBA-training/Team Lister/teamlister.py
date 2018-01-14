import json, sys, requests

authKey = sys.argv[1]

output = open("output.txt","w")

s = requests.Session()
s.headers.update({'X-TBA-Auth-Key': authKey})

events = json.loads(s.get("http://www.thebluealliance.com/api/v3/events/2017").text)
eventinfo = {}
for event in events:
    eventinfo[event["short_name"]] = [event["key"]]
for event in eventinfo:
    teams = sorted([int(team["key"][3:]) for team in json.loads(s.get("http://www.thebluealliance.com/api/v3/event/" + eventinfo[event][0] + "/teams").text)])
    eventinfo[event].append(teams)
for event in eventinfo:
    output.write(event + ": ")
    output.write(str(eventinfo[event][1]))
    output.write("\n")