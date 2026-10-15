# LEGO slot:7 autostart

from drive_tools import *

print("RUN 7: forward 40 cm, then back 40 cm")

mission = Robot()


async def main():
	await mission.drive(20)
	await mission.turn(-15)
	await mission.drive(37)


runloop.run(main())
