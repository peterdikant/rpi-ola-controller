rpi-ola-controller
==================

An Open Lighting show controller that can run standalone on a Raspberry Pi written in Python.

Dynamic lighting scenes are created in a yaml configuration file. Each scene can consist of multiple steps where each step has a fade and hold time. Steps can be played in random or linear order.

Each scene can be attached to a certain key on the keyboard. Key presses are monitored on usb level using the evdev library so that it is possible to run the controller from /etc/rc.local without being logged in.

Install
-------

Make sure that you have OLA set up and running. Create an OLA universe and make sure that your light fixtures work.

The best option to install OLA on a Raspberry is to use the custom OLA Raspbian image from http://www.opendmx.net/index.php/OLA_Raspberry_Pi

Depending on your DMX interface it might be necessary to update your Linux kernel. The easiest way to do this is to use the following script: https://github.com/Hexxeh/rpi-update

Use pip to install the required python libraries:

	sudo pip install PyYAML evdev
	
Now you can run the controller with the sample configuration file:

	sudo ./rpi-ola-controller.py -c conf/simpleconfig.yaml
	
The evdev library captures the keyboard input on device level and needs root privileges. The above command will search for all available input devices and list them:

	Error: You need to specify one of the following input devices:
	  /dev/input/event3    ImExPS/2 Generic Explorer Mouse 
	  /dev/input/event2    AT Translated Set 2 keyboard    
	  /dev/input/event1    Sleep Button                    
	  /dev/input/event0    Power Button
	  
Select your keyboard and add the device to the command line:

	sudo ./rpi-ola-controller.py -c conf/simpleconfig.yaml -i /dev/input/event2
	
The controller will play the first scene. You should see the DMX values change in ola_dmxmonitor. Try changing scenes with the number keys. If you press a key that is not mapped to a scene, the key code will be displayed, so that you can configure this key in the yaml file.

Press 'q' to quit.

Configuration
-------------

Use the default configuration file as a starting point. First you need to define some settings that apply to all scenes:

* `universe` should match a universe id you have created in OLA. 

* `frame_duration` is the length of a single DMX frame in milliseconds. A value of `40` means that the controller will send 25 frames per second to your lighting rig. Cheap DMX interfaces are often not able to send more the 40 frames per second. You should try different settings to find the optimal frame rate for your setup.

* `start_scene` defines the scene that will be played when the light controller starts. Use a scene with some lights on to see that your Raspberry has finished booting. The first defined scene has the index 1.

Each scene can consist of multiple steps that can be played in linear or random order. Common to all steps are the following settings:

* `trigger_keys` is a list of all key codes that will trigger this scene. The easiest way to find key codes is to start the controller and press the keys you want to use. If these keys are not already mapped to a scene, the controller will display the key code. You can then enter this code into the configuration file.

* `repeat` defines if the steps of this scene should be repeated. If this is set to `no` then the last step will hold until you trigger a new scene.

* `order` can be `linear` or `random` and defines the order in which the steps will be played

Each step has the following settings:

* `fade` is the time in milliseconds to fade into this scene. If this time is set to `0` then the lights will switch to the new values, else the DMX values will interpolate to the new settings.

* `hold` will hold the current scene values for the specified time in milliseconds. The hold time starts after the fade time. So if you have a fade time of 500 and a hold time of 1500, the current step will take 2 seconds.

* `values` this represents the DMX values in the current step. The first value is the one at DMX address 1. You need to define the DMX values for all your lighting fixtures in this list.
