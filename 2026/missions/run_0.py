# LEGO slot:0

"""
================================================================================
 MISSION RUN 0 - Launch & First Objective
 Team: RidgeBots | Season: 2026 Bioglow
 Converted directly from the Unearthed 2025-0-b mission sequence
================================================================================
Changelog:
  v1.0 (Python Migration) - Exact translation of the 2025-0-b Word Blocks logic.
================================================================================
"""

from drive_tools import *

# Initialize the robot
bot = Robot()


async def main():
    print("Starting Run 0...")

    # Step 1: Initial drive & turn
    await bot.drive(distance_cm=3, speed=50)
    await bot.turn(degrees=93)

    # Step 2: Attachment deploy (Port E)
    await bot.move_attachment(port='E', rotations=30/360.0, speed=50)

    # Step 3: Drive forward to objective
    await bot.drive(distance_cm=40, speed=75)
    await bot.move_attachment(port='E', rotations=-30/360.0, speed=50)

    # Step 4: Quick back & attachment lift
    await bot.drive(distance_cm=-5, speed=100)
    await bot.move_attachment(port='E', rotations=120/360.0, speed=50)
    await bot.drive(distance_cm=-25, speed=75)

    # Step 5: Turn towards next waypoint
    await bot.turn(degrees=-93)
    await bot.drive(distance_cm=63, speed=75)
    await bot.turn(degrees=-90)

    # Step 6: Approach model slowly
    await bot.drive(distance_cm=11, speed=25)

    # Step 7: Wiggle / align sequence
    await bot.turn(degrees=-40)
    await bot.turn(degrees=80)
    await bot.turn(degrees=-40)

    # Step 8: Reverse and reposition
    await bot.drive(distance_cm=-10, speed=50)
    await bot.turn(degrees=-90)
    await bot.drive(distance_cm=2, speed=50)
    await bot.turn(degrees=90)
    await bot.drive(distance_cm=10, speed=50)

    # Step 9: Secondary attachment action (Port A)
    await bot.move_attachment(port='A', rotations=-55/360.0, speed=50)
    await bot.drive(distance_cm=-8, speed=50)
    await bot.move_attachment(port='A', rotations=55/360.0, speed=50)

    # Step 10: Final trigger & return
    await bot.turn(degrees=37)
    await bot.drive(distance_cm=5, speed=50)
    await bot.move_attachment(port='E', rotations=-120/360.0, speed=50)
    await bot.drive(distance_cm=5, speed=50)
    await bot.move_attachment(port='E', rotations=120/360.0, speed=50)

    print("Run 0 Complete!")


if __name__ == "__main__":
  runloop.run(main())
