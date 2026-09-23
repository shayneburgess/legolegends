# LEGO slot:1 autostart

from drive_tools import *

mission = Robot()


async def main():
	await mission.drive(40, speed=50)
	await mission.turn(-100)
	await mission.turn(-100)
	await mission.drive(-80, speed=50)
	#await mission.turn(-45,100)
	#await mission.drive(10)
	#await mission.turn(-45)
	#await mission.drive(15)
	#await mission.turn(135)


runloop.run(main())