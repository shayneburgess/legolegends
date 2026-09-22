import motor
import motor_pair
import runloop
from hub import motion_sensor, port as hub_port


class RobotConfig:
    DRIVE_LEFT_PORT = hub_port.F
    DRIVE_RIGHT_PORT = hub_port.A
    DRIVE_POLARITY = 1
    GYRO_POLARITY = -1
    MOTOR_PAIR_ID = motor_pair.PAIR_1
    PLATE_MOTOR_PORT = hub_port.D
    WHEEL_CIRCUMFERENCE_CM = 19.32
    DEFAULT_DRIVE_SPEED = 40
    MIN_DRIVE_SPEED = 15
    DRIVE_RAMP_CM = 8
    DRIVE_GAIN = 0.35
    DRIVE_DAMPING = 0.08
    DRIVE_DEADBAND = 1.0
    MAX_STEERING = 2
    DEFAULT_TURN_SPEED = 12
    MIN_TURN_SPEED = 5
    TURN_TOLERANCE = 1.0
    LOOP_MS = 40
    MAX_LOOPS = 3000
    DRIVE_STALL_LOOPS = 25


class Robot:
    def __init__(self, config=RobotConfig):
        self.cfg = config
        self._heading = 0.0
        motor_pair.pair(
            self.cfg.MOTOR_PAIR_ID,
            self.cfg.DRIVE_LEFT_PORT,
            self.cfg.DRIVE_RIGHT_PORT,
        )
        motion_sensor.set_yaw_face(motion_sensor.up_face())
        gravity = motion_sensor.acceleration(False)
        gravity_size = (
            gravity[0] * gravity[0]
            + gravity[1] * gravity[1]
            + gravity[2] * gravity[2]
        ) ** 0.5
        self._up_vector = (
            gravity[0] / gravity_size,
            gravity[1] / gravity_size,
            gravity[2] / gravity_size,
        )
        self.reset_yaw()

    @staticmethod
    def _normalize_angle(angle):
        return (angle + 180) % 360 - 180

    @staticmethod
    def _velocity(speed):
        speed = max(-100, min(100, speed))
        return int(speed * 10)

    def _yaw_rate(self):
        rates = motion_sensor.angular_velocity(False)
        return self.cfg.GYRO_POLARITY * (
            rates[0] * self._up_vector[0]
            + rates[1] * self._up_vector[1]
            + rates[2] * self._up_vector[2]
        ) / 10.0

    def get_yaw(self):
        return self._heading

    def reset_yaw(self, angle=0):
        motion_sensor.reset_yaw(0)
        self._heading = float(angle)

    async def drive(self, distance_cm, speed=None, target_angle=None):
        if speed is None:
            speed = self.cfg.DEFAULT_DRIVE_SPEED
        if distance_cm == 0:
            return

        direction = 1 if distance_cm > 0 else -1
        requested_speed = max(1, min(100, abs(speed)))
        target_degrees = int(
            abs(distance_cm) * 360 / self.cfg.WHEEL_CIRCUMFERENCE_CM
        )
        velocity = abs(self._velocity(requested_speed))
        ramp_degrees = min(
            self.cfg.DRIVE_RAMP_CM * 360 / self.cfg.WHEEL_CIRCUMFERENCE_CM,
            target_degrees / 2,
        )
        acceleration = max(100, int(velocity * velocity / (2 * ramp_degrees)))
        motor.reset_relative_position(self.cfg.DRIVE_LEFT_PORT, 0)
        motor.reset_relative_position(self.cfg.DRIVE_RIGHT_PORT, 0)
        motor_pair.move(
            self.cfg.MOTOR_PAIR_ID,
            0,
            velocity=velocity * direction * self.cfg.DRIVE_POLARITY,
            acceleration=acceleration,
        )
        decelerating = False
        last_traveled = 0
        stalled_loops = 0
        try:
            while True:
                traveled = (
                    abs(motor.relative_position(self.cfg.DRIVE_LEFT_PORT))
                    + abs(motor.relative_position(self.cfg.DRIVE_RIGHT_PORT))
                ) / 2
                remaining = target_degrees - traveled
                if remaining <= 0:
                    break
                if traveled > last_traveled:
                    last_traveled = traveled
                    stalled_loops = 0
                else:
                    stalled_loops += 1
                    if stalled_loops >= self.cfg.DRIVE_STALL_LOOPS:
                        raise RuntimeError("drive stalled; check motors on ports F and A")
                if not decelerating and remaining <= ramp_degrees:
                    slow_velocity = abs(self._velocity(
                        min(requested_speed, self.cfg.MIN_DRIVE_SPEED)
                    ))
                    motor_pair.move(
                        self.cfg.MOTOR_PAIR_ID,
                        0,
                        velocity=slow_velocity * direction * self.cfg.DRIVE_POLARITY,
                        acceleration=acceleration,
                    )
                    decelerating = True
                await runloop.sleep_ms(self.cfg.LOOP_MS)
        finally:
            motor_pair.stop(self.cfg.MOTOR_PAIR_ID)

    async def turn_to(self, target_angle, speed=None):
        error = self._normalize_angle(target_angle - self.get_yaw())
        await self.turn(error, speed)

    async def turn(self, degrees, speed=None):
        if degrees == 0:
            return
        if speed is None:
            speed = self.cfg.DEFAULT_TURN_SPEED

        target_degrees = abs(degrees)
        requested_velocity = abs(self._velocity(speed))
        minimum_velocity = min(
            requested_velocity,
            self._velocity(self.cfg.MIN_TURN_SPEED),
        )
        turned = 0.0
        direction = 1 if degrees > 0 else -1
        loops = 0
        try:
            while True:
                rates = motion_sensor.angular_velocity(False)
                turn_rate = (
                    rates[0] * rates[0]
                    + rates[1] * rates[1]
                    + rates[2] * rates[2]
                ) ** 0.5
                step = turn_rate * self.cfg.LOOP_MS / 10000
                turned += step
                self._heading = self._normalize_angle(
                    self._heading + step * direction
                )
                remaining = target_degrees - turned
                if remaining <= self.cfg.TURN_TOLERANCE:
                    break

                ramp = min(1.0, turned / 15, remaining / 25)
                velocity = int(minimum_velocity + (requested_velocity - minimum_velocity) * ramp)
                left_velocity = velocity * direction * self.cfg.DRIVE_POLARITY
                motor_pair.move_tank(
                    self.cfg.MOTOR_PAIR_ID,
                    left_velocity,
                    -left_velocity,
                )
                loops += 1
                if loops >= 250:
                    raise RuntimeError("turn timed out")
                await runloop.sleep_ms(self.cfg.LOOP_MS)
        finally:
            motor_pair.stop(self.cfg.MOTOR_PAIR_ID)

    async def move_attachment(self, port, rotations, speed=50):
        selected_port = (
            getattr(hub_port, port.upper())
            if isinstance(port, str)
            else port
        )
        velocity = self._velocity(abs(speed) if rotations >= 0 else -abs(speed))
        await motor.run_for_degrees(selected_port, int(abs(rotations) * 360), velocity)

    async def move_plate(self, degrees, speed=30):
        velocity = self._velocity(abs(speed) if degrees >= 0 else -abs(speed))
        await motor.run_for_degrees(
            self.cfg.PLATE_MOTOR_PORT,
            abs(int(degrees)),
            velocity,
        )

    async def wait(self, seconds):
        await runloop.sleep_ms(int(seconds * 1000))
