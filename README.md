# Groupme fastAPI bot

[Groupme API Docs](https://dev.groupme.com/)

**Description:** This bot was created by me to help our club identify our running locations more quickly within the Albany area. I created a custom data structure to hold the location data and other metadata about each location. The bot will send the lat/long of the location to the groupme assuming the user typed in the location trying to match the shortname of the location list.

**Use case:** The user can access the bot through the groupme chat and ask it for information by using the '!' followed by a keyword referenced in !help. The bot listens to the specific chat and if it detects one of these keywords it will respond with the desired data.

Run command: `uvicorn main:app --reload`

Can manage the bot from the groupme dev api site(the bot name, the specific groupme chat, and API keys for the .env)
