import discord
import qrcode
import requests
import json
import asyncio
import functools
import typing
import threading
from datetime import datetime
from discord import app_commands
import sqlite3 as sql
import logging 

try:
    sql.connect("database.db").cursor().execute("CREATE TABLE IF NOT EXISTS links(guild_id INTEGER,message_id INTEGER,role TEXT,vc TEXT)")
    sql.connect("database.db").cursor().execute("CREATE TABLE IF NOT EXISTS data_collecting(guild_id INTEGER,message_id INTEGER,channel TEXT,vc TEXT)")

except:
    logging.warning("error DB")

s = requests.Session()

    

urlStream = 'https://0271-86-229-94-232.eu.ngrok.io/bot-verifier/verifier_stream'

def verifying_data(role,id,payload,c):
   with s.get(urlStream, headers=None, stream=True) as resp:
            for line in resp.iter_lines():
                if line:
                        my_json = line.decode('utf8').replace("'", '"')
                        data = json.loads(my_json[6:])
                        d = json.dumps(data, indent=4, sort_keys=True)
                        if data["id"]==id:
                            if data["check"]=="ok" :
                                client.loop.create_task(payload.member.send("Thank you for verifying your "+data["typeCredential"]+'. You can now use your new permissions.'))   
                                #await message.author.send(data["typeCredential"]+' Verified')                                 
                                roleObj = discord.utils.get(client.get_guild(payload.guild_id).roles, name=role)
                                #await message.author.add_roles(role)
                                client.loop.create_task(payload.member.add_roles(roleObj))
                                return
                            else:
                                client.loop.create_task(payload.member.send('Error'))   
                                #await message.author.send('Error')
                                return

def collecting_data(channel,id,payload,c):
   with s.get(urlStream, headers=None, stream=True) as resp:
            for line in resp.iter_lines():
                if line:
                        my_json = line.decode('utf8').replace("'", '"')
                        data = json.loads(my_json[6:])
                        d = json.dumps(data, indent=4, sort_keys=True)
                        if data["id"]==id:
                            if data["check"]=="ok" :
                                client.loop.create_task(payload.member.send("Thank you for presenting your "+data["typeCredential"]+'.'))   
                                presentation=data["presentation"]
                                print(presentation)
                                print(type(presentation))
                                #.decode('utf8').replace("'", '"')
                                dataP = json.loads(presentation)
                                print(dataP)
                                print(type(dataP))
                                
                                #["verifiableCredential"]["credentialSubject"]
                                #await message.author.send(data["typeCredential"]+' Verified')                                 
                                #roleObj = discord.utils.get(client.get_guild(payload.guild_id).roles, name=role)
                                #await message.author.add_roles(role)
                                print(payload)
                                client.loop.create_task(discord.utils.get(client.get_guild(payload.guild_id).channels,name=channel).send(payload.member.name+" presented "+str(dataP["verifiableCredential"]["credentialSubject"])))
                                return
                            else:
                                client.loop.create_task(payload.member.send('Error'))   
                                #await message.author.send('Error')
                                return

class MyClient(discord.Client):
    def __init__(self):
        super().__init__(intents=discord.Intents.default())
        self.synced=False
    async def send_message(self,member,message):
        print(message)
        await member.send(message)

    async def on_ready(self):
        await self.wait_until_ready()
        if not self.synced:
            await tree.sync()
            self.synced=True
            print("synced")
        print('Logged on as', self.user)
    
    async def on_message(self, message):
        # don't respond to ourselves
        if message.author == self.user:
            return

    async def on_raw_reaction_add(self,payload):
        action=""
        try:
            with sql.connect("database.db") as con:
                cur = con.cursor()
                cur.execute("select vc,role from links where message_id="+str(payload.message_id)+" and guild_id="+str(payload.guild_id))
                select = cur.fetchall()
                action="link"
        except sql.Error as er:
            logging.error('SQLite error: %s', ' '.join(er.args))
        if len(select)==0:
            try:
                with sql.connect("database.db") as con:
                    cur = con.cursor()
                    cur.execute("select vc,channel from data_collecting where message_id="+str(payload.message_id)+" and guild_id="+str(payload.guild_id))
                    select = cur.fetchall()
                    action="collection"
            except sql.Error as er:
                logging.error('SQLite error: %s', ' '.join(er.args))
            if len(select)==0:
                return


            
        #urlToQuery=""
        #card=""
        urlToQuery='https://0271-86-229-94-232.eu.ngrok.io/bot-verifier/init/'+select[0][0]
        card=select[0][0]


        response = requests.get(urlToQuery)
        url=response.json()["url"]
        id=response.json()["id"]
        img = qrcode.make(url)
        img.save("qrcode.png")
        if action=="link":
            await payload.member.send("Hi "+payload.member.name+" , scan this qrcode or click on https://app.altme.io/app/download?uri="+url+" to present your "+card+".")
            await payload.member.send(file=discord.File('qrcode.png'))
            thread = threading.Thread(target=verifying_data, args=(select[0][1],id,payload,self))
            thread.start()
        if action=="collection":
            await payload.member.send("Hi "+payload.member.name+" , scan this qrcode or click on https://app.altme.io/app/download?uri="+url+" to present your "+card+".")
            await payload.member.send(file=discord.File('qrcode.png'))
            thread = threading.Thread(target=collecting_data, args=(select[0][1],id,payload,self))
            thread.start()
        


intents = discord.Intents.default()
intents.message_content = True
client = MyClient()
tree=app_commands.CommandTree(client)

@tree.command(name="add_verification",description="Add a verifial credential verification to give roles.")
async def self(interaction: discord.Interaction, role:str,vc:str,channel:str):
    #await interaction.response.send_message(f"Hello {name}")
    guild_id=interaction.guild_id
    #channel = discord.utils.get(interaction.guild.channels,name="over-13").id
    roleObj = discord.utils.get(interaction.guild.roles, name=role)
    msg = await discord.utils.get(interaction.guild.channels,name=channel).send("React to this message to verify your "+vc+" and get the role "+role+".")
    message_idDB = msg.id

    try:
        with sql.connect("database.db") as con:
            cur = con.cursor()
            cur.execute("INSERT INTO links (guild_id,message_id,role,vc) VALUES (?,?,?,?)",(interaction.guild_id,message_idDB,role,vc) )
            con.commit()
            msg = "Link "+vc+" to "+role+" successfully added."

    except:
        con.rollback()
        msg = "error in insert operation" 
    finally:
        con.close()
        logging.info("msg db %s", msg)
        await interaction.response.send_message(msg)

@tree.command(name="add_collection",description="Add a verifial credential collection to give roles.")
async def self(interaction: discord.Interaction,vc:str,channel_bot:str,channel_reception:str):
    #await interaction.response.send_message(f"Hello {name}")
    guild_id=interaction.guild_id
    #channel = discord.utils.get(interaction.guild.channels,name="over-13").id
    #roleObj = discord.utils.get(interaction.guild.roles, name=role)
    msg = await discord.utils.get(interaction.guild.channels,name=channel_bot).send("React to this message to present us your "+vc+".")
    message_idDB = msg.id

    try:
        with sql.connect("database.db") as con:
            cur = con.cursor()
            cur.execute("INSERT INTO data_collecting (guild_id,message_id,channel,vc) VALUES (?,?,?,?)",(interaction.guild_id,message_idDB,channel_reception,vc) )
            con.commit()
            msg = "Data collection for "+vc+" ready."


    except:
        con.rollback()
        msg = "error in insert operation" 
    finally:
        con.close()
        logging.info("msg db %s", msg)
        await interaction.response.send_message(msg)

client.run('MTA4MjY2NDMxODA0ODQxMTczOA.GOMXWx.bn43J7sU_wrRBeOS_YVBps1Wee-rZ2iwny4rA4')

