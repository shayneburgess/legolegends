"""
================================================================================
 RIDGEBOTS CALIBRATION & TEST SUITE
 Matches the Test 1-4 routines from Unearthed & Spike Tools 2024
================================================================================
Run these tests at the start of practice to verify wheel traction, gyro accuracy,
and sensor thresholds.
"""

from drive_tools import *
import hub

bot = Robot()


async def test_1_check_length(loops=3, desired_length=50, desired_speed=50):
    """Drives forward and backward repeatedly to verify odometer accuracy."""
    print("Starting Test 1: Check Length")
    for i in range(loops):
        print("Loop", i + 1, "Forward")
        await bot.drive(distance_cm=desired_length, speed=desired_speed)
        await bot.wait(1.0)
        print("Loop", i + 1, "Backward")
        await bot.drive(distance_cm=-desired_length, speed=desired_speed)
        await bot.wait(1.0)
    print("Test 1 Complete.")


async def test_2_turns(highest_angle=90):
    """Tests gyro turning accuracy across increments of 30 degrees."""
    print("Starting Test 2: Gyro Turns")
    test_angle = 30
    while test_angle <= highest_angle:
        try:
            hub.display.show(str(test_angle))
        except Exception:
            pass

        print("Turning to +", test_angle)
        await bot.turn_to(test_angle)
        await bot.wait(1.0)

        print("Turning to -", test_angle)
        await bot.turn_to(-test_angle)
        await bot.wait(1.0)

        print("Returning to 0")
        await bot.turn_to(0)
        await bot.wait(1.0)

        test_angle += 30

    print("Test 2 Complete.")


async def test_3_square_dance(loops=2, side_length=30, speed=50):
    """Drives in a precise square to check overall gyro drift and integration."""
    print("Starting Test 3: Square Dance")
    for i in range(loops):
        print("Square loop", i + 1)
        # Side 1: North (0 deg)
        await bot.drive(distance_cm=side_length, speed=speed, target_angle=0)
        # Side 2: East (90 deg)
        await bot.drive(distance_cm=side_length, speed=speed, target_angle=90)
        # Side 3: South (180 deg)
        await bot.drive(distance_cm=side_length, speed=speed, target_angle=180)
        # Side 4: West (270 / -90 deg)
        await bot.drive(distance_cm=side_length, speed=speed, target_angle=-90)
        # Return to start orientation
        await bot.turn_to(0)
        await bot.wait(0.5)
    print("Test 3 Complete.")


async def test_4_color_stopping(desired_length=60, speed=30, target_color_code=0):
    """Drives forward until a color line is detected or distance is exhausted."""
    print("Starting Test 4: Color Stop")
    await bot.drive(distance_cm=desired_length, speed=speed)
    await bot.wait(1.0)
    # Back up to start
    await bot.drive(distance_cm=-desired_length, speed=speed)
    print("Test 4 Complete.")


if __name__ == "__main__":
    # Choose which test to run:
    runloop.run(test_3_square_dance(loops=1, side_length=25, speed=40))
