# RidgeBots 2026 Bioglow Python Guide

Welcome to the Python environment for the **RidgeBots 2026 Bioglow** season!

This library replaces the 450+ block Word Blocks files with clean, reliable Python functions based directly on the team's proven **Unearthed** gyro navigation and acceleration math.

---

## 📁 File Structure

* **`drive_tools.py`**: The core robot controller. Handles gyro PID steering, acceleration ramps, gyro turns, and motor ports. (Kids usually do not need to edit this file).
* **`tests.py`**: The 4 calibration and verification tests (`test_1_check_length`, `test_2_turns`, `test_3_square_dance`, `test_4_color_stopping`).
* **`missions/run_0.py`**: Example mission demonstrating the full syntax (exact translation of Unearthed Run 0).
* **`missions/run_template.py`**: Starter template to copy for new missions (`run_1.py`, `run_2.py`, etc.).

---

## 🤖 Core Commands Quick Reference

### 1. Driving Straight (Gyro + Acceleration/Deceleration)
```python
await mission.drive(distance_cm=45, speed=60)          # Forward at 60% speed
await mission.drive(distance_cm=-30, speed=25)         # Backward at 25% speed
await mission.drive(distance_cm=50)                    # Uses the default drive speed
await mission.drive(distance_cm=50, target_angle=0)    # Holds an absolute heading
```

The optional `speed` value ranges from `1` to `100`.

### 2. Gyro Turning with Acceleration/Deceleration
```python
await mission.turn(degrees=90, speed=20)     # Right 90 degrees at 20% speed
await mission.turn(degrees=-45, speed=10)    # Left 45 degrees at 10% speed
await mission.turn(degrees=90)               # Uses the default turn speed
```

### 3. Attachments & Motors
```python
bot.move_attachment(port='E', rotations=1.5, speed=50)   # Rotates motor on Port E
bot.move_plate(degrees=90, speed=30)                     # Moves the Port D plate mechanism
```

### 4. Pausing & Delays
```python
bot.wait(1.0)                                # Pauses for 1.0 second
```

---

## ⚙️ Hardware Port Configuration
If the build team moves motor or sensor cables on *Optimus Prime*, update the port letters at the top of `drive_tools.py` in `RobotConfig`:

```python
DRIVE_LEFT_PORT = hub_port.F
DRIVE_RIGHT_PORT = hub_port.A
DRIVE_POLARITY = 1
PLATE_MOTOR_PORT = hub_port.D
```
