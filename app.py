'''

Adapted excerpt from Getting Started with Raspberry Pi by Matt Richardson

Modified by Rui Santos
Complete project details: https://randomnerdtutorials.com

'''

import os
import threading
from datetime import date, datetime
import time
import RPi.GPIO as GPIO
from flask import Flask, render_template, request, url_for, json
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired
app = Flask(__name__)
app.config['SECRET_KEY'] = "root"

GPIO.setmode(GPIO.BCM)

# Create a dictionary called pins to store the pin number, name, and pin state:
pins = {
   23 : {'name' : 'GPIO 23', 'state' : GPIO.LOW},
   24 : {'name' : 'GPIO 24', 'state' : GPIO.LOW}
   }

# Set each pin as an output and make it low:
for pin in pins:
   GPIO.setup(pin, GPIO.OUT)
   GPIO.output(pin, GPIO.LOW)

def read_json_file():
   absolute_path = os.path.dirname(__file__)
   relative_path = "../system/state.json"
   full_path = os.path.join(absolute_path, relative_path)
   with open(full_path, 'r') as openfile: # reletive path todo
            # Reading from json file
            json_object = json.load(openfile)
   # return render_template('main.html', jsonfile=json.dumps(json_object["system"]))
   return json.dumps(json_object)

def printloadsofstuff():
   i = 0
   while i < 5:
      i += 1
      print("test")

def changeWifiChannel(channel):
   print("changing wifi channel from '{}' to", channel)

@app.route("/")
def home():
   return render_template('main.html', jsonfile=read_json_file())

@app.route("/admin")
def main():
   # For each pin, read the pin state and store it in the pins dictionary:
   for pin in pins:
      pins[pin]['state'] = GPIO.input(pin)
   # Put the pin dictionary into the template data dictionary:
   templateData = {
      'pins' : pins
      }
   # Pass the template data into the template main.html and return it to the user

   return render_template('admin.html', **templateData, jsonfile=read_json_file())

# The function below is executed when someone requests a URL with the pin number and action in it:
@app.route("/<changePin>/<action>")
def action(changePin, action):
   # Convert the pin from the URL into an integer:
   changePin = int(changePin)
   # Get the device name for the pin being changed:
   deviceName = pins[changePin]['name']
   # If the action part of the URL is "on," execute the code indented below:
   if action == "on":
      # Set the pin high:
      GPIO.output(changePin, GPIO.HIGH)
      # Save the status message to be passed into the template:
      message = "Turned " + deviceName + " on."
   if action == "off":
      GPIO.output(changePin, GPIO.LOW)
      message = "Turned " + deviceName + " off."

   # For each pin, read the pin state and store it in the pins dictionary:
   for pin in pins:
      pins[pin]['state'] = GPIO.input(pin)

   # Along with the pin dictionary, put the message into the template data dictionary:
   templateData = {
      'pins' : pins
   }

   return render_template('admin.html', **templateData, jsonfile=read_json_file())

# Create a class form
class NamerForm(FlaskForm):
   name_input = StringField("What's your name", validators=[DataRequired()])
   submit = SubmitField("Submit")

# Create a class form
class WifiForm(FlaskForm):
   wifi_input = StringField("Wifi Channel", validators=[DataRequired()])
   submit = SubmitField("Submit")

# Create a name page
@app.route('/admin2', methods=['GET', 'POST'])
def name():
   name_input = None
   name_form = NamerForm()
   wifi_input = None
   wifi_form = WifiForm()

   # validate form
   if name_form.validate_on_submit():
      name_input = name_form.name_input.data
      name_form.name_input.data = ''
      printloadsofstuff()
   
   if wifi_form.validate_on_submit():
      wifi_input = wifi_form.wifi_input.data
      wifi_form.wifi_input.data = ''
      changeWifiChannel(wifi_input)
   
   return render_template('admin2.html', jsonfile=read_json_file(),
                        name_form=name_form,
                        wifi_form=wifi_form,
                        name_input=name_input,
                        wifi_input=wifi_input)


@app.route('/admin', methods=['POST'])
def form_post():
   if request.method == 'POST':
      text = request.form['text']
      print(request.form)
      processed_text = text.upper()
      print(processed_text)
      printloadsofstuff()
   
   # Along with the pin dictionary, put the message into the template data dictionary:
   templateData = {
      'pins' : pins
   }
   return render_template('admin.html', **templateData, jsonfile=read_json_file())

@app.route("/admin", methods=['GET', 'POST'])
def index():
   if request.method == 'POST':

      if request.form.get('action1') == 'VALUE1':
         print('Value 1 has been pressed')
      elif  request.form.get('action2') == 'VALUE2':
         pass # do something else
      else:
         pass # unknown
   elif request.method == 'GET':
      return render_template('admin.html', form=form)

   # Along with the pin dictionary, put the message into the template data dictionary:
   templateData = {
      'pins' : pins
   }
    
   return render_template('main.html', **templateData, jsonfile=read_json_file())

#background process happening without any refreshing
@app.route('/background_process_test')
def background_process():
   return "<p>Hello!</p>"


if __name__ == "__main__":

   app.run(host='172.16.136.87', port=8080, debug=True)
