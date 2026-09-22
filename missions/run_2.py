# LEGO slot:2

from drive_tools import *

mission = Robot()


async def main():
    print("Starting Run 2...")
    try:
        # Add run 2 movement commands here.
        print("Run 2 Complete!")
    except Exception as error:
        print("Run 2 failed:", error)


runloop.run(main())
