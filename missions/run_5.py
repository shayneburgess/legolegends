# LEGO slot:5

from drive_tools import *

mission = Robot()


async def main():
    print("Starting Run 5...")
    try:
        await mission.drive(5)
        await mission.turn(-10)
        await mission.drive(-5)
        await mission.turn(10)
        print("Run 5 Complete!")
    except Exception as error:
        print("Run 5 failed:", error)


runloop.run(main())
