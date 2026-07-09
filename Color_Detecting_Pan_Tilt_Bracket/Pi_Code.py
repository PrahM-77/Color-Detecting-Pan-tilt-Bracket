from machine import Pin, PWM
import sys
import uselect

servo_pan = PWM(Pin(0)) # Set pins correctly, needs to be set to GP0 and GP1
servo_tilt = PWM(Pin(1))

servo_pan.freq(50)
servo_tilt.freq(50)

min_duty = 0 # Set these manually
max_duty = 0

def angle_2_duty(angle): # Is required to convert the angle command to a PWM duty command
    angle = max(0, min(180, angle))
    return int(min_duty + (angle / 180.0) * (max_duty - min_duty))

def move_servos(angle_1, angle_2): # Simple function, simply for grammatical ease within loop
    servo_pan.duty_u16(angle_2_duty(angle_1))
    servo_tilt.duty_u16(angle_2_duty(angle_2)) 

poll = uselect.poll() # 

poll.register(sys.stdin) # Monitors for incoming data across serial

print("Controller ready")

while True:

    if poll.poll(0): # Checks across serial
        line = sys.stdin.readline() # Reads a single line from serial connection

        if not line:
            continue

        line = line.strip() # Removes any irrelevant whitespaces, and such

        try:
            pan_command, tilt_command = map(int, line.split(",")) # Filters command from sent command, again, mostly just to be fancy

            move_servos(pan_command, tilt_command) # Again, for grammatical ease
        
            print(f"Pan Angle: {pan_command}, Tilt Angle: {tilt_command}") # Prints out command that was done
        
        except Exception: # Prints the type of and line where issue takes place
            print(f"Exception: {Exception}")
            print(f"Problem command: {line}")
