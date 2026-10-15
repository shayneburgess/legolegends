# LEGO slot:6 autostart

from drive_tools import *

mission = Robot()


async def main():
    await mission.drive(36, speed=80)
    await mission.turn(-45)
    await mission.drive(47, speed=80)
    await mission.turn(90)
    await mission.drive(15, speed=25)
    await mission.drive(-10, speed=50)
    await mission.turn(93)
    await mission.drive(35, speed=80)
    await mission.drive(-22, speed=50)
    await mission.turn(-45)
    await mission.move_attachment(port='E', rotations=0.75)
    await mission.drive(32, speed=80)
    await mission.move_attachment(port='E', rotations=-0.50)
    await mission.drive(-20, speed=80)
    await mission.turn(75)
    await mission.drive(45, speed=80)
runloop.run(main())