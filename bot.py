# General imports
import os, os.path
import regex

# Google Sheets imports
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# Discord imports
import discord
from dotenv import load_dotenv # Needed to read .env file
load_dotenv()
email_regex = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,7}\b'

# Settings for Discord
TOKEN = os.getenv('DISCORD_TOKEN')
VALIDATED_ROLE_ID = os.getenv('VALIDATED_ROLE_ID')
client = discord.Client()

# Settings for Sheets
SPREADSHEET_ID = os.getenv('SPREADSHEET_ID')
RANGE_NAME = "Members!A:A"

# If modifying these scopes, delete the file token.json.
SCOPES = ['https://www.googleapis.com/auth/spreadsheets.readonly']

# Sheets lookup
async def check_email(email):
    # Authorize Google Sheets API... how will the bot handle authenticating?
    creds = None

    # The file token.json stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists("token.json"):
        creds = Credentials.from_authorized_user_file("token.json", SCOPES)

    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            # Your credentials file comes from Google Cloud Console after you setup an app and hook up OAuth
            # Downloaded secrets file needs to renamed to credentials.json
            flow = InstalledAppFlow.from_client_secrets_file(
                "credentials.json", SCOPES
            )
            creds = flow.run_local_server(port=0)

        # Save the credentials for the next run
        with open("token.json", "w") as token:
            token.write(creds.to_json())
   
    # Call the Sheets API
    try:
        service = build("sheets", "v4", credentials=creds)
        sheet = service.spreadsheets()
        result = (
            sheet.values()
            .get(spreadsheetId=SPREADSHEET_ID, range=RANGE_NAME)
            .execute()
        )

        values = result.get("values", [])
        if not values:
            print("No data found.")
            return

        if email in values:
            return True
        else:
            return False

    except HttpError as err:
        print(err)

async def is_valid_email(email):
    if(regex.fullmatch(email_regex, email)):
        return True
    else:
        return False

# Discord event listeners
@client.event
async def on_member_join(member):    
    await member.create_dm()
    await member.dm_channel.send(
        f'Hi {member.name}, welcome to our DSA chapter''s Discord server!'
    )

    await member.create_dm()
    await member.dm_channel.send(
        """
            Your account currently has limited access to the server.
           
            To gain full access, please reply to this message with the email address you used to become a DSA member.            
        """            
    )

@client.event
async def on_message(message):
    # Make sure the message we're reading didn't come from this bot
    if message.author == client.user:
        return

    # Checks:
    # 1. That message is a valid email address, ignore all other messages
    # 2. That message.channel is the DM channel for the bot and NOT any of the regular server channels.
    # https://discordpy.readthedocs.io/en/latest/api.html#discord.Message
    # https://stackoverflow.com/questions/71362604/if-discord-py-bot-gets-dm
    email_valid = await is_valid_email(message.content)
    if email_valid and isinstance(message.channel, discord.DMChannel):
        validated_member = await check_email(message.content)
        if validated_member:
            # Add member to proper 'validated' role, varies by server            
            author = message.author
            role = await author.guild.get_role(VALIDATED_ROLE_ID)

            # Don't add the same role twice
            if not role in author.roles:                
                await author.add_roles(role)

            await message.channel.send('Membership validated!')
        else:
            await message.channel.send('Sorry, we couldn''t validate your email as a member in good standing. Please DM a member of the Steering Committee for support')

@client.event
async def on_ready():
    print(f'{client.user} has connected to Discord!')

@client.event
async def on_error(event, *args, **kwargs):
    with open('err.log', 'a') as f:
        if event == 'on_message':
            f.write(f'Unhandled message: {args[0]}\n')
        else:
            raise

client.run(TOKEN)