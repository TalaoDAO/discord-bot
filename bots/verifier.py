import discord
import qrcode
import requests
import json


s = requests.Session()

    

urlStream = 'https://d8fa-86-229-94-232.eu.ngrok.io/bot-verifier/verifier_stream'

class MyClient(discord.Client):
    async def on_ready(self):
        print('Logged on as', self.user)

    async def on_message(self, message):
        # don't respond to ourselves
        if message.author == self.user:
            return

        if message.content == 'ping':
            await message.channel.send('pong')
            response = requests.get('https://d8fa-86-229-94-232.eu.ngrok.io/bot-verifier/init')
            url=response.json()["url"]
            img = qrcode.make(url)
            img.save("qrcode.png")
            await message.channel.send(file=discord.File('qrcode.png'))
            with s.get(urlStream, headers=None, stream=True) as resp:
                for line in resp.iter_lines():
                    if line:
                        my_json = line.decode('utf8').replace("'", '"')
                        #print(my_json)
                        # Load the JSON to a Python list & dump it back out as formatted JSON
                        data = json.loads(my_json[6:])
                        print(type(data))
                        d = json.dumps(data, indent=4, sort_keys=True)
                        print(d)
                        print(type(d))
                        if data["check"]=="ok":
                            print("ok "+data["id"])
                            return

intents = discord.Intents.default()
intents.message_content = True
client = MyClient(intents=intents)
client.run('MTA4MjY2NDMxODA0ODQxMTczOA.Genteu.UliKEqeCFis_-8YTs3FerJsSATeu-EtwULKNfU')

