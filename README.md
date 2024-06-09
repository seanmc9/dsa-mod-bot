# Discord Moderation Bot Template

To connect this bot to your Discord server with the necessary permissions, you'll have to have 
1. Created an application on Discord
2. Categorized it as a bot
3. Gone to this URL to authorize your bot on the server(s) you want it: `https://discord.com/oauth2/authorize?client_id=<BOT_CLIENT_ID>&permissions=<PERMISSIONS>&integration_type=0&scope=bot` where
   - BOT_CLIENT_ID is also referred to as a bot's Application ID by Discord
   - PERMISSIONS is an integer that can be determined at the bottom of this page https://discord.com/developers/applications/YOUR_APPLICATION_ID_HERE/bot

## Requirements
Rename `.example.env` to `.env` and fill it in wither your Discord Bot Token you'd like to add the bot to. 

## To Run Locally
Before running the bot you will need to install all the requirements with this command:

```
python3 -m pip install -r requirements.txt
```

After that you can start it with

```
python3 bot.py
```

## To Run on an Open Ocean Ubuntu 24.04 (LTS) x64 OS from scratch

The last command in here will start the bot in the background so that the bot doesn't stop when you close your terminal, you can see it by running `ps` and looking for the line that says `python`.
```
apt install python3-pip
apt install python3.12-venv
mkdir ~/.virtualenvs
python3 -m venv ~/.virtualenvs/botenv
source ~/.virtualenvs/botenv/bin/activate
pip install -r requirements.txt
nohup python3 bot.py &
```