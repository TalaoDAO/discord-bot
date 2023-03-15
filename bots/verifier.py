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
except:
    logging.warning("error DB")

s = requests.Session()

    

urlStream = 'https://22f6-86-229-94-232.eu.ngrok.io/bot-verifier/verifier_stream'

def perform_time_consuming_task(id,payload,c):
   with s.get(urlStream, headers=None, stream=True) as resp:
            for line in resp.iter_lines():
                if line:
                        my_json = line.decode('utf8').replace("'", '"')
                        print(my_json)
                        data = json.loads(my_json[6:])
                        d = json.dumps(data, indent=4, sort_keys=True)
                        print(d)
                        print(id)
                        if data["id"]==id:
                            if data["check"]=="ok" :
                                print("ok "+data["id"])
                                client.loop.create_task(payload.member.send("Thank you for verifying your "+data["typeCredential"]+'. You can now use your new permissions.'))   
                                #await message.author.send(data["typeCredential"]+' Verified')      
                                roleName=""
                                if data["typeCredential"]=="BloometaPass":
                                    roleName="Bloometa"  
                                if data["typeCredential"]=="Over13":
                                    roleName="Over13"  
                                if data["typeCredential"]=="Over18":
                                    roleName="Over18"                             
                                role = discord.utils.get(client.get_guild(payload.guild_id).roles, name=roleName)
                                #await message.author.add_roles(role)
                                client.loop.create_task(payload.member.add_roles(role))
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

        if message.content == 'test':
            print(message.channel)
            print(message.channel.id)
            print(client.get_channel(1085140978156965920))
            response = requests.get('https://bda8-86-229-94-232.eu.ngrok.io/bot-verifier/init')
            url=response.json()["url"]
            id=response.json()["id"]
            print(response)
            img = qrcode.make(url)
            img.save("qrcode.png")
            await message.author.send("Hi "+message.author.name+" , scan this qrcode or click on https://app.altme.io/app/download?uri="+url+" to present your document.")
            await message.author.send(file=discord.File('qrcode.png'))
            thread = threading.Thread(target=perform_time_consuming_task, args=(id,message,self))
            thread.start()
    async def on_raw_reaction_add(self,payload):
        print(payload.message_id)
        Channel = client.get_channel(1085140978156965920)
        print(payload.emoji)
        print(payload)
        urlToQuery=""
        card=""
        if payload.message_id==1085324693227180123:
            urlToQuery='https://22f6-86-229-94-232.eu.ngrok.io/bot-verifier/init/over13'
            card="Over 13 card"
        elif payload.message_id==1085324703561961584:
            urlToQuery='https://22f6-86-229-94-232.eu.ngrok.io/bot-verifier/init/over18'
            card="Over 18 card"

        elif payload.message_id==1085324829936328804:
            urlToQuery='https://22f6-86-229-94-232.eu.ngrok.io/bot-verifier/init/bloometa'
            card="Bloometa pass"

        else:
            print("wrong message")
            return

        if payload.emoji.name == "🅰️"  :
            #print(message.channel)
            #print(message.channel.id)
            print(client.get_channel(1085140978156965920))
            response = requests.get(urlToQuery)
            url=response.json()["url"]
            id=response.json()["id"]
            print(response)
            img = qrcode.make(url)
            img.save("qrcode.png")
            await payload.member.send("Hi "+payload.member.name+" , scan this qrcode or click on https://app.altme.io/app/download?uri="+url+" to present your "+card+".")
            await payload.member.send(file=discord.File('qrcode.png'))
            thread = threading.Thread(target=perform_time_consuming_task, args=(id,payload,self))
            thread.start()
            """print(payload.message_id)
            role = discord.utils.get(client.get_guild(payload.guild_id).roles, name="role")
            await payload.member.add_roles(role)"""

intents = discord.Intents.default()
intents.message_content = True
client = MyClient()
tree=app_commands.CommandTree(client)

@tree.command(name="test",description="testing")
async def self(interaction: discord.Interaction, name:str):
    await interaction.response.send_message(f"Hello {name}")

@tree.command(name="add_verification",description="Add a verifial credential verification to give roles.")
async def self(interaction: discord.Interaction, role:str,vc:str,channel:str):
    #await interaction.response.send_message(f"Hello {name}")
    guild_id=interaction.guild_id
    #channel = discord.utils.get(interaction.guild.channels,name="over-13").id
    roleObj = discord.utils.get(interaction.guild.roles, name=role)
    msg = await discord.utils.get(interaction.guild.channels,name=channel).send("React to this message to verify your "+vc+".")
    message_idDB = msg.id

    try:
        with sql.connect("database.db") as con:
            cur = con.cursor()
            cur.execute("INSERT INTO links (guild_id,message_id,role,vc) VALUES (?,?,?,?)",(interaction.guild_id,message_idDB,role,vc) )
            con.commit()
            msg = "link successfully added"
    except:
        con.rollback()
        msg = "error in insert operation" 
    finally:
        con.close()
        logging.info("msg db %s", msg)

client.run('MTA4MjY2NDMxODA0ODQxMTczOA.Gg5FrQ.pbT45HBweReiSYNWheaqMb0DDGhUoInA78PNGY')

