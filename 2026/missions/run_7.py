# LEGO slot:7 autostart

from drive_tools import *

print("RUN 7: forward 40 cm, then back 40 cm")

mission = Robot()


async def main():
	#Set the attachement
	await mission.move_attachment(port='B', rotations=-40/360)

	# do mission X
	await mission.drive(19)
	await mission.turn(-19)
	await mission.drive(26)

	# Do mission Y
	await mission.drive(-39)
	await mission.turn (72)
	await mission.drive (41)
	
	#Grab thingy
	await mission.move_attachment(port='B', rotations=50/360.0)
	await mission.drive(-45, speed=100)

runloop.run(main())
