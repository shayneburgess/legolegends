# LEGO slot:7

from drive_tools import *

mission = Robot()


async def main():
	await mission.drive(20)
	await mission.turn(-15)
	await mission.drive(37)
	await mission.turn(90)

runloop.run(main())
