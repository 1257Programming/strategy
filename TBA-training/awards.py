"""An API, or application programming interface, is an interface which, to put it generally, allows a user to send data to an application from another, or receive
data in an application from another. The Blue Alliance has an API called TBA API that can be used to request data about FRC. The data is returned in a format called
JSON (JavaScript Object Notation), which is converted to a native Python object with nested data (lists, dictionaries, etc.), making the data easy to process and use.

To get the data, this program uses the requests module. The requests module is not a default module and has to be installed using pip, but the module makes API
requests easier to make and is an easy, one-time install."""

import requests, json, sys # imports requests module to make requests to TBA API, json module to process requested data, and sys to access headers argument

"""API authentication key is stored as a program argument that is included in sys.argv at the program's start. Storing the key in the program would make the key accessible to others
if pushed to a git repository, so the better way to access the key is to store it as a program argument. The program arguments are stored as a list, the first item
of which is always the file path for the program since the only additional argument is the API key, the index of the key will be 1 as it is the second item."""
key = sys.argv[1]
# when making an API request, a "headers" dictionary is needed. For TBA API, the dictionary only requires the string "X-TBA-Auth-Key" set to the value of the auth key.
headers = {"X-TBA-Auth-Key":key}

# taking the input team number as a string
team = input("What team would you like to pick? ")

# this dictionary will hold the info for the events of a team
eventdict = {}

"""request the 2017 event data for the given team, using the headers argument (the auth key) as needed for requests.get()
because the requested item includes not just the data but also other info like the request status code, appending .text returns just the requested data
then json.loads() converts the data from a JSON object to a Python object. The data in this case becomes nested lists and dictionaries"""
rawevents = json.loads(requests.get("https://www.thebluealliance.com/api/v3/team/frc" + team + "/events/2017/simple", headers=headers).text)
# for each event in the data, create a value/key pair in eventdict in this format: {"2017code":{"name":name,"awards":[]}}
for event in rawevents:
    eventdict["2017" + event["event_code"]] = {"name":event["name"],"awards":[]}

# for each event, get the awards earned by the inputted team and append each award's name to the "awards" list in the key-dictionary for that event
for event in eventdict:
    awards = json.loads(requests.get("https://www.thebluealliance.com/api/v3/team/frc" + team + "/event/" + event + "/awards", headers=headers).text)
    for award in awards:
        eventdict[event]["awards"].append(award["name"])

# this processes the printed output for each event
for event in eventdict:
    # if no awards were won, a message is printed saying that the inputted team did not win an award at that event
    if len(eventdict[event]["awards"]) == 0:
        print("Team " + team + " did not win an award at " + eventdict[event]["name"] + ".")
    # if 1 award was won, a message is printed saying that the inputted team won that award at that event
    elif len(eventdict[event]["awards"]) == 1:
        print("Team " + team + " won the " + eventdict[event]["awards"][0] + " at " + eventdict[event]["name"] + ".")
    # if 2 awards were won, a message is printed saying that the inputted team won the first award and the second award at that event
    elif len(eventdict[event]["awards"]) == 2:
        print("Team " + team + " won the " + eventdict[event]["awards"][0] + " and the " + eventdict[event]["awards"][1] + " at " + eventdict[event]["name"] + ".")
    # in any other scenario (>2 awards won), the printed message is constructed in two steps
    else:
        # an output string is created
        output = ""
        # for every award *except the last one*, "the [award]," is added to the output string
        for award in eventdict[event]["awards"]:
            if award != eventdict[event]["awards"][-1]:
                output += "the " + award + ", "
        # " and the [award]" is added to the output string
        output += "and" + " the " + eventdict[event]["awards"][-1]
        # the final output string is in this form: "the [award1], the [award2], the [award3],... and the [lastaward]"
        # a message is printed saying that the team won [output] at that event
        print("Team " + team + " won " + output + " at " + eventdict[event]["name"] + ".")