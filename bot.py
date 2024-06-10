# General imports
import os, base64, regex, uuid

# Google Sheets imports
import google.auth
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from email.message import EmailMessage
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# Discord imports
import discord

# Load .env vars
from dotenv import load_dotenv # Needed to read .env file
load_dotenv()

# Settings for Discord
TOKEN = os.getenv('DISCORD_TOKEN')
VALIDATED_ROLE_ID = os.getenv('VALIDATED_ROLE_ID')
intents = discord.Intents.default()
intents.members = True
client = discord.Client(intents=intents)

# Settings for Sheets
SPREADSHEET_ID = os.getenv('SPREADSHEET_ID')
RANGE_NAME = "Members!A:A"
email_regex = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,7}\b'

# Settings for validation code email
SENDING_EMAIL = os.getenv('SENDING_EMAIL')
email_to_sent_code = {}
author_id_to_claimed_email = {}

# If modifying these scopes, delete the file token.json.
SCOPES = ['https://www.googleapis.com/auth/spreadsheets.readonly', 'https://www.googleapis.com/auth/gmail.send']

async def send_verification_code_email(email_to_validate: str, validation_code_to_send: str):
  """Create and send an email message
  Print the returned  message id
  Returns: Message object, including message id

  Load pre-authorized user credentials from the environment.
  TODO(developer) - See https://developers.google.com/identity
  for guides on implementing OAuth2 for the application.
  """
  if os.path.exists("token.json"):
    creds = Credentials.from_authorized_user_file("token.json", SCOPES)

  try:
    service = build("gmail", "v1", credentials=creds)
    message = EmailMessage()

    message.set_content(validation_code_to_send)

    message["To"] = email_to_validate
    message["From"] = SENDING_EMAIL
    message["Subject"] = "DSA Discord Bot Validation Code"

    # encoded message
    encoded_message = base64.urlsafe_b64encode(message.as_bytes()).decode()

    create_message = {"raw": encoded_message}
    # pylint: disable=E1101
    send_message = (
        service.users()
        .messages()
        .send(userId="me", body=create_message)
        .execute()
    )
    print(f'Message Id: {send_message["id"]}')
  except HttpError as error:
    print(f"An error occurred: {error}")
    send_message = None
  return send_message

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

        if [email] in values:
            return True
        else:
            return False

    except HttpError as err:
        print(err)

async def generate_validation_code():
    return str(uuid.uuid4())

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

    if isinstance(message.channel, discord.DMChannel):
        email_valid = await is_valid_email(message.content)
        if email_valid: # if the message is a valid regex email
            validated_member = await check_email(message.content) # check that email is in Google Sheet
            if validated_member:
                author_id_to_claimed_email[message.author.id] = message.content
                code = await generate_validation_code()
                email_to_sent_code[message.content] = code # store the author id in a dict with the email they're claiming
                validation_code_email = await send_verification_code_email(message.content, code) # send a confirmation code via email to the validating email
                if validation_code_email:
                    await message.channel.send('Validation code sent! Please respond here with the code you were sent.')
            else:
                await message.channel.send('Sorry, we couldn\'t validate your email as a member in good standing. Please DM a member of the Steering Committee for support')
        else: # if the message is a validation code
            author = message.author
            # verify that it is the correct code for the email that the message author is claiming
            if message.content == email_to_sent_code[author_id_to_claimed_email[author.id]]:
                # TODO: be able to determine which guild to get the role from and add to
                role = client.get_guild(1249516111125282846).get_role(int(VALIDATED_ROLE_ID))

                # Don't add the same role twice
                if not role in client.get_guild(1249516111125282846).get_member(author.id).roles:
                    await client.get_guild(1249516111125282846).get_member(author.id).add_roles(role)

                await message.channel.send('Membership validated!')
            else:
                await message.channel.send('That code is not correct, please try again or DM a member of the Steering Comittee for support.')

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