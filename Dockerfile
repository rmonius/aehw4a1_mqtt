FROM python:3

ADD ./aehw4a1_mqtt.py /home

RUN mkdir /home/config
ADD ./config/aehw4a1_mqtt.ini /home/config

RUN pip install pyaehw4a1
RUN pip install paho-mqtt
RUN pip install ifaddr
WORKDIR /home
CMD [ "python", "/home/aehw4a1_mqtt.py" ]