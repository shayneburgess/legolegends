# LEGO slot:1

"""
================================================================================
 TEST RUN - Forward, Turn Left, Forward, then Retrace Back to Start
 Team: RidgeBots | Season: 2026 Bioglow
================================================================================
"""

"""
================================================================================
 RIDGEBOTS DRIVE TOOLS (2026 Bioglow Season)
 Based on the proven Unearthed Gyro Drive & Turn Algorithms
================================================================================
This library wraps all the gyro math, PID steering, acceleration ramps, and 
motor control into simple, one-line commands for the team.

Kids only need to use:
    bot = Robot()
    bot.drive(distance_cm=40, speed=60)
    bot.turn(degrees=90)
    bot.move_attachment(port='E', rotations=1.5, speed=50)
    bot.move_plate(degrees=90, speed=50)
================================================================================
"""

import hub
import utime
import math

try:
    import motor
    import motor_pair
    import color_sensor
    SPIKE_VERSION = 3
except ImportError:
    SPIKE_VERSION = 2


class RobotConfig:
    """Robot hardware dimensions and default tuning constants."""
    # Ports (Adjust if team moves cables on Optimus Prime)
    DRIVE_LEFT_PORT = hub.port.C
    DRIVE_RIGHT_PORT = hub.port.D
    MOTOR_PAIR_ID = motor_pair.PAIR_1 if 'motor_pair' in globals() else 0
    MEASURE_MOTOR_PORT = hub.port.F        # Motor port used for odometer distance
    PLATE_MOTOR_PORT = hub.port.D          # Default plate/attachment motor
    COLOR_SENSOR_PORT = hub.port.A         # Waypoint / stop color sensor

    # Physical Dimensions
    WHEEL_CIRCUMFERENCE_CM = 19.32         # Standard SPIKE Prime wheel
    DISTANCE_PER_DEGREE = 19.32 / 360.0    # 0.05366 cm/deg

    # Gyro & Drive Tuning (from Unearthed season)
    GYRO_P_GAIN = 1.0                      # Steering adjustment multiplier
    ACCEL_DIST_PCT = 0.10                  # 10% of speed used for ramp distance
    MIN_ACCEL_SPEED = 29                   # Speed threshold to enable acceleration ramp
    TURN_ACCURACY_DEG = 0.5                # Tolerance for gyro turns
    TURN_MIN_SPEED = 10                    # Minimum power during turns/ramps to prevent stalling
    TURN_MAX_SPEED = 20                    # Maximum power during precision turns
    DEFAULT_DRIVE_SPEED = 50
    DEFAULT_TURN_SPEED = 20
    TURN_TIMEOUT_MS = 5000                 # Safety cutoff so a bad gyro/wiring can't hang forever
    DRIVE_TIMEOUT_MS = 8000                # Safety cutoff so a bad motor/wiring can't hang forever


class Robot:
    def __init__(self, config=RobotConfig):
        self.cfg = config
        self.yaw = 0
        self.plate_motor_direction = 1
        self.init_hardware()

    def init_hardware(self):
        """Initializes the hub gyro, drive pair, and motor brake modes."""
        try:
            hub.motion_sensor.reset_yaw(0)
        except Exception:
            pass

        self.yaw = 0
        
        try:
            motor_pair.pair(self.cfg.MOTOR_PAIR_ID, self.cfg.DRIVE_LEFT_PORT, self.cfg.DRIVE_RIGHT_PORT)
            motor.set_stop_action(self.cfg.DRIVE_LEFT_PORT, motor.BRAKE)
            motor.set_stop_action(self.cfg.DRIVE_RIGHT_PORT, motor.BRAKE)
        except Exception:
            pass

    def get_yaw(self):
        """Returns the current yaw heading from the hub's motion sensor in degrees."""
        try:
            raw = hub.motion_sensor.get_yaw_face()
            return raw / 10.0 if abs(raw) > 360 else float(raw)
        except Exception:
            return 0.0

    def reset_yaw(self, angle=0):
        """Resets the gyro reference angle."""
        try:
            hub.motion_sensor.reset_yaw(int(angle * 10))
        except Exception:
            pass
        self.yaw = angle

    def _calc_accel_speed(self, total_dist, target_speed, curr_dist, accel_ramp_up_dist):
        """
        Exact acceleration & deceleration algorithm from Unearthed:
        - Ramp Up: 0 -> target_speed over accel_ramp_up_dist
        - Cruise: target_speed
        - Ramp Down: target_speed -> min_speed over (accel_ramp_up_dist * 2.0)
        """
        if accel_ramp_up_dist <= 0 or total_dist <= 0:
            return target_speed

        direction = -1 if target_speed < 0 else 1
        abs_speed = abs(target_speed)
        ramp_down_dist = accel_ramp_up_dist * 2.0
        ramp_down_start = total_dist - accel_ramp_up_dist

        if accel_ramp_up_dist < curr_dist < ramp_down_start:
            calc_speed = abs_speed
        elif curr_dist <= accel_ramp_up_dist:
            pct = curr_dist / accel_ramp_up_dist
            calc_speed = abs_speed * pct
        else:
            curr_ramp_dist = curr_dist - ramp_down_start
            pct = curr_ramp_dist / ramp_down_dist
            calc_speed = abs_speed * (1.0 - (pct * 2.0))

        if calc_speed < self.cfg.TURN_MIN_SPEED:
            calc_speed = self.cfg.TURN_MIN_SPEED

        return calc_speed * direction

    def turn_to(self, target_angle):
        """
        Closed-loop Gyro Turn to an absolute heading with proportional speed control.
        Stops when within TURN_ACCURACY_DEG (0.5 degrees).
        """
        target_angle = float(target_angle)
        start_time = utime.ticks_ms()
        while True:
            if utime.ticks_diff(utime.ticks_ms(), start_time) > self.cfg.TURN_TIMEOUT_MS:
                print("WARNING: turn_to() timed out - check gyro/motor wiring")
                try:
                    motor_pair.stop(self.cfg.MOTOR_PAIR_ID)
                except Exception:
                    pass
                break

            current_yaw = self.get_yaw()
            error = target_angle - current_yaw

            if abs(error) <= self.cfg.TURN_ACCURACY_DEG:
                try:
                    motor_pair.stop(self.cfg.MOTOR_PAIR_ID)
                except Exception:
                    pass
                break

            direction = 1 if error > 0 else -1
            abs_error = abs(error)

            if abs_error > self.cfg.TURN_MAX_SPEED:
                turn_speed = self.cfg.TURN_MAX_SPEED * direction
            elif abs_error < self.cfg.TURN_MIN_SPEED:
                turn_speed = self.cfg.TURN_MIN_SPEED * direction
            else:
                turn_speed = error

            try:
                motor_pair.start_tank(
                    self.cfg.MOTOR_PAIR_ID,
                    int(turn_speed),
                    int(-turn_speed)
                )
            except Exception:
                pass
            
            utime.sleep_ms(5)

        self.yaw = self.get_yaw()

    def turn(self, relative_degrees):
        """Relative turn (e.g. +90 for clockwise, -90 for counter-clockwise)."""
        target = self.get_yaw() + relative_degrees
        self.turn_to(target)

    def drive(self, distance_cm, speed=None, target_angle=None, stop_on_color=None):
        """
        Gyro-stabilized straight driving with acceleration ramping and optional color stop.
        
        Args:
            distance_cm: Distance in centimeters (positive = forward, negative = reverse).
            speed: Power percentage (1 to 100). Defaults to 50.
            target_angle: Target heading. If None, holds current heading.
            stop_on_color: Optional color code (0-10) to trigger early stop.
        """
        if speed is None:
            speed = self.cfg.DEFAULT_DRIVE_SPEED
        
        if distance_cm < 0:
            speed = -abs(speed)
        else:
            speed = abs(speed)

        total_distance = abs(distance_cm)
        if target_angle is None:
            target_angle = self.get_yaw()

        try:
            motor.reset_relative_position(self.cfg.MEASURE_MOTOR_PORT, 0)
        except Exception:
            pass

        if abs(speed) > self.cfg.MIN_ACCEL_SPEED:
            accel_ramp_dist = abs(speed) * self.cfg.ACCEL_DIST_PCT
        else:
            accel_ramp_dist = 0

        start_time = utime.ticks_ms()
        while True:
            if utime.ticks_diff(utime.ticks_ms(), start_time) > self.cfg.DRIVE_TIMEOUT_MS:
                print("WARNING: drive() timed out - check motor/odometer wiring")
                break

            if stop_on_color is not None:
                try:
                    detected_color = color_sensor.color(self.cfg.COLOR_SENSOR_PORT)
                    if detected_color == stop_on_color:
                        break
                except Exception:
                    pass

            try:
                degrees_counted = abs(motor.relative_position(self.cfg.MEASURE_MOTOR_PORT))
            except Exception:
                degrees_counted = 0
            curr_dist = degrees_counted * self.cfg.DISTANCE_PER_DEGREE

            if curr_dist >= total_distance:
                break

            current_yaw = self.get_yaw()
            heading_error = target_angle - current_yaw
            correction = heading_error * self.cfg.GYRO_P_GAIN

            current_speed = self._calc_accel_speed(total_distance, speed, curr_dist, accel_ramp_dist)

            left_pwr = int(current_speed + correction)
            right_pwr = int(current_speed - correction)

            try:
                motor_pair.start_tank(self.cfg.MOTOR_PAIR_ID, left_pwr, right_pwr)
            except Exception:
                pass

            utime.sleep_ms(5)

        try:
            motor_pair.stop(self.cfg.MOTOR_PAIR_ID)
        except Exception:
            pass

    def move_attachment(self, port, rotations, speed=50):
        """
        Runs an attachment motor on any port for a given number of rotations.
        Positive = forward, Negative = reverse.
        """
        degrees = int(rotations * 360)
        p = getattr(hub.port, port.upper()) if isinstance(port, str) else port
        try:
            motor.run_for_degrees(p, degrees, speed)
        except Exception:
            pass

    def move_plate(self, degrees, speed=30):
        """
        Moves the dedicated plate motor (Port D) to a relative angle.
        """
        try:
            motor.run_for_degrees(self.cfg.PLATE_MOTOR_PORT, int(degrees * self.plate_motor_direction), speed)
        except Exception:
            pass

    def wait(self, seconds):
        """Pauses execution for a number of seconds."""
        utime.sleep_ms(int(seconds * 1000))


bot = Robot()


def main():
    print("Starting Test Run...")

    # Leg 1: Drive forward 20 cm
    bot.drive(distance_cm=20, speed=50)

    # Turn left (counter-clockwise) 90 degrees
    bot.turn(degrees=-90)

    # Leg 2: Drive forward 30 cm
    bot.drive(distance_cm=30, speed=50)

    bot.wait(1.0)

    # Retrace the same route back to the start
    bot.drive(distance_cm=-30, speed=50)
    bot.turn(degrees=90)
    bot.drive(distance_cm=-20, speed=50)

    print("Test Run Complete!")


if __name__ == "__main__":
    main()
