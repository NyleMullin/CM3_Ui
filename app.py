import os
absolute_path = os.path.dirname(__file__)
import fileinput
import socket
import pandas as pd
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

TYPES = {
    'A' : 'Tac_G_TRX',
    'C' : 'nesie2_controller',
    'I' : 'Tac_G_Controller',
    'T' : 'nesie2_pa_tx',
    'U' : 'Covert',    # C/U-NESIE
    'B' : 'Tac_A_TRX/Tac_U',
    'R' : 'REDSTREAK',
    'F' : 'flight_unit',
    'K' : 'Tac_A_Controller',
    '' : 'Other'
}

KEYS = ('name', 'mac', 'type', 'ID', 'group')

def unit_search():
    results = dict()
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
          
            sock.settimeout(2)
            sock.bind(('0.0.0.0', 30303))                                    
            print('Broadcasting on 255.255.255.255, port 30303 to find NESIE devices.')
            sock.sendto(b'Discovery: Python', ('255.255.255.255', 30303))
            while True:
                data, address = sock.recvfrom(1024)
                values = data.decode('utf8').split()
                
                if len(values) >= 3 and values != ['Discovery:','Python']:    # this should catch CM/MCM/ACM/S/T/U-NESIEs
                    found = TYPES.get(values[2], None)
                    
                    if found is not None:
                        values.insert(2, found)
                        device = dict(zip(KEYS, values))
                        device['mac'] = ':'.join(device['mac'].lower().split('-'))
                        results[address[0]] = device
    except socket.timeout as e:
        print(e)
        pass

    return results

def gui_data_import(*eth_filter):

    headings = ['IP Address','Name','Mac Address','Type', 'ID','Group']
    eth_list = unit_search()
    gui_eth_df = pd.DataFrame.from_dict(eth_list, orient='index')
    gui_eth_df_filt = gui_eth_df.sort_values('name')

    if eth_filter[0] != '':
        gui_eth_df_filt = gui_eth_df.loc[gui_eth_df['ID'] == eth_filter[0]]

    gui_eth_df_filt = gui_eth_df_filt.rename_axis('ip_adress').reset_index()
    gui_eth_list = gui_eth_df_filt.values.tolist()

    return gui_eth_df_filt

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

   gui_eth_df_filt = gui_data_import('B')
   
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
                        wifi_input_ip=wifi_input_ip,
                        tables=[gui_eth_df_filt.to_html(classes='data', header="true")])

#background process happening without any refreshing
@app.route('/background_process_test')
def background_process():
   return "<p>Hello!</p>"

#background process happening without any refreshing
@app.route('/wifiMode')
def bp_wifiMode():
   # Switch channel from 11 - 36 or vice verse
   hostapd_path = "/etc/hostapd/hostapd.conf"
   with open(hostapd_path, 'r+') as default_conf:
      for line in default_conf:
         if line.lstrip().startswith('channel='):
            channel = line
            channel = line.rsplit('=', 1)[1]
         if line.lstrip().startswith('hw_mode='):
            hw_mode = line
   with open(hostapd_path, 'r+') as default_conf:
      for line in default_conf:
         if line.lstrip().startswith('channel='):
            channel = line.rsplit('=', 1)[1]
            print(channel, "found wifi channel")
            if channel <= "14":
               print("WiFi is in 2.4 ghz mode changing to 5ghz")
               with fileinput.input(hostapd_path, inplace=True) as default_conf:
                  for linefile in default_conf:
                     op_line = linefile.replace(channel, '36\n')
                     print(op_line, end='')
            if channel >= "14":
               print("Wifi is in 5ghz mode changing to 2.4ghz")
               with fileinput.input(hostapd_path, inplace=True) as default_conf:
                  for linefile in default_conf:
                     op_line = linefile.replace(channel, '11\n')
                     print(op_line, end='')
         elif line.lstrip().startswith('hw_mode='):
            hw_mode = line
            hw_mode = hw_mode.rstrip()
            print("wifi is currently in hardware mode: ", len(hw_mode))
            if hw_mode == "hw_mode=g" and channel <= "14":
               print("Channel is in 2.4ghz changin to 5ghz")
               with fileinput.input(hostapd_path, inplace=True) as default_conf:
                  for linefile in default_conf:
                     op_line = linefile.replace(hw_mode, 'hw_mode=a')
                     print(op_line, end='')
            if hw_mode == "hw_mode=a" and channel >= "14":
               print("Channel is in 2.4ghz changin to 5ghz")
               with fileinput.input(hostapd_path, inplace=True) as default_conf:
                  for linefile in default_conf:
                     op_line = linefile.replace(hw_mode, 'hw_mode=g')
                     print(op_line, end='')
   print(line, '1\n')

   subprocess.run(["sudo", "ip", "link", "set", "wlan0", "down"])
   subprocess.Popen(("/etc/init.d/hostapd", "restart"), shell = False).wait()
   subprocess.run(["sudo", "ip", "link", "set", "wlan0", "up"])
   time.sleep(5)
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

#background process happening without any refreshing
# @app.route('/admin', methods=["POST", "GET"])
# def bp_ethDiscover():
#    gui_eth_df_filt = gui_data_import('B')
#    return render_template('admin.html',  tables=[gui_eth_df_filt.to_html(classes='data', header="true")])


if __name__ == "__main__":

   app.run(host='192.168.168.199', port=8080, debug=True)
