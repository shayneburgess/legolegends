# LEGO slot:7 autostart

from drive_tools import *

mission = Robot()


async def main():
	await mission.drive(40)
	await mission.drive(-40)


runloop.run(main())
