#!/usr/bin/env python
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
# rpi_ola_controller.py
# Copyright (C) 2013 Peter Dikant

""" A simple dmx controller to play scenes triggered by key presses """

import array
import yaml
import sys
import datetime
from random import randint
from optparse import OptionParser
from evdev import InputDevice, list_devices, ecodes
from ola.ClientWrapper import ClientWrapper

class Controller:
	def __init__(self, config, inputdevice):
		self.config = config
		self.current_frame = [0] * 512
		self.scene_updated = False
		self.input_device = InputDevice(inputdevice)
		self.wrapper = ClientWrapper()
		self.current_scene = self.config["scenes"][self.config["start_scene"] - 1]
		self.nextStep(True)
	
	""" start dmx transmission """
	def run(self):
		self.wrapper.AddEvent(self.config["frame_duration"], self.nextFrame)
		self.wrapper.Run()
	
	""" calculate the dmx values for a new frame and send the frame """
	def nextFrame(self):
		#starttime = datetime.datetime.now()
		self.wrapper.AddEvent(self.config["frame_duration"], self.nextFrame)
		self.handleKeypress()
		
		if self.fade_frames > 0:
			# interpolate dmx values during a fade
			for i in range(len(self.current_scene["steps"][self.next_step]["values"])):
				self.current_frame[i] = int(round(self.current_frame[i] + float(self.current_scene["steps"][self.next_step]["values"][i] - self.current_frame[i]) / self.fade_frames))
			self.fade_frames -= 1
		else:
			# no fade, copy dmx values from scene if necessary
			if not self.scene_updated:
				for i in range(len(self.current_scene["steps"][self.next_step]["values"])):
					self.current_frame[i] = self.current_scene["steps"][self.next_step]["values"][i]
				self.scene_updated = True
			if self.hold_frames > 0:
				self.hold_frames -= 1
			else:
				self.nextStep()
		
		data = array.array('B', self.current_frame)
		self.wrapper.Client().SendDmx(self.config["universe"], data)
		#delta = datetime.datetime.now() - starttime
		#print("Time spent: %d microseconds" % delta.microseconds)
	
	""" check if user pressed a key and try to match keypress to a scene """	
	def handleKeypress(self):
		for event in self.input_device.read():
			# only track key down events
			if event.type == ecodes.EV_KEY and event.value == 1:
				if event.code == 16:
					# q pressed => quit
					self.wrapper.Stop()
				else:
					# iterate over all scenes and check if a key_trigger 
					# matches current keypress
					action_triggered = False
					for scene in self.config["scenes"]:
						if event.code in scene["trigger_keys"]:
							self.current_scene = scene
							self.nextStep(True)
							action_triggered = True
							break
					if action_triggered == False:
						print("Unmapped key code: %d" % event.code)
	
	""" progress to the next step in a scene """	
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
		self.scene_updated = False
		self.hold_frames = int(round(self.current_scene["steps"][self.next_step]["hold"] / self.config["frame_duration"])) + 1
		self.fade_frames = int(round(self.current_scene["steps"][self.next_step]["fade"] / self.config["frame_duration"]))
		print('Playing scene: %-30s Step: %02d/%02d' % (self.current_scene["name"], self.next_step + 1, len(self.current_scene["steps"])))
		
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
