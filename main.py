from fastapi import FastAPI, Request, HTTPException
from pydantic import BaseModel
import requests
import os
from dotenv import load_dotenv
from rapidfuzz import process, fuzz

load_dotenv()

app = FastAPI(title="GroupMe Bot")
PORT = os.getenv("PORT") or 8000 
BOT_ID = os.getenv("GROUPME_BOT_ID")
GROUPME_ACCESS_TOKEN = os.getenv("GROUPME_ACCESS_TOKEN")

if not BOT_ID:
    raise ValueError("GROUPME_BOT_ID not set in .env")

GROUPME_POST_URL = "https://api.groupme.com/v3/bots/post"

LOCATIONS = {
    "Albany": [
        {'id':'1','type':'location','name':'UAlbany (Tennis Courts)','lat': '42.685231','lng': '-73.831806'},
        {'id':'2','type':'location','name':'Corning Preserve Boat Launch','lat': '42.656085','lng': '-73.743020'},
        {'id':'3','type':'location','name':'Delmar Bikepath(Slingerlands)','lat': '42.629096','lng': '-73.862722'},
        {'id':'4','type':'location','name':'Schuyler Flatts Cultural Park(Town of Colonie)','lat': '42.706385','lng': '-73.710876',"address":"595 Broadway, Watervliet, NY 12189"},
    ],"Clifton Park": [
        {'id':'5','type':'location','name':"The Klam'r Tavern And Marina",'lat': '42.796767','lng': '-73.760907'},
        {'id':'6','type':'location','name':"Vischer Ferry(Whipple Truss Bridge)",'lat': '42.792802','lng': '-73.795840'},
        {'id':'7','type':'location','name':"Leah's Bakery",'lat': '42.934827','lng': '-73.807381',"address":"146 Raylinsky Rd, Ballston Lake, NY 12019"}
    ],"Troy": [
        {'id':'8','type':'location','name':"RPI (ECAV,upper renwyck field)",'lat': '42.735070','lng': '-73.667017',"address":"110 8th St, Troy, NY 12180"}
    ],"Cohoes": [
        {'id':'9','type':'location','name':"Alexander Street Trailhead (Mohawk-Hudson)",'lat': '42.760899','lng': '-73.704022','runtype':'bikepath'},
        {'id':'10','type':'location','name':"Cannon Street Trailhead",'lat': '42.757988','lng': '-73.688318','runtype':'bikepath',"address":"260 B Cannon St, Green Island, NY 12183"},
    ],"Niskayuna": [
        {'id':'11','type':'location','name':"Lions Park",'lat': '42.777019','lng': '-73.824418','runtype':'bikepath',"address":"3439 Rosendale Rd, Niskayuna, NY 12309"}
    ]
}
SHORT_LOCATIONS = ['ualbany','ualbs','corning','delmar bikepath','schuyler flatts','klam','vischer',
                   'leah bakery','rpi','alexander','cannon','lions park']
SCHEDULE = [{'date':'03/14/2026','event':'❗Running of the Green @SchalmontHS aka-ROTG(REQUIRED)','distance':'5k'},{'date':'04/11/2026','event':'Helderberg to Hudson aka-H2H','distance':'13.1mi'},{'date':'05/02/2026','event':'Bacon Hill Bonanza','distance':'10k'},
            {'date':'05/30/2026','event':'❗Delightful Run for Women(REQUIRED:if female)','distance':'5k'},{'date':'06/06/2026','event':'❗Kinderhook OK 5K(REQUIRED)','distance':'5k'},{'date':'06/06/2026','event':'USATF Masters 4 Miler','distance':'4mi'},
            {'date':'07/04/2026','event':'Firecracker 4','distance':'4mi'},{'date':'07/04/2026','event':'Freedom Mile','distance':'1mi'},{'date':'07/12/2026','event':'Boilermaker','distance':'15k'},
            {'date':'09/06/2026','event':'Run 4 the River','distance':'13.1mi'},{'date':'09/12/2026','event':'❗Malta 5k(REQUIRED)','distance':'5k'},
            {'date':'10/03/2026','event':'Barn to Bridge','distance':'5k'},{'date':'10/11/2026','event':'Mohawk Hudson River','distance':'13.1mi'},{'date':'11/08/2026','event':'❗Stackadeathon(REQUIRED)','distance':'15k'},]

class GroupMeMessage(BaseModel):
    """Pydantic model for incoming GroupMe webhook payload"""
    id: str
    text: str | None = None
    sender_id: str
    sender_type: str | None = None
    name: str | None = None
    group_id: str


def send_message(text: str, attachments: list[dict] | None = None):
    """Send a message back to the group via the bot"""
    if not text.strip():
        return

    payload = {"bot_id": BOT_ID, "text": text}
    if attachments:
        payload["attachments"] = attachments

    response = requests.post(GROUPME_POST_URL, json=payload)
    if response.status_code != 202:
        print(f"Failed to send message: {response.text}")


def handle_word_match(user_input: str)-> str:
    '''Tries to match the users input to a list of locations to identify the correct one'''
    user_input = user_input.strip().lower()

    # Find the single closest match (returns tuple: (best_match, score, index))
    best_match, score, _ = process.extractOne(
        user_input,
        SHORT_LOCATIONS,
        scorer=fuzz.token_sort_ratio   # or fuzz.ratio, fuzz.partial_ratio, etc.
    )

    if score >= 60:  # adjustable threshold (70-85 is common)
        if best_match == 'ualbany' or best_match == 'ualbs':
            return '1'
        elif best_match == 'corning':
            return '2'
        elif best_match == 'delmar bikepath':
            return '3'
        elif best_match == 'schuyler flatts':
            return '4'
        elif best_match == 'klam':
            return '5'
        elif best_match == 'vischer':
            return '6'
        elif best_match == 'leah bakery':
            return '7'
        elif best_match == 'rpi':
            return '8'
        elif best_match == 'alexander':
            return '9'
        elif best_match == 'cannon':
            return '10'
        elif best_match == 'lions park':
            return '11'
    else:
        send_message(f"Sorry, I don't understand '{user_input}'. Try typing better")


@app.post("/webhook")
async def handle_groupme_webhook(request: Request):
    """
    GroupMe sends POST requests here for every new message in the group.
    Returns 200 quickly to acknowledge (important!).
    """
    try:
        data = await request.json()
        msg = GroupMeMessage(**data)  # Validate with Pydantic
    except Exception as e:
        raise HTTPException(status_code=400, detail="Invalid payload")

    # Ignore messages from bots (including ourselves) to prevent loops
    if msg.sender_type == "bot":
        return {"status": "ignored"}

    # Clean input
    text = (msg.text or "").strip().lower()

    # -----------------------
    # Bot command logic
    # -----------------------
    if text == "!hello":
        send_message(f"Hello, {msg.name}! 👋")
    elif text == "!greet":
        send_message("Hello, everyone 👋! I am a bot, dont call me an LLM😠. Here to help with finding running locations a little easier, show the race schedule, and possibly more to come! Like Devin I'm a little slow😣, so be patient if there's a delay in response(I'm on a free tier)")
    elif text == "!alllocations" or text == "!alllocation":
        output = ''
        for location in LOCATIONS:
            output+= location + ': \n'
            for location_json in LOCATIONS[location]:
                output+= "   →" + location_json['name'] + '\n'
        output += '\n'
        send_message(output)
    elif text == "!shortlist":
        send_message(' | '.join(SHORT_LOCATIONS))
    elif text.startswith("!location"):
        location_id = handle_word_match(text[9:])
        for location in LOCATIONS:
            for location_json in LOCATIONS[location]:
                if location_json['id'] == location_id:
                    send_message(f"I found {location_json['name']}",attachments=[location_json])
    elif text == "!schedule":
        out = 'Date       Event     Distance \n'
        for race in SCHEDULE:
            out+='       '.join(race.values()) + '\n'
        send_message(out)
    elif text == "!help":
        send_message(
            "Available commands:\n"
            "!hello → say hi\n"
            "!location [text] → will try to match to a location in the short list and return lat/long \n"
            "!alllocations → Displays a formatted list of running locations \n"
            "!shortlist → Displays a shorter list of running locations \n"
            "!schedule → Displays the fleet feet race schedule 2026(subject to change) \n"
            "!help → this message"
        )

    # Always return 200 OK quickly
    return {"status": "OK"}



if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=PORT)