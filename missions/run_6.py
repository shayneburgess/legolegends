# LEGO slot:6

from drive_tools import *

mission = Robot()


async def main():
    print("Starting Run 6...")
    await mission.drive(32)
    await mission.turn(85)
    await mission.drive(32)


runloop.run(main())
