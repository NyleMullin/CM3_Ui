'''

Adapted excerpt from Getting Started with Raspberry Pi by Matt Richardson

Modified by Rui Santos
Complete project details: https://randomnerdtutorials.com

'''

import os
absolute_path = os.path.dirname(__file__)
import threading
import subprocess
from datetime import date, datetime
import time
import RPi.GPIO as GPIO
from flask import Flask, render_template, request, url_for, json
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired
app = Flask(__name__)
app.config['SECRET_KEY'] = "root"

# Create a class form for WiFi channel
class WifiChannelForm(FlaskForm):
   wifi_input_channel = StringField("Wifi Channel", validators=[DataRequired()])
   submit = SubmitField("Submit")

# Create a class form for WiFi static ip
class WifiStaticIp(FlaskForm):
   wifi_input_ip = StringField("Set Static ip of basestation", validators=[DataRequired()])
   submit = SubmitField("Submit")

def read_json_file():
   relative_path = "../system/state.json"
   full_path = os.path.join(absolute_path, relative_path)
   with open(full_path, 'r') as openfile:
            # Reading from json file
            json_object = json.load(openfile)
   # return render_template('main.html', jsonfile=json.dumps(json_object["system"]))
   return json.dumps(json_object)

def printloadsofstuff(): # Test function
   i = 0
   while i < 5:
      i += 1
      print("test")

def changeWifiChannel(channel): # Finish
   print("changing wifi channel from '{}' to", channel)

def changeWifiIp(wifi_ip): # Finish
   print("Setting basestation to a static ip of: ", wifi_ip)

@app.route("/") # Home Page
def home():
   return render_template('main.html', jsonfile=read_json_file())

@app.route("/admin", methods=['GET', 'POST'])
def main():
   wifi_input_channel = None
   wifi_form_channel = WifiChannelForm()
   wifi_input_ip = None
   wifi_form_ip = WifiStaticIp()
   
   if wifi_form_channel.validate_on_submit():
      wifi_input_channel = wifi_form_channel.wifi_input_channel.data
      wifi_form_channel.wifi_input_channel.data = ''
      changeWifiChannel(wifi_input_channel)

   if wifi_form_ip.validate_on_submit():
      wifi_input_ip = wifi_form_ip.wifi_input_ip.data
      wifi_form_ip.wifi_input_ip.data = ''
      changeWifiIp(wifi_input_ip)
   
   return render_template('admin.html', jsonfile=read_json_file(),
                        wifi_form_channel=wifi_form_channel,
                        wifi_input_channel=wifi_input_channel,
                        wifi_form_ip=wifi_form_ip,
                        wifi_input_ip=wifi_input_ip)

#background process happening without any refreshing
@app.route('/background_process_test')
def background_process():
   return "<p>Hello!</p>"

#background process happening without any refreshing
@app.route('/wifiMode')
def bp_wifiMode():
   # change channel from 11 - 36
   hostapd_path = "/etc/hostapd/hostapd.conf"
   with open(hostapd_path, 'r+') as default_config:
      for line in default_config:
         if line.lstrip().startswith('channel='):
            channel = line.rsplit('=', 1)[1]
            if channel <= "14":
               print("WiFi is in 2.4 ghz mode changing to 5ghz")
               default_config.write('channel={}\n'.format(36))
            else:
               print("Wifi is in 5ghz mode changing to 2.4ghz")
               default_config.write('channel={}\n'.format(11))

   # subprocess.run(["sudo", "ip", "link", "set", "wlan0", "down"])
   # subprocess.Popen(("/etc/init.d/hostapd", "restart"), shell = False).wait()
   # subprocess.run(["cm3"])
   # subprocess.run(["sudo", "ip", "link", "set", "wlan0", "up"])
   # time.sleep(5)
   return str(line)

#background process happening without any refreshing
@app.route('/wifiDhcp')
def bp_wifiDhcp():
   return "<p>Toggle enabling the dhcp</p>"

#background process happening without any refreshing
@app.route('/wifiRestart')
def bp_wifiRestart():
   subprocess.run(["sudo", "ip", "link", "set", "wlan0", "down"])
   subprocess.Popen(("/etc/init.d/hostapd", "restart"), shell = False).wait()
   subprocess.run(["cm3"])
   subprocess.run(["sudo", "ip", "link", "set", "wlan0", "up"])
   time.sleep(5)

#background process happening without any refreshing
@app.route('/powerRestart')
def bp_powerRestart():
   os.system("sudo reboot")

#background process happening without any refreshing
@app.route('/powerOff')
def bp_powerOff():
   os.system("sudo shutdown -h now")


if __name__ == "__main__":

   app.run(host='172.16.136.87', port=8080, debug=True)
