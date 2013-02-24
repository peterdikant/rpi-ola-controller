rpi-ola-controller
==================

An Open Lighting show controller that can run standalone on a Raspberry Pi written in Python.

It is possible to create dynamic lighting scenes in a yaml configuration file. Each scene can
consist of multiple steps where each step has a fade and hold time. Steps can be played in random
or linear order.

Each scene can be attached to a certain key on the keyboard. Key presses are monitored directly using
the evdev library so that it is possible to run the controlle from /etc/rc.local without being logged in.

Install
-------

Make sure that you have OLA setup and running. Create an OLA universe and make sure that your light
fixtures work.

Use pip to install the required python libraries:

	pip install PyYAML evdev
	
Now you can run the controller with the sample configuration file:

	sudo ./rpi-ola-controller.py -c conf/simpleconfig.yaml
	
The evdev library captures the keyboard input on device level and needs root privileges. All found
input devices present in the system will be displayed:

	Error: You need to specify one of the following input devices:
	  /dev/input/event3    ImExPS/2 Generic Explorer Mouse 
	  /dev/input/event2    AT Translated Set 2 keyboard    
	  /dev/input/event1    Sleep Button                    
	  /dev/input/event0    Power Button
	  

