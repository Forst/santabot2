# Santabot2 – a Secret Santa bot for Discord

This bot allows to conduct Secret Santa events in Discord guilds! It is specifically optimized for digital presents, such as game codes, gift cards etc., which the bot can send anonymously via direct messages.

**Key features:**

* Perfect for **digital** presents (ex. game codes, gift cards) or any other textual gifts.
* **Anonymous:** no postal addresses or e-mails required, gifts are sent via Discord direct messages.
* **Personal:** users can specify their wishes (preferred gaming platform or game genre, for example).

*This is a complete rewrite of the older [Santabot](https://github.com/Forst/santabot): the idea remained the same, but no code was reused.*


## Configuration

Copy the `config.example.py` configuration file to `config.py` in the same directory and edit the resulting file in your favourite editor.

The only **required** change is the Discord token (`DISCORD_TOKEN`), which you have to obtain yourself through the [Discord Developer Portal](https://discordapp.com/developers/applications/).

**Required bot permissions:**

* Read Text Channels & See Voice Channels (to receive commands)
* Send Messages (to reply to commands)
* Manage Messages (to delete `wish` and `gift` commands for secrecy reasons)

In this configuration file you can also change the **command prefix** (for example if it conflicts with another bot in your server, default is `s!`) or the **back-end database** (SQLite is used by default, which is only acceptable when used in a few small guilds).


## Installation

Make sure you've **configured** your bot first! See the section above.

### Docker Compose (recommended)

**Prerequisites:**

* Docker Engine >= 1.13.0 (tested on 18.09.7)
* Docker Compose >= 1.10.0 (tested on 1.24.0)

**Step 1.** Run Docker Composer:

```
$ docker-compose up
```

That's it! It will automatically build a `santabot2:latest` image, spin up a new container and pass through the configuration file you created as a volume.

### Manual installation

**Prerequisites:**

* Python >= 3.5.3 (tested on 3.7.3) with pip and virtual environment support


**Step 1.** Set up a virtual environment:

```
$ python3 -m venv venv
$ ./venv/bin/pip3 install -r requirements.txt
```

**Step 2.** Run the bot:

```
$ ./venv/bin/python3 santabot2.py
```

To stop the bot, press Ctrl+C. It may take up to 10 seconds to stop gracefully.


## Usage

For more information and extra commands refer to the `s!help` command. Note that help contents depend on the user running the command and current status of the Secret Santa event.

### How-to for users

1. To **join** the event, type:

    ```
    s!join
    ```

2. To submit your **wish**, type:

    ```
    s!wish I would like a big penguin plushie, please!
    ```

3. To submit the **gift** for your secret recipient, type:

    ```
    s!gift Your redeem code for 5 candies on SuperGameStore is XXXXX-XXXXX-XXXXX
    ```

### How-to for moderators

1. To **start** the event (with an optional comment), type:

    ```
    s!start Budget is 10 candies
    ```

2. To **assign** everyone their secret recipients, type:

    ```
    s!assign
    ```

3. To **distribute** everyone their gifts, type:

    ```
    s!distribute
    ```


## Acknowledgements

* [discord.py](https://github.com/Rapptz/discord.py): an API wrapper for Discord written in Python.
* [Pony ORM](https://ponyorm.org): a Python Object-Relational Mapper with beautiful query syntax
* [Discord](https://discordapp.com), hosting the [Community Hack Week](https://blog.discordapp.com/discord-community-hack-week-build-and-create-alongside-us-6b2a7b7bba33) 🎉

---

*Created for Discord Community Hack Week 2019 by Forst#8128*

![Discord Hack Week 2019](https://github.com/Forst/santabot2/raw/master/.readme/hack_badge_black.png)
