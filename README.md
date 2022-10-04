<img align="left" height="200" src="https://user-images.githubusercontent.com/23436953/193432193-4b5573ab-8dc1-4aa5-ba4e-6c52017605ef.png">

# ULBDiscordBot

[![CodeFactor](https://www.codefactor.io/repository/github/bepolytech/ulbdiscordbot/badge)](https://www.codefactor.io/repository/github/bepolytech/ulbdiscordbot)

⚠️ ***WORK IN PROGRESS*** ⚠️

This is a small discord bot written in python using the [disnake library](https://github.com/DisnakeDev/disnake) to make a registration system for ULB servers.

## 📥 Installation

### Install without docker

```bash
git clone https://github.com/bepolytech/ULBDiscordBot.git
cd /ULBdDiscordBot
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### Install with docker

Make sure you have the [Docker Engine installed](https://docs.docker.com/engine/install/).

(Container image available on DockerHub: [bepolytech/ulbdiscordbot](https://hub.docker.com/r/bepolytech/ulbdiscordbot))

```bash
docker pull bepolytech/ulbdiscordbot
```

> #### Or build the image yourself
>
> ```bash
> docker build . -t ulbdiscordbot
> ```

## 🤖 Discord Bot

### Creation

Go to the [discord developper portal](https://discord.com/developers/applications):

Create a new application. Once on the app dashboard, go to `Bot` and click `Add Bot`.

### Settings

⚠️ *Still need to check the exact permissions needed here* ⚠️

On the `Bot` page:

Considere unchecking the `Public Bot` field if you don't want everybody to be able to add the bot to their server.

Check the `Server Members Intent`.

You can also change the bot `user name` and `icon`.

Click on `Reset Token` and save the new generated token for later.

On the `OAuth2` > `URL Generator` > `Scopes`, check the following fields:

* `bot`
* `applications.commands`

![placeholder](/docs/bot_scopes.png)

On the `Bot Permissions` that appeared below, check the following fields:

* `View Audit Log`
* `Manages Roles`
* `Manage Nicknames`
* `Use Slash Commands`

![placeholder](/docs/bot_perms.png)

Copy the `Generated URL` given below, this is the URL to use in your browser to add the bot to your server.

## 🔐 Configuration

Copy the `.env_template` -`.env` to easily see all the parameters that need to be set.

### Discord

* `DISCORD_TOKEN`

The bot token generated above.

* `ADMIN_GUILD_ID`

(Optional) The discord server where to register admin commandes (see below)

* `LOG_CHANNEL`

(Optional) The discord channel ID where the bot will send message when an error occure during a command. It need to have acces to this channel. If not provided, the bot owner DM is used.

* `CONTACT_USER_ID`

(Optional) The user id that users can contact in case of an issu with the registration.

### Email

This bot is writen to send email through gmail account.

* `EMAIL_ADDR`

The email address

* `AUTH_TOKEN`

You need to go to the [google account settings Security](https://myaccount.google.com/security?hl=fr), enable the two-factor authentification then generate an applications password for the email app.

### Google Sheet

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

The google sheet url. It need to be shared to the bot using the email address on `client_email`.

The google sheet itself must have two worksheet with the following name and headers (first line)

* `users`: with headers:

  * `user_id`
  * `name`
  * `email`

* `guilds`: with headers:

  * `guild_id`
  * `role_id`
  * `rename`

## 🏃🏼 Run

### Run without docker

```bash
source .venv/bin/activate
python3 main.py
```

### Run with docker

You can either run with docker directly, or with docker-compose.

#### docker

```bash
docker run -d --env-file=.env bepolytech/ulbdiscordbot
```

#### docker-compose

```bash
docker-compose up -d
```

To see the bot logs when running with docker in detached mode (`-d`), use the [docker logs for the container](https://docs.docker.com/engine/reference/commandline/logs/).

## 💠 Bot usage

### ULB servers

* `/setup`

(Admin permission needed) When adding the bot to a new server, you need to set the @ULB role with the command `/setup`. This commande also allow you to choose if you want to force the registered membre to get rename with real name or not (yes by default).

* `/info`

(Admin permission needed) Get current server information (@ULB role, does rename is enable, and check for permission conflict).

* `/ulb`

Once the ULB role is set, when a new user join the server, either he is already registered (from another of yours server) in which case he will get the `@ULB` role and get rename, or he is not registered yet and will received a DM message with the instruction to register himself using `/ulb` command.

### Admin server

* `/user add`

Manually add an user (don't required email address to be verified)

* `/user info`

Get info about a registered user (discord id, ulb email, name and list of ulb guild that he is on)

* `/user edit`

Edit info of a user.

* `/user delete`

Delete an user.

* `/update`

This force a total update of the database and all the servers. Since the bot already do this automatically at startup and after each reconnection, the only normal usecase for this would be if you manually add an entry (server or user) to the google sheet instead of using the `/user add` command above.

## 👤 Author

Bot made by [OscarVsp](https://github.com/OscarVsp)

## 👥 Contributors

* [Lucas Placentino](https://github.com/LucasPlacentino)

## 🏛 Made originally for the Université libre de Bruxelles student associations

Built for the [Bureau Etudiant de Polytechnique (BEP)](https://bepolytech.be).

<a href="https://ulb.be/en" target="_blank"><img src="https://user-images.githubusercontent.com/23436953/193416825-acafd006-a90b-4c8f-ba73-47a77e38b400.jpg" height="80"></a>

## 📜 License

GNU General Public License v3.0
