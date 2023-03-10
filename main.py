from flask import Flask,render_template, request, jsonify, redirect,session, Response,send_file
import uuid 
import json
import redis
import string
import random
import os
import environment

app = Flask(__name__,static_folder=os.path.abspath('/home/achille/altme-identity/static'))
app.secret_key ="""json.dumps(json.load(open("keys.json", "r"))["appSecretKey"])"""

characters = string.digits

#init environnement variable
myenv = os.getenv('MYENV')
if not myenv :
   myenv='thierry'

mode = environment.currentMode(myenv)

red= redis.Redis(host='127.0.0.1', port=6379, db=0)

did_verifier = 'did:tz:tz2NQkPq3FFA3zGAyG8kLcWatGbeXpHMu7yk'
pattern = {"type": "VerifiablePresentationRequest",
            "query": [
                {
                    "type": "QueryByExample",
                    "credentialQuery": []
                }]
            }

@app.route('/bot-verifier/init')
def verifier_init():
    id = str(uuid.uuid1())
    pattern['challenge'] = str(uuid.uuid1()) # nonce
    """IP=extract_ip()
    pattern['domain'] = 'http://' + IP"""
    pattern['domain']="https://d8fa-86-229-94-232.eu.ngrok.io"
    # l'idee ici est de créer un endpoint dynamique
    red.set(id,  json.dumps(pattern))
    url = 'https://d8fa-86-229-94-232.eu.ngrok.io/bot-verifier/endpoint/' + id +'?issuer=' + did_verifier
    return jsonify({"url":url,"id":id}),200


@app.route('/bot-verifier/endpoint/<id>', methods = ['GET', 'POST'],  defaults={'red' : red})
def presentation_endpoint(id, red):
    try :
        my_pattern = json.loads(red.get(id).decode())
        #pprint("my_pattern "+str(my_pattern))
    except :
        event_data = json.dumps({"id" : id,
                                 "message" : "redis decode failed",
                                 "check" : "ko"})
        red.publish('verifier', event_data)
        #pprint("event data "+str(event_data))
        return jsonify("server error"), 500
    
    if request.method == 'GET':
        #pprint("my_pattern "+str(my_pattern))
        return jsonify(my_pattern)
    
    if request.method == 'POST' :
        #red.delete(id)
        try : 
            print(request.form['presentation'])
            #result = json.loads(asyncio.run(verifyPresentation(request.form['presentation'])))
            result=False
            print("result "+str(result))
        except:
            print("except")
            event_data = json.dumps({"id" : id,
                                    "check" : "ko",
                                    "message" : "presentation is not correct"})
            red.publish('verifier', event_data)
            return jsonify("presentation is not correct"), 403
        if result :
            print("result")
            event_data = json.dumps({"id" : id,
                                    "check" : "ko",
                                    "message" : result})
            red.publish('verifier', event_data)
            return jsonify(result), 403
        # mettre les tests pour verifier la cohérence entre issuer, holder et credentialSubject.id 
        # 
        red.set(id,  request.form['presentation'])
        event_data = json.dumps({"id" : id,
                                "message" : "presentation is verified",
                                "check" : "ok"})           
        red.publish('verifier', event_data)
        
        #return redirect("/")
        return jsonify("ok"), 200

# server event push, peut etre remplacé par websocket
@app.route('/bot-verifier/verifier_stream', methods = ['GET'],  defaults={'red' : red})
def presentation_stream(red):
    def event_stream(red):
        pubsub = red.pubsub()
        pubsub.subscribe('verifier')
        for message in pubsub.listen():
            if message['type']=='message':
                yield 'data: %s\n\n' % message['data'].decode()
    headers = { "Content-Type" : "text/event-stream",
                "Cache-Control" : "no-cache",
                "X-Accel-Buffering" : "no"}
    return Response(event_stream(red), headers=headers)

app.run(host = "localhost", port= 3000, debug=True)
