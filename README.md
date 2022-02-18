# aehw4a1_mqtt
MQTT client for for Hisense AEH-W4A1 wifi module with multi split support.

## aehw4a1_mqtt.ini

### Example of minimum configuration of aehw4a1_mqtt.ini 
    [mqtt-broker]
    ; host = localhost
    host = 192.168.1.200
    ; port = 1883

    [air_conditioners]
    ; <AC_Nickname> = <ip-address>
    bedroom = 192.168.1.102
    livingroom = 192.168.1.100
    chris = 192.168.1.81 

### Selection of status messages to be published to MQTT broker
The section "[messages]" allows to select the status messages which shall be 
published to the MQTT broker. All available status messages are already included in the ini file.
You need only to uncomment the messages for publishing.
If all messages are commented in the ini file, the whole JSON received from aehw4a1 will be published.

    [messages]
    # Uncommend individuale lines to publish messages only. 
    # If all lines are commented the complete dictionary received from AEHW4A1 will be published
    wind_status
    sleep_status
    mode_status
    run_status
    direction_status
    indoor_temperature_setting
    indoor_temperature_status
    ; indoor_pipe_temperature
    ; indoor_humidity_setting
    ; indoor_humidity_status
    ; somatosensory_temperature
    ; somatosensory_compensation
    ...

## Based on pyaehw4a1
This script uses the module [pyaehw4a1](https://github.com/bannhead/pyaehw4a1) from Davide Varricchio. 
Many thanks to Davide for his great work.
