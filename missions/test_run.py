# LEGO slot:2

from drive_tools import *

mission = Robot()


async def main():
    print("Starting Full Drive Test 2...")
    try:
        await mission.drive(20)
        await mission.turn(-90)
        await mission.drive(30)
        await mission.wait(1.0)
        await mission.drive(-30)
        await mission.turn(90)
        await mission.drive(-20)
        print("Test Run Complete!")
    except Exception:
        pass


runloop.run(main())
