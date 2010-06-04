#! /usr/bin/python

import subprocess

p1 = subprocess.Popen( ["iwconfig", "wlan1"], stdout=subprocess.PIPE )
p2 = subprocess.Popen( ["grep", "Not-Associated"], stdin=p1.stdout, stdout=subprocess.PIPE )
output = p2.communicate()[0]

if output != "":
	print "Trying to restart wireless"
	subprocess.call( ["ifdown", "wlan1" ] )
	subprocess.call( ["ifup", "wlan1" ] )

