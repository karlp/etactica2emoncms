# Karl Palsson October 2018
# Listens to the live MQTT stream from an eTactica device and republishes
# to an EmonCMS system.
# http://www.etactica.com
# http://emoncms.org

import argparse
import json
import logging
import requests
import paho.mqtt.client as mqtt


def parseargs():
    parser = argparse.ArgumentParser(description="Listens to an eTactica MQTT stream and posts to EmonCMS",
                                     formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument("--mhost", help="MQTT Host for listening to messages", default="localhost")
    parser.add_argument("--emon", help="base emoncms url for posting", default="https://emon.example.org/input/post")
    parser.add_argument("--key", help="EmonCMS API key for posting data", required=True)

    return parser.parse_args()


def on_message(client, udata, msg):
    try:
        # APIs that swallow exceptions written by insane developer haters
        on_message_real(client, udata, msg)
    except Exception as e:
        logging.exception("oops?", e)


def on_message_real(client, udata, msg):
    s = udata.get("s")
    opts = udata.get("opts")
    js = json.loads(msg.payload.decode("utf-8"))
    deviceid = js.get("deviceid")
    if not deviceid:
        logging.warning("No deviceid in message?! who made this?!")
        return
    if js.get("error"):
        logging.debug("Ignoring failed reading on %s", deviceid)
        return
    senml = js.get("senml")
    if not senml:
        logging.warning("invalid json on topic? no senml on topic: %s", msg.topic)
    values = {}
    for e in senml.get("e"):
        n = e.get("n")
        v = e.get("v")
        if not n and not v:
            logging.warning("senml element without name and value?! who made this?!")
            continue
        # undocumented, but can't have / in point name :)
        n = n.replace("/", "_")
        values[n] = v

    # curl --data "node=1&data={power1:100,power2:200,power3:300}&apikey=8bc8733d80dd6b2272ba99f80e3d5be4" "https://emon.beeroclock.net/input/post"
    topost = dict(node=deviceid, fulljson=json.dumps(values), apikey=opts.key)
    logging.info("Posting data: %s", topost)
    r = s.post(opts.emon, topost)
    if r.status_code != 200:
        logging.warning("EmonCMS API failure? %d %s", r.status_code, r.text())
        return
    resp = r.json()
    if not resp.get("success"):
        logging.warning("Data POST failed with explanation: %s", resp.get("message"))


def on_connect(client, udata, flags, rc):
    if rc == 0:
        logging.debug("got connected, susbcribing")
        client.subscribe("status/local/json/device/#")
    else:
        raise ConnectionError("failed doh")


def main(opts):
    # build our http session object, we don't want to be making new https connections every message
    s = requests.Session()

    client = mqtt.Client(userdata=dict(s=s, opts=opts))
    client.on_connect = on_connect
    client.on_message = on_message
    client.connect(opts.mhost)

    client.loop_forever()


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    main(parseargs())
