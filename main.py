from flask import Flask,render_template, request, jsonify, redirect,session, Response,send_file
import uuid 
import json
import redis
import string
import random
import os
import environment


app = Flask(__name__)
app.secret_key=json.dumps(json.load(open("keys.json", "r"))["appSecretKey"])
countries=json.load(open("countries.json", "r"))

myenv = os.getenv('MYENV')
if not myenv :
   myenv='thierry'

mode = environment.currentMode(myenv)
red= redis.Redis(host='127.0.0.1', port=6379, db=0)
did_verifier = 'did:tz:tz2NQkPq3FFA3zGAyG8kLcWatGbeXpHMu7yk'

pattern={"type": "VerifiablePresentationRequest",
            "query": [
                {
                    "type": "QueryByExample",
                    "credentialQuery": []
                }]
            }

patternSpec = {"type": "VerifiablePresentationRequest",
            "query": [
                {
                    "type": "QueryByExample",
                    "credentialQuery": [{
                    "required": True,
                    "example": {
                        "type": "",
                    }
                }]
                }]
            }

patternNationality={"type": "VerifiablePresentationRequest",
            "query": [
                {
                    "type": "QueryByExample",
                    "credentialQuery": [{
                    "required": True,
                    "example": {
                        "type": "Nationality",
                    }
                }]
                }]
            }


@app.route('/discord-bot/init/<typeP>')
def verifier_init(typeP):
    id = str(uuid.uuid1())
    url=""
    patternToSend=pattern
    if len(typeP)==2:
        for country in countries:
            if(country["alpha2Code"]):
                patternToSend=patternNationality
                url = mode.server+'discord-bot/endpoint/' + id +'?issuer=' + did_verifier+"&country="+typeP

                break
    elif len(typeP)==3:
        for country in countries:
            if(country["alpha3Code"]):
                patternToSend=patternNationality
                url = mode.server+'discord-bot/endpoint/' + id +'?issuer=' + did_verifier+"&country="+typeP

                break
    if patternToSend!=patternNationality:
        patternToSend=patternSpec
        patternToSend["query"][0]["credentialQuery"][0]["example"]["type"]=typeP
        url = mode.server+'discord-bot/endpoint/' + id +'?issuer=' + did_verifier

    patternToSend['challenge'] = str(uuid.uuid1()) # nonce
    patternToSend['domain']=mode.server
    red.setex(id,180,  json.dumps(patternToSend))
    return jsonify({"url":url,"id":id}),200


@app.route('/discord-bot/endpoint/<id>', methods = ['GET', 'POST'],  defaults={'red' : red})
def presentation_endpoint(id, red):
    try :
        my_pattern = json.loads(red.get(id).decode())
    except :
        event_data = json.dumps({"id" : id,
                                 "message" : "redis decode failed",
                                 "check" : "ko"})
        red.publish('verifier', event_data)
        return jsonify("server error"), 500
    
    if request.method == 'GET':
        return jsonify(my_pattern)
    
    if request.method == 'POST' :
        #red.delete(id)
        try : 
            result=False
        except:
            event_data = json.dumps({"id" : id,
                                    "check" : "ko",
                                    "message" : "presentation is not correct"})
            red.publish('verifier', event_data)
            return jsonify("presentation is not correct"), 403
        if result :
            event_data = json.dumps({"id" : id,
                                    "check" : "ko",
                                    "message" : result})
            red.publish('verifier', event_data)
            return jsonify(result), 403
        red.setex(id,180,  request.form['presentation'])
        presentation=request.form['presentation']
        dictionnaire=json.loads(presentation)
        typeCredential=dictionnaire["verifiableCredential"]["type"][1]
        try:
            if dictionnaire["verifiableCredential"]["credentialSubject"]["nationality"]!=request.args["country"]:
                event_data = json.dumps({"id" : id,
                                "message" : "country is wrong",
                                "check" : "ko","typeCredential":typeCredential,
                                    "presentation":request.form['presentation']}) 
                red.publish('verifier', event_data)
                return jsonify(result), 403     
        except:
            event_data = json.dumps({"id" : id,
                                    "message" : "presentation is verified",
                                    "check" : "ok","typeCredential":typeCredential,
                                        "presentation":request.form['presentation']})           
            red.publish('verifier', event_data)
            
            return jsonify("ok"), 200


@app.route('/discord-bot/verifier_stream', methods = ['GET'],  defaults={'red' : red})
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

if __name__ == '__main__':
    app.run( host = mode.IP, port= mode.port, debug =True)
