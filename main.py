import requests
from web import run, app
from io import StringIO
from html.parser import HTMLParser
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from threading import Thread
import database
import secrets
import string
import json
import os
import dns
import re
from tldextract import extract
from constants import domains, sudoers, reserved_keyword
from pyrogram.enums import MessageEntityType
from pyrogram.errors import UserNotParticipant, UserIsBlocked
import pyromod.listen
from pyromod.helpers import ikb
from flask import Flask, request, Response, send_file
import json
import requests
import re
import database
import time
import pymongo

ostrich = Client("ot",
                 bot_token="bot-token",
                 api_id=111111,
                 api_hash="api_hash")


class MLStripper(HTMLParser):

    def __init__(self):
        super().__init__()
        self.reset()
        self.strict = False
        self.convert_charrefs = True
        self.text = StringIO()

    def handle_data(self, d):
        self.text.write(d)

    def get_data(self):
        return self.text.getvalue()


def strip_tags(html):
    s = MLStripper()
    s.feed(html)
    return s.get_data()


async def send_mail(sender, client, message):
    domain = sender.split("@")[1]
    if domain.lower() not in domains:
        await ostrich.send_message(
            message.chat.id,
            f"**The domain {domain} is not maintained by us.\nUse /domains to check list of available domains.\n\nIf you are the owner of {domain[1]} and interested to use it in this bot, contact us at @ostrichdiscussion.**"
        )
        return
    userid = message.chat.id
    to = await client.ask(userid, '**Send me recipient mail**')

    mail = []
    for entity in to.text.entities:
        if entity.type == MessageEntityType.EMAIL:
            o = entity.offset
            l = entity.length
            mail.append(to.text[o:o + l])

    if len(mail) == 0:
        await ostrich.send_message(
            message.chat.id,
            f"**Please provide a valid mail./nUse /send to redo this task.**")
        return
    limits = database.get_limits(message.chat.id)
    at_once = limits["limits"]["send"]["at_once"]
    if len(mail) > at_once:
        await ostrich.send_message(
            message.chat.id,
            f"**You cannot send mail to more than {at_once} users at once. Upgrade your account to remove limitations.**"
        )
        return

    subject = await client.ask(userid, "Provide mail subject")
    body = await client.ask(userid, "Send any text to send.")
    print(body.text)

    api = f"https://api.mailgun.net/v3/{domain}/messages"
    token = "mailgun token"
    #if domain == "cognant.tech" or domain:
    # api =
    #f"https://api.eu.mailgun.net/v3/{domain}/messages"
    #''
    # token = ""
    r = requests.post(api,
                      auth=("api", token),
                      data={
                          "from": sender,
                          "to": mail,
                          "subject": subject.text,
                          "text": body.text
                      })
    print(r.text)
    await ostrich.send_message(
        message.chat.id,
        f"**Mail queued successfully.**",
        reply_markup=InlineKeyboardMarkup([[
            InlineKeyboardButton("Get Help",
                                 url="https://telegram.dog/ostrichdiscussion"),
        ]]))
    database.statial("sent", 1)


@ostrich.on_message(filters.command(["blocks"]))
async def blocks(client, message):
    blocks = database.get_blocked(message.chat.id)
    domains = "- **Domains:**\n"
    mails = "- **Mails:**\n"
    regex = "- **Regex:**\n"

    for i in blocks["domains"]:
        domains = domains + f"     - {i}\n"
    for i in blocks["mails"]:
        mails = mails + f"     - {i}\n"
    for i in blocks["regex"]:
        regex = regex + f"     - {i}\n"

    if len(blocks['domains']) == 0:
        domains = domains + f"     - None"
    if len(blocks['mails']) == 0:
        mails = mails + f"     - None"
    if len(blocks['regex']) == 0:
        regex = regex + f"     - None"

    text = f'''
**Your blocklist:**

{domains}
{mails}
{regex}
__Use /unblock to stop blocking mails here.__
'''
    await message.reply_text(text, disable_web_page_preview=True)


@ostrich.on_message(filters.command(["block"]))
async def block_mail(client, message):

    await message.reply_text(
        "**Select an option:**",
        reply_markup=InlineKeyboardMarkup([[
            InlineKeyboardButton("mail", callback_data="block_mails"),
            InlineKeyboardButton("domain", callback_data="block_domains"),
        ], [InlineKeyboardButton("regex", callback_data="block_regex")]]),
        disable_web_page_preview=True)


@ostrich.on_message(filters.command(["stats"]))
async def stats(client, message):
    stat = database.get_statial()

    text = f'''**
Mailable Bot - STATS:

User : {stat['users']}
Mails : {stat['mails']}
Sent : {stat['sent']}
Received : {stat['received']}**
    '''
    await message.reply_text(text)


@ostrich.on_message(filters.command(["transfer"]))
async def transfer(client, message):
    user = message.from_user.id
    mails = database.mails(user)

    if len(mails) != 0:
        buttons = []

        for mail in mails:
            buttons.append([InlineKeyboardButton(mail, f"transfer_{mail}")])
        await message.reply_text(text="**Select a mail:**",
                                 reply_markup=InlineKeyboardMarkup(buttons),
                                 reply_to_message_id=message.id)
    else:
        await message.reply_text(
            text=
            "**You don't own any mail.\nUse /generate to get a new domain.**")


@ostrich.on_message(filters.command(["unblock"]))
async def unblock_mail(client, message):

    await message.reply_text(
        "**Select an option:**",
        reply_markup=InlineKeyboardMarkup([[
            InlineKeyboardButton("mail", callback_data="unblock_mails"),
            InlineKeyboardButton("domain", callback_data="unblock_domains"),
        ], [InlineKeyboardButton("regex", callback_data="unblock_regex")]]),
        disable_web_page_preview=True)


@ostrich.on_message(filters.command(["start"]))
async def start(client, message):

    await message.reply_text(
        text=f"**Hello {message.from_user.mention} 👋 !\n\n"
        "I am mail bot. I can forward all your mails here.\n\nHit help to know more on using me.**",
        disable_web_page_preview=True,
        reply_markup=InlineKeyboardMarkup([[
            InlineKeyboardButton("HELP", callback_data="getHelp"),
            InlineKeyboardButton("Privacy Policy", callback_data="prp"),
        ]]),
        reply_to_message_id=message.id)
    database.scrape(message)


@ostrich.on_message(filters.command(["user"]))
async def user(client, message):
    split = message.text.split(" ")
    user = None

    if len(split) > 1:
        id = split[1]
        user = database.user_info(id)
    if message.reply_to_message:
        if message.reply_to_message.forward_from:
            user = database.user_info(
                str(message.reply_to_message.forward_from.id))
    if not user:
        await message.reply_text("**No user found!**")
        return
    text = f'''
**User:** {user['firstname']}  {user['lastname']}
**Username:** @{user['username']}
**DC:** `{user['dc']}`
**Plan:** `{user['plan']['type']}`
**Mails:** `{user['mails']}`
**First seen:** `{user['firstseen']}`

'''

    await message.reply_text(text)


@ostrich.on_message(filters.command(["whoo"]))
async def whoo(client, message):
    split = message.text.split(" ")
    user = database.find_user(split[1])

    await message.reply_text(f'''
Mail {split[1]} belongs to {user}
    ''')


@ostrich.on_message(filters.command(["domains"]))
async def list_domains(client, message):
    text = '''
**List of available domains:**    
  - themails.ml
  - mailablebot.tk
 
  - aquaseven.me [17 JUL 2023]
  - crimpton.website [11 DEC 2023]
  - digitalworm.tech [12 JUL 2023]
  - swiggie.space [2 JUL 2023]
  - treehub.live [26 JUL 2023]
  - user.mailable.me [26 OCT 2023]
'''
    await message.reply_text(text)


@ostrich.on_message(filters.command(["sponsors"]))
async def sponsors(client, message):
    text = '''
**Our sponsor list:**
  >> [Ž€ ₣ΔŁĆØŇ](https://t.me/Ze_Falcon)
        - hmm.nyc
        - seemsgood.us

__Help us by sponsoring a domain or [buy us a cup of tea](https://ko-fi.com/rabbitfored/) and become one of the premium members.__
'''
    await message.reply_text(text, disable_web_page_preview=True)


@ostrich.on_message(filters.command(["help"]))
async def assist(client, message):
    text = '''
**Here is an detailed guide on using me.**

**Available Commands:**
/start : Check if I am alive!
/help : Send you this text

/generate : generates a random mail
/set <mail> : Set mail to your
   Eg: `/set foo@cometdown.me`

/send : Send a mail

/mails  : List your mails
/delete : Release a mail id
/transfer: Tranfers a mail

/block : Block a mail
/unblock : Unblock a mail
/blocks : Check your current blocklist

/domains : List of available domain
/sponsors : Check our sponsors
/about : About me
/donate : Donate us.
'''
    await message.reply_text(text,
                             reply_markup=InlineKeyboardMarkup([
                                 [
                                     InlineKeyboardButton(
                                         "Get Help",
                                         url="t.me/ostrichdiscussion"),
                                 ],
                             ]))


@ostrich.on_message(filters.command(["about"]))
async def aboutTheBot(client, message):
    """Log Errors caused by Updates."""

    keyboard = [
        [
            InlineKeyboardButton("➰Channel", url="t.me/theostrich"),
            InlineKeyboardButton("👥Support Group",
                                 url="t.me/ostrichdiscussion"),
        ],
    ]

    reply_markup = InlineKeyboardMarkup(keyboard)

    await message.reply_text(
        "<b>Hello! I am MailableBot.</b>"
        "\nI make temp mas for you."
        "\n\n<b>About Me :</b>"
        "\n\n  - <b>Name</b>        : Mailable"
        "\n\n  - <b>Creator</b>      : @theostrich"
        "\n\n  - <b>Language</b>  : Python 3"
        "\n\n  - <b>Library</b>       : <a href=\"https://docs.pyrogram.org/\">Pyrogram</a>"
        "\n\nIf you enjoy using me and want to help me survive, do donate with the /donate command - my creator will be very grateful! Doesn't have to be much - every little helps! Thanks for reading :)",
        reply_markup=reply_markup,
        disable_web_page_preview=True)


@ostrich.on_message(filters.command(["donate"]))
async def donate(client, message):
    keyboard = [
        [
            InlineKeyboardButton("Contribute",
                                 url="https://github.com/theostrich"),
            InlineKeyboardButton("Paypal Us",
                                 url="https://paypal.me/donateostrich"),
        ],
    ]

    reply_markup = InlineKeyboardMarkup(keyboard)
    await message.reply_text(
        "Thank you for your wish to contribute. I hope you enjoyed using our services. Make a small donation/contribute to let this project alive.",
        reply_markup=reply_markup)


@ostrich.on_message(filters.command(["send"]))
async def send(client, message):
    user = message.chat.id
    mails = database.mails(user)

    if len(mails) != 0:
        buttons = []

        for mail in mails:
            buttons.append([InlineKeyboardButton(mail, f"send_{mail}")])
        await message.reply_text(text="**Select a mail:**",
                                 reply_markup=InlineKeyboardMarkup(buttons))
    else:
        await message.reply_text(
            text=
            "**You don't own any mail.\nUse /generate to get a new domain.**")


@ostrich.on_message(filters.command(["mails"]))
async def mails(client, message):
    user = message.from_user.id
    mails = database.mails(user)

    if len(mails) != 0:
        buttons = []

        for mail in mails:
            buttons.append([InlineKeyboardButton(mail, f"info_{mail}")])
        await message.reply_text(text="**Select a mail:**",
                                 reply_markup=InlineKeyboardMarkup(buttons),
                                 reply_to_message_id=message.id)
    else:
        await message.reply_text(
            text=
            "**You don't own any mail.\nUse /generate to get a new domain.**")


@ostrich.on_message(filters.command(["delete"]))
async def delete(client, message):
    user = message.from_user.id
    mails = database.mails(user)
    if len(mails) != 0:
        buttons = []

        for mail in mails:
            buttons.append([InlineKeyboardButton(mail, f"delete_{mail}")])
        await message.reply_text(text="**Select a mail:**",
                                 reply_markup=InlineKeyboardMarkup(buttons))
    else:
        await message.reply_text(
            text=
            "**You don't own any mail.\nUse /generate to get a new domain.**")


@ostrich.on_message(filters.command(["set"]))
async def set_mail(client, message):
    mail = None

    for entity in message.entities:
        if entity.type == MessageEntityType.EMAIL:
            o = entity.offset
            l = entity.length
            mail = message.text[o:o + l]
    if mail == None:
        await message.reply_text(text="**Provide a valid mail ID.**")
        return

    domain = mail.split("@")

    if domain[0].lower() in reserved_keyword:
        await ostrich.send_message(message.chat.id,
                                   f"**Sorry this mail ID is unavailable**")
        return

    limits = database.get_limits(message.chat.id)
    member_mail_limit = limits["limits"]["mails"]["member"]
    non_member_mail_limit = limits["limits"]["mails"]["non_member"]
    mails = database.mails(message.from_user.id)

    if domain[1].lower() not in domains:
        await ostrich.send_message(
            message.chat.id,
            f"**The domain {domain[1]} is not maintained by us.\nUse /domains to check list of available domains.\n\nIf you are the owner of {domain[1]} and interested to use it in this bot, contact us at @ostrichdiscussion.**"
        )
        return
    if message.from_user.id in sudoers:
        text = database.add_mail(message.chat.id, mail)
        if text == "exist":
            await ostrich.send_message(message.chat.id,
                                       f"Sorry this mail ID is unavailable")
            return
        await ostrich.send_message(
            message.chat.id,
            f"**Mail Created successfully.\nYour mail id : {mail}\nNow You can access your mails here.**"
        )
        return
    if len(mails) == 0:
        text = database.add_mail(message.chat.id, mail)
        if text == "exist":
            await ostrich.send_message(
                message.chat.id, f"**Sorry this mail ID is unavailable**")
            return
        await ostrich.send_message(
            message.chat.id,
            f"**Mail Created successfully.\nYour mail id : {mail}\nNow You can access your mails here.**"
        )
    elif len(mails) > 0:
        if len(mails) < member_mail_limit:
            try:
                user_exist = await client.get_chat_member(
                    'theostrich', message.from_user.id)
                text = database.add_mail(message.chat.id, mail)
                if text == "exist":
                    await ostrich.send_message(
                        message.chat.id, f"Sorry this mail ID is unavailable")
                    return
                await ostrich.send_message(
                    message.chat.id,
                    f"Mail Created successfully.\nYour mail id : {mail}\nNow You can access your mails here."
                )
            except UserNotParticipant:
                await message.reply_text(
                    text=
                    f"**Due to limited resource, making mails more than {non_member_mail_limit} require channel membership.**",
                    reply_markup=InlineKeyboardMarkup([[
                        InlineKeyboardButton(text="Join theostrich",
                                             url=f"https://t.me/theostrich")
                    ]]))
        else:
            await ostrich.send_message(
                message.chat.id,
                f"Free users can make {member_mail_limit} mails only.\nSwitch to premium plan or delete any mail using /delete."
            )


@ostrich.on_message(filters.command(["me"]))
async def user_info(client, message):
    limits = database.get_limits(message.from_user.id)
    plan = limits["type"]
    member_mail_limit = limits["limits"]["mails"]["member"]
    non_member_mail_limit = limits["limits"]["mails"]["non_member"]
    at_once = limits["limits"]["send"]["at_once"]
    text = f'''```User : {message.from_user.mention}
Plan : {plan}
Limits:
  • Mails:
       - member  : {member_mail_limit}
       - !member : {non_member_mail_limit}
  • Send : 
       - at_once : {at_once}
```
   '''
    await message.reply_text(text)


@ostrich.on_message(filters.command(["generate"]))
async def generate(client, message):
    buttons = []
    for domain in domains:
        buttons.append([InlineKeyboardButton(domain, f"new_{domain}")])

    await message.reply_text(text=f"**Select a domain:**",
                             disable_web_page_preview=True,
                             reply_markup=InlineKeyboardMarkup(buttons),
                             reply_to_message_id=message.id)


@ostrich.on_callback_query()
async def cb_handler(client, query):

    if query.data.startswith('new'):

        await query.answer()
        await query.message.delete()
        alphabet = string.ascii_letters + string.digits
        user = ''.join(secrets.choice(alphabet) for i in range(8))
        mails = database.mails(query.message.chat.id)

        limits = database.get_limits(query.message.chat.id)
        member_mail_limit = limits["limits"]["mails"]["member"]
        non_member_mail_limit = limits["limits"]["mails"]["non_member"]

        if query.message.chat.id in sudoers:
            cb = query.data.split("_")
            domain = cb[1]
            mail = user + "@" + domain
            text = database.add_mail(query.message.chat.id, mail)
            await query.message.reply_text(
                f"Mail Created successfully.\nYour mail id : {mail}\nNow You can access your mails here."
            )
            return
        if len(mails) < 2:
            cb = query.data.split("_")
            domain = cb[1]
            mail = user + "@" + domain
            text = database.add_mail(query.message.chat.id, mail)
            await ostrich.send_message(
                query.message.chat.id,
                f"Mail Created successfully.\nYour mail id : {mail}\nNow You can access your mails here."
            )
        elif len(mails) > 1:
            if len(mails) < member_mail_limit:
                try:
                    user_exist = await client.get_chat_member(
                        'theostrich', query.message.chat.id)
                    cb = query.data.split("_")
                    domain = cb[1]

                    mail = user + "@" + domain
                    text = database.add_mail(query.message.chat.id, mail)
                    await ostrich.send_message(
                        query.message.chat.id,
                        f"Mail Created successfully.\nYour mail id : {mail}\nNow You can access your mails here."
                    )

                except UserNotParticipant:
                    await query.message.reply_text(
                        text=
                        f"**Due to limited resource, making mails more than {non_member_mail_limit} requires channel membership.**",
                        reply_markup=InlineKeyboardMarkup([[
                            InlineKeyboardButton(
                                text="Join theostrich",
                                url=f"https://t.me/theostrich")
                        ]]))
            else:
                await ostrich.send_message(
                    query.message.chat.id,
                    f"**Your plan includes reserving {member_mail_limit} mails only.\nSwitch to premium plan or delete any mail using /delete to make more mails.**"
                )
    elif query.data == 'close':
        await query.message.delete()
    elif query.data == 'del':
        id = query.message.reply_markup.inline_keyboard[0][0].url.split(
            "/")[-1]
        print(id)

        await client.send_message(
            query.message.chat.id,
            "**Are you sure?**",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("YES", callback_data=f"yes_{id}"),
            ], [
                InlineKeyboardButton("NO", callback_data=f"nope"),
            ]]))
    elif query.data.startswith("yes"):
        key = query.data.split("_")[1]

        requests.get(f"https://paste.theostrich.eu.org/api/delete/aio/{key}")
        await query.answer("Mail deleted successfully")
        await query.message.delete()

    elif query.data == "nope":

        await query.message.delete()
    elif query.data.startswith('delete'):
        await query.answer()
        mail = query.data[7:]
        database.delete_mail(query.message.chat.id, mail)
        await query.message.edit_text("**Mail deleted successfully**")
    elif query.data.startswith('send'):
        await query.answer()
        sender = query.data[5:]
        await send_mail(sender, client, query.message)

    elif query.data == "getHelp":
        await query.answer()
        await assist(client, query.message)
        await query.message.delete()

    elif query.data == "prp":
        await query.answer()
        prp = '''
**Privacy Policy:**

We are committed to protecting and respecting your privacy.
It is our overriding policy to collect as little user information as possible when using the Service.

This Privacy Policy explains (i) what information we collect through your access and use of our Service, (ii) the use we make of such information

By using this Service, you agree to the terms outlined in this Privacy Policy.

**Data we collect and why we collect it:**

- **Account creation:**
     Data like your telegram username, user id, date of creation are collected at the time of account creation (starting the bot).
This information is necessary to provide the service and support.

- **Mail content:**
    All mail contents are stored temporarily to provide web view access to the users.

**Note:** _These mails will never be accessed by us (or) some others unless you share the access link. It is your sole responsibility to protect the access links shared by bot._

**Changes to our Privacy Policy**

We reserve the right to periodically review and change this Policy and will notify users who have enabled the notification preference about any change. Continued use of the Service will be deemed as acceptance of such changes.

**We may stop this service at any time without prior notice.**

        '''
        await query.message.edit(text=prp)

    elif query.data.startswith('block'):
        await query.answer()
        option = query.data[6:]
        await block(client, query.message, option)
    elif query.data.startswith("transfer"):
        mail = query.data.split("_")[1]
        await transfer_mail(client, query.message, mail)
    elif query.data.startswith('unblock'):
        await query.answer()
        option = query.data[8:]
        await unblock(client, query.message, option)
    elif query.data.startswith('info'):
        mail = query.data[5:]
        text = f'''**
Mail  : {mail}
Owner : {query.message.reply_to_message.from_user.mention()}
**'''
        await query.message.edit_text(text)


async def transfer_mail(client, message, mail):
    recipient = await client.ask(message.chat.id,
                                 "**Please enter new owners username**")
    args = recipient.text.split(" ")
    if not args[0].startswith("@"):
        await client.send_message(
            message.chat.id,
            "**Provide a valid Username. Use /transfer to restart this process**"
        )
        return
    try:
        await client.send_message(
            args[0],
            f"**Incoming mail transfer request for {mail} by {message.reply_to_message.from_user.mention()}**"
        )
    except:
        await message.reply_text(
            f"**Cannot transfer {mail} to {args[0]}.\nBe sure that the user started me.**"
        )
        return
    mails = database.mails(args[0])

    limits = database.get_limits(args[0])
    member_mail_limit = limits["limits"]["mails"]["member"]

    if len(mails) > member_mail_limit:
        await message.reply_text(
            f"**Cannot transfer {mail} to {args[0]}.\nThis user had exhausted free mail limits.**"
        )
        return

    database.delete_mail(message.chat.id, mail)
    database.add_mail(args[0], mail)

    await client.send_message(
        args[0], f'''
**New mail transferred to your account.

`Mail `: {mail}
`Transferred by :` {message.reply_to_message.from_user.mention()}

Check your mails using /mails command.**''')
    await message.reply_text(
        f"**Successfully transferred {mail} to {recipient.text}")


async def block(client, message, option):

    trigger = []
    if option == "mails":
        value = await client.ask(
            message.chat.id,
            "**Provide a mail to block:\nEx:** ```ostrich@spammer.com```")
        for entity in value.text.entities:
            if entity.type == MessageEntityType.EMAIL:
                o = entity.offset
                l = entity.length
                trigger.append(value.text[o:o + l])

        text = f"**Blocked successfully.\nNow you won't receive mails from {trigger}**"

    if option == "domains":
        value = await client.ask(
            message.chat.id,
            "**Provide a domain to block:\nEx:** ```spammer.com```")
        for entity in value.text.entities:
            if entity.type == MessageEntityType.URL:
                o = entity.offset
                l = entity.length
                url = value.text[o:o + l]
                tsd, td, tsu = extract(url)
                domain = td + '.' + tsu
                if tsd:
                    domain = tsd + '.' + td + '.' + tsu
                trigger.append(domain)
        text = f"**Blocked successfully.\nNow you won't receive mails from {trigger}**"

    if option == "regex":
        value = await client.ask(
            message.chat.id,
            "**Provide a regex to block its matches:\nEx:** ```(.*)@spammer.com```"
        )
        pattern = value.text
        try:
            re.compile(pattern)
            trigger.append(pattern)
        except re.error:
            print(f"invalid regex - {message.from_user.first_name}")
        text = f"**Blocked successfully.\nNow you won't receive mails matching {trigger}**"

    if len(trigger) == 0:
        await message.reply_text(
            f"**No valid {option} provided.\nUse /block to restart this process**"
        )
        return

    database.block(message.chat.id, option, trigger)
    await value.reply_text(text)


def strip_script_tags(page_source: str) -> str:
    pattern = re.compile(r'\s?on\w+="[^"]+"\s?')
    result = re.sub(pattern, "", page_source)
    pattern2 = re.compile(r'<script[\s\S]+?/script>')
    result = re.sub(pattern2, "", result)
    return result


async def unblock(client, message, option):

    trigger = []
    if option == "mails":
        value = await client.ask(
            message.chat.id,
            "**Provide a mail to unblock:\nEx:** ```ostrich@notaspammer.com```"
        )
        for entity in value.text.entities:
            if entity.type == MessageEntityType.EMAIL:
                o = entity.offset
                l = entity.length
                trigger.append(value.text[o:o + l])
    if option == "domains":
        value = await client.ask(
            message.chat.id,
            "**Provide a domain to unblock:\nEx:** ```notaspammer.com```")
        for entity in value.text.entities:
            if entity.type == MessageEntityType.URL:
                o = entity.offset
                l = entity.length
                url = value.text[o:o + l]
                tsd, td, tsu = extract(url)
                domain = td + '.' + tsu
                if tsd:
                    domain = tsd + '.' + td + '.' + tsu
                trigger.append(domain)
    if option == "regex":
        value = await client.ask(
            message.chat.id,
            "**Provide a regex to unblock its matches:\nEx:** ```(.*)@notaspammer.com```"
        )
        pattern = value.text
        try:
            re.compile(pattern)
            trigger.append(pattern)
        except re.error:
            print(f"invalid regex - {message.from_user.first_name}")

    if len(trigger) == 0:
        await message.reply_text(
            f"**No valid {option} provided.\nUse /unblock to restart this process**"
        )
        return

    database.unblock(message.chat.id, option, trigger)
    await message.reply_text(f"**Unblocked successfully**")


@app.route('/secretm/<id>')
def secretm(id):
    m = ostrich.get_messages(-1001816373321, id)
    f = m.download()
    return send_file(f)


@app.route('/secretmessages', methods=['POST'])
def secretmessages():
    data = request.get_json()
    #f = open("inbox.html", "w")
    #f.write(bytes(str(data["html"])))
    #f.close()    #os.remove("inbox.html")

    #print (m.id)

    headers = {"Content-Type": "application/json"}
    d = {
        "Title": str(data["subject"]),
        "Author": "Penker",
        "Content": str(data["html"][0][:65532])
    }
    # this paste bin service may not be available in future, so it is recommended to use some alternative service.
    req = requests.post("https://paste.theostrich.eu.org/api/documents",
                        data=json.dumps(d),
                        headers=headers)
    res = json.loads(req.text)
    #print(res)
    key = res['result']['key']
    #print(key)
    text = f"\
**Sender     :** {data['from']}\n\
**Recipient  :** {data['to']}\n\
**Subject    :** {data['subject']}\n\
**Content    :** [Raw](https://paste.theostrich.eu.org/{key})\n\n\
**Message    :** {str(data['text'][0][:200])}\n...\
"

    ostrich.send_message(
        1520625615,
        text,
        disable_web_page_preview=True,
        reply_markup=InlineKeyboardMarkup([[
            InlineKeyboardButton("View mail",
                                 url=f"https://inbox.mailable.me/{key}"),
        ], [
            InlineKeyboardButton("Delete", callback_data=f"del"),
        ]]))

    return Response(status=200)


@app.route('/messages', methods=['POST'])
def foo():

    sender = request.form.get('sender')
    print(sender)
    recipient = request.form.get('recipient')
    database.statial("received", 1)

    user = database.find_user(recipient)

    subject = request.form.get('subject', '@penkerBot')
    subject = subject[:55]

    body_html = request.form.get('body-html', ' ')
    body_html = body_html[:65532]

    blocked = database.get_blocked(user)
    default_blocks = database.defaults("blocked")

    mail = request.form.get('sender')

    reDomain = recipient.split("@")[1]

    domain = mail.split("@")[1]

    b_mails = blocked["mails"]
    b_domains = blocked["domains"]
    b_regex = blocked["regex"]
    #  print(reDomain.lower() != "themails.ml" and reDomain.lower != "seemsgood.us" )
    if reDomain.lower() != "themails.ml" and reDomain.lower(
    ) != "seemsgood.us":
        # print("su")
        b_mails = blocked["mails"] + default_blocks["mails"]
        b_domains = blocked["domains"] + default_blocks["domains"]
        b_regex = blocked["regex"] + default_blocks["regex"]

    print(b_domains, b_mails, b_regex)

    if mail in b_mails:
        print(f"blocked mail - {mail}")
        if mail == "bounces@heroku.com" or mail == "noreply@heroku.com":
            ostrich.send_message(
                user,
                "**Incoming mail from heroku.com.\n\nNote: You can receive mails from heroku only for mails which belongs to themails.ml**"
            )

        return Response(status=200)

    if domain in b_domains:
        print(f"blocked domain - {domain}")
        if domain == "heroku.com":
            ostrich.send_message(
                user,
                "**Incoming mail from heroku.com.\n\nNote: You can receive mails from heroku only for mails which belongs to themails.ml**"
            )
        return Response(status=200)

    for exp in b_regex:
        regex = re.compile(exp)
        match = regex.search(mail)
        if match:
            print(f"blocked {mail} : matches regex {exp}")
            return Response(status=200)

    headers = {"Content-Type": "application/json"}
    data = {"Title": subject, "Author": "Penker", "Content": body_html}

    req = requests.post("https://paste.theostrich.eu.org/api/documents",
                        data=json.dumps(data),
                        headers=headers)
    res = json.loads(req.text)

    key = res['result']['key']
    mail_content = strip_tags(body_html).strip()

    text = f"\
**Sender     :** {sender}\n\
**Recipient  :** {recipient}\n\
**Subject    :** {subject}\n\
**Content    :** [Raw](https://paste.theostrich.eu.org/{key})\n\n\
**Message    :** \n{mail_content[:200]}...\
"

    if sender.startswith("bounce"):
        by = request.form.get("from")
        text = f"\
**Sender     :** {sender}\n\
**From       :** {by}\n\
**Recipient  :** {recipient}\n\
**Subject    :** {subject}\n\
**Content    :** [Raw](https://paste.theostrich.eu.org/{key})\n\n\
**Message    :** \n{mail_content[:200]}...\
"

    ostrich.send_message(
        user,
        text,
        disable_web_page_preview=True,
        reply_markup=InlineKeyboardMarkup([[
            InlineKeyboardButton("View mail",
                                 url=f"https://inbox.mailable.me/{key}"),
        ], [
            InlineKeyboardButton("Delete", callback_data=f"del"),
        ]]))

    #ostrich.send_message(
    #   user,
    #   f'**Message:**\n\n{mail_content[:200]}...',
    #   disable_web_page_preview=True,
    #   reply_markup=InlineKeyboardMarkup([ [
    #      InlineKeyboardButton("Close", callback_data=f"close"),
    #   ]]))

    return Response(status=200)


myclient = pymongo.MongoClient(os.environ['mongo_uri'])
db = myclient['mailis']
collection = db["usercache"]


@ostrich.on_message(filters.command(["broadcast"]))
async def broadcast(client, message):
    chat_id = message.chat.id
    botOwnerID = [1775541139, 1520625615]
    if chat_id in botOwnerID:
        await message.reply_text("Broadcasting...")
        chat = (collection.find({}, {'userid': 1, '_id': 0}))
        chats = [sub['userid'] for sub in chat]
        failed = 0
        for chat in chats:
            try:
                await message.reply_to_message.copy(chat)
                time.sleep(2)
            except:
                failed += 1
                print("Couldn't send broadcast to %s, group name %s", chat)
        await message.reply_text(
            "Broadcast complete. {} users failed to receive the message, probably due to being kicked."
            .format(failed))
    else:
        await client.send_message(
            1520625615, f"Someone tried to access broadcast command,{chat_id}")


server = Thread(target=run)
server.start()
ostrich.run()
