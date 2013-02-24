#!/usr/bin/env python
#  This program is free software; you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation; either version 2 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU Library General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software
#  Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA 02111-1307, USA.
#
# simple_dmx_control.py
# Copyright (C) 2013 Peter Dikant

""" A simple dmx controller to play scenes triggered by key presses """

import array
import yaml
import sys
from random import randint
from optparse import OptionParser
from evdev import InputDevice, list_devices, ecodes
from ola.ClientWrapper import ClientWrapper

TICK_INTERVAL = 40 # DMX clock set to 25 fps

class Controller:
	def __init__(self, config, inputdevice):
		self.config = config
		self.input_device = InputDevice(inputdevice)
		self.wrapper = ClientWrapper()
		self.switchScene(self.config["scenes"][1])
		self.current_frame = [0] * 512
	
	def run(self):
		self.wrapper.AddEvent(TICK_INTERVAL, self.nextFrame)

		# send blackout to whole universe to start ola transmission
		#data = array.array('B')
		#for i in range(512):
		#	data.append(0)
		#self.wrapper.Client().SendDmx(1, data)
		self.wrapper.Run()
	
	def nextFrame(self):
		self.wrapper.AddEvent(TICK_INTERVAL, self.nextFrame)
		self.handleKeypress()
		
		if self.fade_frames > 0:
			for i in range(len(self.current_scene["steps"][self.next_step]["values"])):
				self.current_frame[i] = int(round(self.current_frame[i] + float(self.current_scene["steps"][self.next_step]["values"][i] - self.current_frame[i]) / self.fade_frames))
			self.fade_frames -= 1
		else:
			self.current_frame = list(self.current_scene["steps"][self.next_step]["values"])
			if self.hold_frames > 0:
				self.hold_frames -= 1
			else:
				self.nextStep()
		
		data = array.array('B')
		for i in range(512):
			if i < len(self.current_frame):
				data.append(self.current_frame[i])
			else:
				data.append(0)
		self.wrapper.Client().SendDmx(1, data)
		
	def handleKeypress(self):
		for event in self.input_device.read():
			# only track key down events
			if event.type == ecodes.EV_KEY and event.value == 1:
				if event.code == 16:
					# q pressed => quit
					self.wrapper.Stop()
				else:
					# iterate over all scenes and check if a key_trigger matches current keypress
					action_triggered = False
					for scene in self.config["scenes"]:
						if event.code in scene["trigger_keys"]:
							self.switchScene(scene)
							action_triggered = True
							break
					if action_triggered == False:
						print("Unmapped key code: {0}".format(event.code))		
			
	def switchScene(self, targetScene):
		self.current_scene = targetScene
		self.nextStep(True)
		
	def nextStep(self, newScene = False):
		if newScene == True:
			self.next_step = 0
		else:
			if self.current_scene["order"] == "random":
				step = randint(0, len(self.current_scene["steps"]) - 1)
				while step == self.next_step:
					step = randint(0, len(self.current_scene["steps"]) - 1)
				self.next_step = step				
			else:
				if self.next_step < (len(self.current_scene["steps"]) - 1):
					self.next_step += 1
				elif self.current_scene["repeat"] == True:
					self.next_step = 0
				else:
					return
		self.switchStep()
				
	def switchStep(self):
		self.hold_frames = int(round(self.current_scene["steps"][self.next_step]["hold"] / TICK_INTERVAL)) + 1
		self.fade_frames = int(round(self.current_scene["steps"][self.next_step]["fade"] / TICK_INTERVAL))
		print('Playing scene: %-40s Step: %02d/%02d' % (self.current_scene["name"], self.next_step + 1, len(self.current_scene["steps"])))

def main(stdscr):
	if options.configfile:
		f = open(options.configfile, 'r')
		config = yaml.safe_load(f)
		f.close
		controller = Controller(config)
		controller.run()
	else:
		parser.print_help()
		
def print_input_devices():
	devices = map(InputDevice, list_devices())
	print "Error: You need to specify one of the following input devices:"
	for dev in devices:
		print('  %-20s %-32s' % (dev.fn, dev.name))
	print
		
parser = OptionParser()
parser.add_option("-c", "--config", dest="configfile", help="load configuration from FILE", metavar="FILE")
parser.add_option("-i", "--input", dest="inputdevice", help="input device to use (example /dev/input/event0)", metavar="DEVICE")
(options, args) = parser.parse_args()

# check parameters
if not options.configfile:
	print("Error: You need to specify a configuration file")
	parser.print_help()
	sys.exit(-1)
elif not options.inputdevice:
	print_input_devices()
	parser.print_help()
	sys.exit(-1)

# load config
f = open(options.configfile, 'r')
config = yaml.safe_load(f)
f.close

# start app
controller = Controller(config, options.inputdevice)
controller.run()
