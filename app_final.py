import os
absolute_path = os.path.dirname(__file__)
import fileinput
import socket
import pandas as pd
import sys
sys.path.append('/home/cm3/system/') # reletive path todo
import globalvars
import powerbutton
import clear_oled
import signal
import subprocess
import math
import copy
from board import SCL, SDA
import busio
from PIL import Image, ImageDraw, ImageFont
sys.path.append('/home/cm3/Adafruit_CircuitPython_SSD1306/')
import adafruit_ssd1306
import json
import os
import threading
from datetime import date, datetime
import time
from flask import Flask, render_template, request, url_for, json
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired
app = Flask(__name__)
SECRET_KEY = os.urandom(32)
app.config['SECRET_KEY'] = SECRET_KEY
app.config['WTF_CSRF_ENABLED'] = False
app.config['WTF_CSRF_METHODS'] = []

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
    if gui_eth_df.empty:
      data = [['NO DEVICES FOUND', 400]]
      gui_eth_df_filt = pd.DataFrame(data, columns=['MESSAGE', 'CODE'])
      return gui_eth_df_filt
    gui_eth_df_filt = gui_eth_df.sort_values('name')

    if eth_filter[0] != '':
        gui_eth_df_filt = gui_eth_df.loc[gui_eth_df['ID'] == eth_filter[0]]

    gui_eth_df_filt = gui_eth_df_filt.rename_axis('ip_adress').reset_index()
    gui_eth_list = gui_eth_df_filt.values.tolist()

    return gui_eth_df_filt

# Kill variable for the loop thread
exit_now = False

# initalising systemState variables
systemState = {
   "system":{
         "CPU": "None",
         "Mem": "None",
         "Disk": "None",
         "Hostname": "None",
   },
   "network":{
         "IP": "None",
         "MAC": "None",
         "SSID": "None",
         "Ports": "None",
         "Freq": "None",
         "Clients": "None",
   },
   "link":{
         "Connected": False,
         "Strength": False,
   },
   "battery":{
         "Charging": False,
         "Percentage": False,
         "TTC": False,
         "TTD": False,
         "Volt": False,
   },
   "mapping":{
         "Running": False,
         "Style": False,
         "Tileset": False,
   },
   "systemlog":{
         "Systemlog": False,
   },
}

def write_oled(command):
   # Opening JSON file
   with open('/home/cm3/system/state.json', 'r') as openfile: # reletive path todo
      # Reading from json file
      json_object = json.load(openfile)
      print(json_object)
   if command == 'CPU':
      globalvars.display = json_object["system"]["CPU"]
      print(f'Setting Oled to show {command}')
      globalvars.changed = True
   elif command == 'Mem':
      globalvars.display = json_object["system"]["Mem"]
      print(f'Setting Oled to show {command}')
      globalvars.changed = True
   elif command == 'Disk':
      globalvars.display = json_object["system"]["Disk"]
      print(f'Setting Oled to show {command}')
      globalvars.changed = True
   else:
      globalvars.display = json_object["network"]["IP"]
      print(f'Setting Oled to show {command}')
      globalvars.changed = True

# web function to get json data
def read_system_state():
   lock.acquire()
   returnValue = copy.deepcopy(systemState)
   lock.release()
   return json.dumps(returnValue)

def updateJson(lock):
   global systemState
   global exit_now
   # raise TypeError("Only integers are allowed")
   print("updateJsoncalled")
   while exit_now == False:
      try:

         cmd = "hostname -I | cut -d' ' -f1"
         IP = subprocess.check_output(cmd, shell=True).decode("utf-8")
         IP = IP.rstrip('\n')

         cmd = 'cut -f 1 -d " " /proc/loadavg'
         CPU = subprocess.check_output(cmd, shell=True).decode("utf-8")
         CPU = CPU.rstrip('\n')

         cmd = "free -m | awk 'NR==2{printf \"Mem: %s/%s MB  %.2f%%\", $3,$2,$3*100/$2 }'"
         MemUsage = subprocess.check_output(cmd, shell=True).decode("utf-8")

         cmd = 'df -h | awk \'$NF=="/"{printf "Disk: %d/%d GB  %s", $3,$2,$5}\''
         Disk = subprocess.check_output(cmd, shell=True).decode("utf-8")

         cmd = "ip addr show $(awk 'NR==3{print $1}' /proc/net/wireless | tr -d :) | awk '/ether/{print $2}'"
         MAC = subprocess.check_output(cmd, shell=True).decode("utf-8")

         cmd = "hostnamectl | grep hostname | awk '{print $2,$3}'"
         Hostname = subprocess.check_output(cmd, shell=True).decode("utf-8")

         cmd = "sudo netstat -tuwanp4 | awk '{print $4}' | grep ':' | cut -d ':' -f 2 | sort | uniq"
         Ports = subprocess.check_output(cmd, shell=True).decode("utf-8")

         cmd = "iwconfig wlan0 | grep Freq | awk '{print $2,$3}' | cut -d':' -f2"
         Freq = subprocess.check_output(cmd, shell=True).decode("utf-8")

         cmd = """iwconfig wlan0 | grep ESSID | awk '{print $4}' | cut -d'"' -f2"""
         SSID = subprocess.check_output(cmd, shell=True).decode("utf-8")

         cmd = "who | wc -l"
         Clients = subprocess.check_output(cmd, shell=True).decode("utf-8")
      
      except subprocess.CalledProcessError as e:
            exit_now = True
            break

      lock.acquire()

      # Data to be written
      systemState = {
         "system":{
               "CPU": CPU,
               "Mem": MemUsage,
               "Disk": Disk,
               "Hostname": Hostname,
         },
         "network":{
               "IP": IP,
               "MAC": MAC,
               "SSID": SSID,
               "Ports": Ports,
               "Freq": Freq,
               "Clients": Clients,
         },
         "link":{
               "Connected": False,
               "Strength": False,
         },
         "battery":{
               "Charging": False,
               "Percentage": False,
               "TTC": False,
               "TTD": False,
               "Volt": False,
         },
         "mapping":{
               "Running": False,
               "Style": False,
               "Tileset": False,
         },
         "systemlog":{
               "Systemlog": False,
         },
      }

      with open('/home/cm3/system/state.json', 'w', encoding='utf-8') as f: # reletive path todo
         json.dump(systemState, f, ensure_ascii=False, indent=4)
      
      lock.release()
      time.sleep(1)

def run_oled(lock):
   powerbutton.init()

   clear_oled.init() # Clears up artifacts temp fix investigate why oled not use full physical diplay

   # Create the I2C interface.
   i2c = busio.I2C(SCL, SDA)

   # Create the SSD1306 OLED class.
   # The first two parameters are the pixel width and pixel height.  Change these
   # to the right size for your display!
   disp = adafruit_ssd1306.SSD1306_I2C(96, 16, i2c)

   # rotate display
   disp.rotation = 2

   # Clear display.
   disp.fill(0)
   disp.write_cmd(0x2E)
   disp.show()

   # Create blank image for drawing.
   # Make sure to create image with mode '1' for 1-bit color.
   width = disp.width
   height = disp.height
   image = Image.new("1", (width, height))

   # Get drawing object to draw on image.
   draw = ImageDraw.Draw(image)

   # Draw a black filled box to clear the image.
   draw.rectangle((0, 0, width, height), outline=0, fill=0)

   # Draw some shapes.
   # First define some constants to allow easy resizing of shapes.
   padding = +3
   top = padding
   bottom = height - padding
   # Move left to right keeping track of the current x position for drawing shapes.
   #x = 0


   # Load default font.
   font = ImageFont.load_default()

   text = globalvars.display # ("172.16.136.00")
   maxwidth, unused = draw.textsize(text, font=font)

   # Alternatively load a TTF font.  Make sure the .ttf font file is in the
   # same directory as the python script!
   # Some other nice fonts to try: http://www.dafont.com/bitmap.php
   # font = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', 9)

   # Set animation
   amplitude = height / 4
   offset = height / 2 - 4
   velocity = -2
   startpos = width

   pos = startpos

   while not exit_now:
      # Draw a black filled box to clear the image.
      draw.rectangle((0, 0, width, height), outline=0, fill=0)

      #draw.text((x, top + 0), "IP: " + IP, font=font, fill=255)

      # Display image.
      x = pos
      for i, c in enumerate(globalvars.display):
         # Stop drawing if off the right side of screen.
         if x > width:
               break
         # Calculate width but skip drawing if off the left side of screen.
         if x < -10:
               char_width, char_height = draw.textsize(c, font=font)
               x += char_width
               continue
         # Calculate offset from sine wave.
         # y = offset + math.floor(amplitude * math.sin(x / float(width) * 2.0 * math.pi))
         y = 0
         # Draw text.
         draw.text((x, y), c, font=font, fill=255)
         # Increment x position based on chacacter width.
         char_width, char_height = draw.textsize(c, font=font)
         x += char_width

      # Draw the image buffer.
      disp.image(image)
      disp.show()

      # Move position for next frame.
      pos += velocity
      # Start over if text has scrolled completely off left side of screen.
      if pos < -maxwidth:
         pos = startpos

      # Pause briefly before drawing next frame.
      time.sleep(0.05)
   else:
      # Clear display.
      disp.fill(0)
      disp.show()

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

@app.route("/")
def home():
   return render_template('main.html', jsonfile=read_json_file())

@app.route("/admin")
def main():
   wifi_input_channel = None
   wifi_form_channel = WifiChannelForm()
   wifi_input_ip = None
   wifi_form_ip = WifiStaticIp()

   try:
      gui_eth_df_filt = gui_data_import('B')
   except Exception as e:
      print(e)
   
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
   jsonfile=read_system_state()
   return jsonfile
   # return "<p>Hello</p>!"

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

   lock = threading.Lock()

   # creating threads
   t1 = threading.Thread(target=run_oled, args=(lock,))
   t2 = threading.Thread(target=updateJson, args=(lock,))

   # start threads
   t1.start()
   t2.start()

   app.run(host='0.0.0.0', port=80, debug=False)

   print("flask exit")
   exit_now = True
   t1.join()
   t2.join()
