import os
import pymongo
import json

myclient = pymongo.MongoClient("mongodb+srv://mongo")
database = myclient['mail']
collection = database["user"]


def scrape(data):
    userid = data.from_user.id
    
    firstseen = data.date
    result = collection.find_one({'userid': userid})

    try:
        result['userid']
        userexist = True

    except:
        userexist = False

    username = data.from_user.username
    firstname = data.from_user.first_name
    lastname = data.from_user.last_name
    dc = data.from_user.dc_id

    scraped = {}
    scraped['userid'] = userid
    scraped['username'] = username
    scraped['firstname'] = firstname
    scraped['lastname'] = lastname
    scraped['is-banned'] = False
    scraped['dc'] = dc
    scraped['mails'] = []
    
    plan = "free"
    mail_limit = { "member":5,"non_member":2 }
    send_limits = {"at_once":3}
    
    scraped['plan'] = {
      "type"  : plan,
      "limits": {
         "mails" : mail_limit,
         "send"  : send_limits
      }
    }
    
    scraped['blocked'] = {
      "domains": [],
      "mails": [],
      "regex": []
    }
    scraped['firstseen'] = firstseen

    if (userexist == False):
        collection.insert_one(scraped)
        statial("users",1)
    
def user_info(userid):
  collection=database["usercache"]

  if userid.startswith("@"):
    cursor = collection.find({"username":userid[1:]})
    for user in cursor:
     return user

  cursor = collection.find({"userid":int(userid)})
  for user in cursor:
     return user
    
  
def user_exist(chatid,chattype):
    collection = database["usercache"]
    if chattype == 'group' or chattype == "supergroup":
        collection = database["groupcache"]
    
    result = collection.find_one({'userid': chatid})
    print(result)

    try:
        result['userid']
        userexist = True

    except:
        userexist = False

    return userexist

def add_mail(user,mail):
  mail = mail.lower()
  collection = database["usercache"]
  cursor = collection.find({'mails': mail })
  if cursor.count() != 0:
    return "exist"
  
  
  filter = { 'userid': user }
  if isinstance(user, str):
   if user.startswith("@"):
     filter = {"username":user[1:]}
  newvalues = { "$addToSet": { 'mails': mail }}
  collection.update_one(filter, newvalues)
  statial("mails",1)


def find_user(mail):
  mail = mail.lower()
  collection = database["usercache"]
  cursor = collection.find({'mails': mail })

  user = -1001337409011

  for i in cursor:
    user = i['userid']
  
    
  return user
  
def mails(user):
  
  collection=database["usercache"]
  filter = { 'userid': user }
  if isinstance(user, str):
   if user.startswith("@"):
     filter = {"username":user[1:]}
  cursor = collection.find(filter)
  mails = []
  for i in cursor:
    for mail in i["mails"]:
      mails.append(mail)
      
  return mails
  
    
def delete_mail(user,mail):
  mail = mail.lower()
  collection=database["usercache"]
  filter = {"userid":user}
  values = { "$pull": { "mails":  mail}}
  collection.update(filter, values)
  statial("mails",-1)

  return mails


def get_limits(user):
  filter = { 'userid': user }
  if isinstance(user, str):
   if user.startswith("@"):
     filter = {"username":user[1:]}
  print(filter)
  cursor = collection.find(filter)
  for i in cursor:
    plan = i["plan"]
    return plan
    
def get_blocked(user):
  filter =  {"userid":user}
  cursor = collection.find({"userid":user})
  for i in cursor:
    blocked = i["blocked"]
    return blocked

def block(user,option,value):
  collection = database["usercache"]
  filter = { 'userid': user }
  newvalues = { "$addToSet": {f"blocked.{option}" :{"$each": value}}}
  collection.update_one(filter, newvalues)

def unblock(user,option,values):
  collection=database["usercache"]
  filter = {"userid":user}
  for value in values:
    values = { "$pull": { f"blocked.{option}" : value}}
    collection.update(filter, values)


def defaults(key):
  collection=database["defaults"]
  cursor = collection.find()
  for i in cursor:
    value = i[key.lower()]
  return value
  


def statial(what,how):
  collection = database["statial"]
  collection.update( {}, {"$inc": { what : how }} )
  return "ok"
  
def get_statial():
  collection = database["statial"]
  cursor = collection.find()
  for i in cursor:
    value = i
  return value
