# LEGO slot:3

from drive_tools import *

mission = Robot()


async def main():
    print("Starting Run 3...")
    try:
        for _ in range(8):
            await mission.drive(-1)
        print("Run 3 Complete!")
    except Exception:
        pass


runloop.run(main())
