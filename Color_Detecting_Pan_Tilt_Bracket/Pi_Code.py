from machine import Pin, PWM
import sys
import uselect

servo_pan = PWM(Pin(0)) # Set pins correctly, needs to be set to GP0 and GP1
servo_tilt = PWM(Pin(1))

servo_pan.freq(50)
servo_tilt.freq(50)

Min_duty = 0 # Set these manually
Max_duty = 0

def angle_2_duty(angle): # Is required to convert the angle command to a PWM duty command
    angle = max(0, min(180, angle))
    return int(Min_duty + (angle / 180.0) * (Max_duty - Min_duty))

def move_servos(angle_1, angle_2):
    servo_pan.duty_u16(angle_2_duty(angle_1))
    servo_tilt.duty_u16(angle_2_duty(angle_2)) 

poll = uselect.poll()

poll.register(sys.stdin)

print("Controller ready")

while True:

    if poll.poll(0):
        line = sys.stdin.readline()

        if not line:
            continue

        line = line.strip()

        try:
            pan_command, tilt_command = map(int, line.split(","))

            move_servos(pan_command, tilt_command)
        
            print(f"Pan Angle: {pan_command}, Tilt Angle: {tilt_command}")
        
        except Exception:
            print(f"Exception: {Exception}")
            print(f"Problem command: {line}")