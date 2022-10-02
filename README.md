<img align="left" height="200" src="https://user-images.githubusercontent.com/23436953/193432193-4b5573ab-8dc1-4aa5-ba4e-6c52017605ef.png">

# ULBDiscordBot

[![CodeFactor](https://www.codefactor.io/repository/github/oscarvsp/ulbdiscordbot/badge)](https://www.codefactor.io/repository/github/oscarvsp/ulbdiscordbot)

⚠️ **WORK IN PROGRESS** ⚠️

This is a small discord bot written in python using the [disnake library](https://github.com/DisnakeDev/disnake) to make a registration system for ULB servers.

## 📥 Installation

### Install without docker

```bash
git clone https://github.com/OscarVsp/ULBDiscordBot.git
cd /ULBdDiscordBot
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### Install with docker

TODO : Add docker hub link and cmd

## 🤖 Discord Bot

### Creation

Go to the [discord developper portal](https://discord.com/developers/applications):

Create a new application. Once on the app dashboard, go to `Bot` and click `Add Bot`.

### Settings

On the `Bot` page:

Considere unchecking the `Public Bot` field if you don't want everybody to be able to add the bot to their server.

Check the `Server Members Intent`.

You can also change the bot `user name` and `icon`.

Click on `Reset Token` and save the new generated token for later.

On the `OAuth2` `URL Generator` `Scopes`

Check the following fields:

* `bot`
* `applications.commands`

On the `Bot Permissions` that appeared below

Check the following fields:

* `Manages Roles`
* `Manage Nicknames`
* `Send Messages`
* `Use Slash Commands`

Copy the `Generated URL` given below, this is the URL to use to add the bot to your server

## 🔐 Configuration

Copy the `.env_template` -`.env` to easily see all the parameters that need to be set.

### Discord

* `DISCORD_TOKEN`

The bot token generated above.


* `LOG_CHANNEL`

(Optional) The discord channel ID where the bot will send message when an error occure during a command. It need to have acces to this channel. If not provided, the bot owner DM is used.

* `CONTACT_USER_ID`

(Optional) The user id that users can contact in case of an issu with the registration.

* `GUILD_TEMPLATE_URL`

(Optional) The url of the guild template to automatically detect role (must have a `@ULB` role).

### Email

This bot is writen to send email through gmail account.

* `EMAIL_ADDR`

The email address

* `AUTH_TOKEN`

You need to go to the [google account settings Security](https://myaccount.google.com/security?hl=fr), enable the two-factor authentification then generate an applications password for the email app.

### Google Sheet

Create a Google Sheet, with one sheet named "users" and another sheet named "guilds".

To generate google sheet api credentials, follow [this guide](https://medium.com/@a.marenkov/how-to-get-credentials-for-google-sheets-456b7e88c430). You will get a `.json` file with all the following fields:

* `GS_TYPE` <- `'type'`
* `GS_PROJECT_ID` <- `'project_id'`
* `GS_PRIVATE_KEY_ID` <- `'private_key_id'`
* `GS_PRIVATE_KEY` <- `'private_key'`
* `GS_CLIENT_EMAIL` <- `'client_email'`
* `GS_CLIENT_ID` <- `'client_id'`
* `GS_AUTHOR_URI` <- `'auth_uri'`
* `GS_TOKEN_URI` <- `'token_uri'`
* `GS_AUTH_PROV` <- `'auth_provider_x509_cert_url'`
* `GS_CLIENT_CERT_URL` <- `'client_x509_cert_url'`

The last field is:

* `GOOGLE_SHEET_URL`

The google sheet url. It need to be shared to the bot using the email address on `client_email`

## 🏃🏼 Run

### Run without docker

```bash
source .venv/bin/activate
python3 main.py
```

### Run with docker

```bash
docker run --env-file=.env ulbdiscordbot
```

## 💠 Bot usage

* `/role setup`

When adding the bot to a new server, either the server follow the guild template given, and the role `@ULB` will get automatically set, or you can set it manually with the command `/role setup` (admin permission needed).

* `/email`

Once the ULB role is set, when a new user join the server, either he is already registered (from another of yours server) in which case he will get the `@ULB` role and get rename, or he is not registered yet and will received a DM message with the instruction to register himself using `/email` command.

* `/role update`

At any point, you can run `/role update` (admin permission needed) to check all the member of the server and add `@ULB` role and rename if the member is registered (usefull when adding the bot to a server that already contains registered users, or if you have manually added an user to the google sheet). ⚠️ That won't affect users that are not registered, so you can still add manually the `@ULB` role to someone to give him acces to only this server.

## 👤 Author

Bot made by [OscarVsp](https://github.com/OscarVsp)

## 👥 Contributors

* [Lucas Placentino](https://github.com/LucasPlacentino)

## 🏛 Made originally for the Université libre de Bruxelles student associations

Built for the [Bureau Etudiant de Polytechnique (BEP)](https://bepolytech.be).  

<a href="https://ulb.be/en" target="_blank"><img src="https://user-images.githubusercontent.com/23436953/193416825-acafd006-a90b-4c8f-ba73-47a77e38b400.jpg" height="80"></a>

## 📜 License

TODO
