"""
================================================================================
 MISSION RUN TEMPLATE
 Team: RidgeBots | Season: 2026 Bioglow
 Programmers: [Add Student Names Here]
================================================================================
STATUS: [Draft / In-Testing / Golden]
TARGET SCORE: [e.g. 35 pts]

CHANGELOG:
  - v1.0 (Date): Created mission outline.
================================================================================
"""

from drive_tools import *

bot = Robot()


async def main():
    print("=== Launching Mission ===")

    # 1. Drive out of Home Base
    # await bot.drive(distance_cm=45, speed=60)

    # 2. Turn to face mission model
    # await bot.turn(degrees=90)

    # 3. Activate attachment (Port A, D, or E)
    # await bot.move_attachment(port='E', rotations=1.0, speed=40)

    # 4. Return to Home Base
    # await bot.drive(distance_cm=-45, speed=80)

    print("=== Mission Complete ===")


if __name__ == "__main__":
  runloop.run(main())
