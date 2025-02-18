# dbus-mqtt-dcdc_converter - Emulates a physical DCDC Converter/Charger from info in MQTT data

**First off, a big thanks to [mr-manuel](https://github.com/mr-manuel) that created a bunch of templates that made this possible**

GitHub repository: [LundSoftwares/venus-os_dbus-mqtt-dcdc_converter](https://github.com/LundSoftwares/venus-os_dbus-mqtt-dcdc_converter)

### Disclaimer
I'm not responsible for the usage of this script. Use on own risk! 


### Purpose
The script emulates a physical DCDC Converter/Charger (for example Orion XS) in Venus OS. It gets the MQTT data from a subscribed topic and publishes the information on the dbus as the service com.victronenergy.dcdc.mqtt_dcdc with the VRM instance 32.


### Config
Copy or rename the config.sample.ini to config.ini in the dbus-mqtt-dcdc_converter folder and change it as you need it.


#### JSON structure
<details>
<summary>Minimum required</summary> 
  
```ruby
{
  "dcdc_charger": {
      "dc_in_voltage": 0
      }
}


```
</details>

<details>
<summary>Full</summary> 
  
```ruby
{
    "dcdc_charger": {
        "dc_in_voltage": 0,
        "dc_in_current": 0,
        "dc_in_power": 0,
        "dc_out_voltage": 0,
        "dc_out_current": 0,
        "dc_out_power": 0,
        "device_off_reason": '0x0000',
        "error_code": 0,
        "state": 0,
        "mode": 1,
        "device_function": 1
    }
}
```
</details>


### Install
1. Copy the ```dbus-mqtt-dcdc_converter``` folder to ```/data/etc``` on your Venus OS device

2. Run ```bash /data/etc/dbus-mqtt-dcdc_converter/install.sh``` as root

The daemon-tools should start this service automatically within seconds.

### Uninstall
Run ```/data/etc/dbus-mqtt-dcdc_converter/uninstall.sh```

### Restart
Run ```/data/etc/dbus-mqtt-dcdc_converter/restart.sh```

### Debugging
The logs can be checked with ```tail -n 100 -F /data/log/dbus-mqtt-dcdc_converter/current | tai64nlocal```

The service status can be checked with svstat: ```svstat /service/dbus-mqtt-dcdc_converter```

This will output somethink like ```/service/dbus-mqtt-dcdc_converter: up (pid 5845) 185 seconds```

If the seconds are under 5 then the service crashes and gets restarted all the time. If you do not see anything in the logs you can increase the log level in ```/data/etc/dbus-mqtt-dcdc_converter/dbus-mqtt-dcdc_converter.py``` by changing ```level=logging.WARNING``` to ```level=logging.INFO``` or ```level=logging.DEBUG```

If the script stops with the message ```dbus.exceptions.NameExistsException: Bus name already exists: com.victronenergy.dcdc.mqtt.dcdc"``` it means that the service is still running or another service is using that bus name.

### Multiple instances
It's possible to have multiple instances, but it's not automated. Follow these steps to achieve this:

1. Save the new name to a variable ```driverclone=dbus-mqtt-dcdc_converter-2```

2. Copy current folder ```cp -r /data/etc/dbus-mqtt-dcdc_converter/ /data/etc/$driverclone/```

3. Rename the main ```script mv /data/etc/$driverclone/dbus-mqtt-dcdc_converter.py /data/etc/$driverclone/$driverclone.py```

4. Fix the script references for service and log
```
sed -i 's:dbus-mqtt-dcdc_converter:'$driverclone':g' /data/etc/$driverclone/service/run
sed -i 's:dbus-mqtt-dcdc_converter:'$driverclone':g' /data/etc/$driverclone/service/log/run
```
5. Change the ```device_name``` and increase the ```device_instance``` in the ```config.ini```

Now you can install and run the cloned driver. Should you need another instance just increase the number in step 1 and repeat all steps.

### Compatibility
It was tested on Venus OS Large ```v3.53~2``` on the following devices:

- RaspberryPi 4
- data from Orion XS sent from NodeRed

### NodeRed Example code

<details>
<summary>Import into NodeRed runing on your VenusOS device for some simple testing</summary> 
  
```ruby
[{"id":"151b4fd27828d36a","type":"mqtt out","z":"94e5e9af83dc4fbf","name":"MQTT out","topic":"charger/dcdc","qos":"","retain":"","respTopic":"","contentType":"","userProps":"","correl":"","expiry":"","broker":"3cc159c0642d9663","x":960,"y":130,"wires":[]},{"id":"60931daffe7ec9ed","type":"inject","z":"94e5e9af83dc4fbf","name":"","props":[{"p":"payload"},{"p":"topic","vt":"str"}],"repeat":"10","crontab":"","once":false,"onceDelay":0.1,"topic":"","payload":"","payloadType":"date","x":590,"y":130,"wires":[["0a04092b5aceada6"]]},{"id":"0a04092b5aceada6","type":"function","z":"94e5e9af83dc4fbf","name":"function 16","func":"msg.payload =\n{\n    \"dcdc_charger\": {\n        \"dc_in_voltage\": 13.51,\n        \"dc_in_current\": 5.3,\n        \"dc_in_power\": 70,\n        \"dc_out_voltage\": 13.42,\n        \"dc_out_current\": 5.2,\n        \"dc_out_power\": 71,\n        \"device_off_reason\": '0x0000',\n        \"error_code\": 0,\n        \"state\": 3,\n        \"mode\": 1,\n        \"device_function\": 1\n    }\n}\nreturn msg;","outputs":1,"timeout":0,"noerr":0,"initialize":"","finalize":"","libs":[],"x":750,"y":130,"wires":[["151b4fd27828d36a","f21d17eadb64238f"]]},{"id":"3cc159c0642d9663","type":"mqtt-broker","name":"","broker":"localhost","port":"1883","clientid":"","autoConnect":true,"usetls":false,"protocolVersion":"4","keepalive":"60","cleansession":true,"birthTopic":"","birthQos":"0","birthPayload":"","birthMsg":{},"closeTopic":"","closeQos":"0","closePayload":"","closeMsg":{},"willTopic":"","willQos":"0","willPayload":"","willMsg":{},"userProps":"","sessionExpiry":""}]
```
</details>






### Screenshots

<details>
<summary>Main Screen</summary> 
  
![Skärmbild 2025-02-18 201903](https://github.com/user-attachments/assets/d444f537-8c59-4c65-bbf9-5adcb13b5469)


</details>



# Sponsor this project

<a href="https://www.paypal.com/donate/?business=MTXQ49TG6YH36&no_recurring=0&item_name=Like+my+work?+%0APlease+buy+me+a+coffee...&currency_code=SEK">
  <img src="https://pics.paypal.com/00/s/MjMyYjAwMjktM2NhMy00NjViLTg3N2ItMDliNjY3MjhiOTJk/file.PNG" alt="Donate with PayPal" />
</a>
