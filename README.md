## etactica2emoncms

Simple python3 service that listens to the MQTT broker on an eTactica device
and republishes the live datastream to an EmonCMS installation.

## Usage

etactica2emoncms.py --mhost 192.168.3.89 --key 8bc8733d80dd6b2272ba99f80e3d5be4 --emon https://emon.example.org/input/post

## Requirements
python3, paho-mqtt, requests
