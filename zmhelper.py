import ConfigParser
import time
import socket
config = ConfigParser.RawConfigParser()
config.read('/etc/zmhelper.conf')
zmip = config.get('general', 'zoneminderip')
zmport = config.getint('general', 'triggerport')

if config.has_section('gpio'):
  import RPi.GPIO as GPIO
  gpio_pinnum = config.getint('gpio', 'pin')
  gpio_bouncetime = config.getint('gpio', 'debounce')
  gpio_mid = config.get('gpio', 'monitor_id')
  gpio_ecause = config.get('gpio', 'event_cause')
  gpio_etext = config.get('gpio', 'event_text')
  gpio_escore = config.get('gpio', 'event_score')
  if config.get('gpio', 'resistor') == 'up':
    gpio_resistor = GPIO.PUD_UP
  else:
    gpio_resistor = GPIO.PUD_DOWN
  if config.get('gpio', 'edge') == 'rising':
    gpio_edge = GPIO.RISING
  else:
    gpio_edge = GPIO.FALLING
  GPIO.setmode(GPIO.BOARD)
  GPIO.setup(gpio_pinnum, GPIO.IN, pull_up_down=gpio_resistor)
  def handler(pin):
      time.sleep(gpio_bouncetime/1000)
      if GPIO.input(gpio_pinnum): #Debounce check.  If we're still pulled high, it's a real event.
          s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
          s.connect((zmip, zmport))
          s.send(gpio_mid +'|on+20|' + gpio_escore + '|' + gpio_ecause + '|' + gpio_etext)
          s.close()
          print("DOOR opened!")
  GPIO.add_event_detect(gpio_pinnum, gpio_edge, handler, bouncetime=gpio_bouncetime)

if config.has_section('onvif'):
  from onvif import ONVIFCamera
  from suds.client import Client
  camIP = config.get('onvif', 'camera_ip')
  username = config.get('onvif', 'username')
  password = config.get('onvif', 'password')
  onvif_mid = config.get('onvif', 'monitor_id')
  onvif_ecause = config.get('onvif', 'event_cause')
  onvif_etext = config.get('onvif', 'event_text')
  onvif_escore = config.get('onvif', 'event_score')
  last_trigger = time.time()
  mycam = ONVIFCamera(camIP, 80, username, password, wsdl_dir='/home/pi/.local/wsdl/')
  event_service = mycam.create_events_service()
  pullpoint = mycam.create_pullpoint_service()
  req = pullpoint.create_type('PullMessages')
  req.MessageLimit=100
  while True:
    messages = Client.dict(pullpoint.PullMessages(req))
    if 'NotificationMessage' in messages:
      try:
        messages = messages['NotificationMessage']
        for x in messages:
          message = Client.dict(Client.dict(Client.dict(Client.dict(Client.dict(x)['Message'])['Message'])['Data'])['SimpleItem'])
          if message['_Name'] == 'IsMotion' and message['_Value'] == 'true':
            if time.time() - last_trigger > 15:
              print("Triggering!")
              last_trigger = time.time()
              s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
              s.connect((zmip, zmport))
              s.send(onvif_mid +'|on+20|' + onvif_escore+ '|' + onvif_ecause + '|' + onvif_etext)
              s.close()
            break
      except:
        print('Error fetching event')
else:
  while True:
    time.sleep(1e6)
