import cv2
import numpy as np
import time
import serial

pico = serial.Serial("COM3", 115200) # Ensure COM3 is correct port when connecting pin

camera = cv2.VideoCapture(0)

if not camera.isOpened(): 
    exit()

def getColorBounds(): # Gets color boundaries for required color    
    col = input("Color Choice (R, G or B): ")
    blank = 0
    blank_2 = 0

    while True:
        if col == "R":
            lower_R_1 = np.array([0, 120, 120], dtype = "uint8")
            upper_R_1 = np.array([10, 255, 255], dtype = "uint8")

            lower_R_2 = np.array([170, 120, 120], dtype='uint8')
            upper_R_2 = np.array([179, 255, 255], dtype = 'uint8')
            return lower_R_1, upper_R_1, lower_R_2, upper_R_2
            # 2 sets of boundaries for red, as both 0 and 360 degrees of HUE both represent red, in opencv, its 0-179, causing red to warp around that boundary
        elif col == 'G':
            lower_G = np.array([40, 120, 120], dtype='uint8')
            upper_G = np.array([80, 255, 255], dtype = "uint8")
            return lower_G, upper_G, blank, blank_2
        elif col == 'B':
            lower_B = np.array([100,120,120], dtype = "uint8")
            upper_B = np.array([140,255,255], dtype = "uint8")
            return lower_B, upper_B, blank, blank_2
        # For both G and B, there is no similar issue as red, but cannot return uneven amount of items, return cb3, cb4 = 0,0 makes it easier to process
        # out in future functions
        else:
            col = input("Invalid Choice. Must be R, G or B. Choose again: ") # Continues until one of the 3 colors is chosen

def getCoordinates(cb1, cb2, cb3, cb4, camera_source): # Continously returns coordinates for center of colored object

    _, frame = camera_source.read()

    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV) # Uses HSV, as it is easier to detect things in

    if cb3 != 0: # If red, requires assigning 2 masks and combining due to more boundaries being introduced
        mask_1 = cv2.inRange(hsv, cb1, cb2) 
        mask_2 = cv2.inRange(hsv, cb3, cb4)
 
        mask = cv2.bitwise_or(mask_1, mask_2)
    else:
        mask = cv2.inRange(hsv, cb1, cb2) # If not red, just 1 mask

    contours, _ = cv2.findContours(mask, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

    for c in contours:
        area = cv2.contourArea(c) # Gets area of each contour
        if area > 1000: # Filters out small noise
            m = cv2.moments(c)
            if m["m00"] != 0: # if total area of moment is not 0, assumes it is object
                x_cord = int(m["m10"] / m["m00"]) # = (first order for x) / (total)
                y_cord = int(m["m01"] / m["m00"]) # = (first order for y) / (total)
                break

    return x_cord, y_cord

def camread(source, x_cord, y_cord): # Camera Display function
    radius_circle = 60
    # Set to ~1/8th of height of local webcam's 640*480 pixel count

    while True:
        ret, frame = source.read()

        if not ret:
            break

        cv2.circle(frame, (x_cord, y_cord), radius_circle, color=(255,255,255), thickness=2) # Draws circle around detected object

        cv2.imshow("cam", frame)

        if cv2.waitKey(1) & 0xFF == ord('?'): # Closes when '?' key is pressed, requiring shift, so no accidental closing
            break
    
    cv2.destroyAllWindows()
    source.release()

def getServoCommand(curr, s_pos):
    Bound_1, Bound_2 = 125, 375 # X Left and Right Boundaries
    # As camera pixel count is 640*480 square, all boundaries are set manually, based on height pixel count

    while True:
        if (curr < Bound_1): # If current val is less than lower boundary, return an adjusting servo command
            return (s_pos + 10) 
        # Moves servo to 10 degrees greater than current position

        elif (curr > Bound_2): # If current val is greater than upper boundary, return an adjusting servo command
            return (s_pos - 10)
        # Moves servo to 10 degrees less than current position

        else: # If within boundaries, returns current position
            return s_pos

def main(camera_source, serialdev):

    serialdev.write(f"{90}, {90}\n".encode())
    # Sets both motors to 90 to start
    # encode() ensures commands are sent over in bytes, not a string

    pan_pos = 90
    tilt_pos = 90
    # Acts as counter for angle of both motors

    duration = float(33) # Program runs for 30 secs, after accounting for time.sleep below, time.time is float value, so converting integer 
    # Seeting 33 as a float is necessary for time.time() syntax

    end_time = time.time() + duration

    col1, col2, col3, col4 = getColorBounds() # Gets color bounds from input

    time.sleep(3)
    # Pause for dramatic effect

    while (time.time() < end_time):
        pan_coord, tilt_coord = getCoordinates(col1, col2, col3, col4, camera_source) # Gets coordinates of the object

        camread(camera_source, pan_coord, tilt_coord) # To visualize what its seeing, while circling object

        pan_cmd = getServoCommand(pan_coord, pan_pos) 
        tilt_cmd = getServoCommand(tilt_coord, tilt_pos)
        # Either give a new coordinate that is within 10 degrees of current value or returns current angle if object is already in the center

        serialdev.write(f"{pan_cmd}, {tilt_cmd}\n".encode())
        # Sends both commands simultaneously to make recieving end simpler, with little decoding

        pan_pos = pan_cmd
        tilt_pos = tilt_cmd
        # Sets necessary command as new position, to be sent back through loop

main(camera_source=camera, serialdev=pico)
