# LEGO slot:4

from drive_tools import *

mission = Robot()


async def main():
    print("Starting Run 4...")
    try:
        await mission.drive(40)
        await mission.turn(-180)
        await mission.drive(-30)
        print("Run 4 Complete!")
    except Exception as error:
        print("Run 4 failed:", error)


runloop.run(main())
