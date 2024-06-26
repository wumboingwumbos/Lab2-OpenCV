import cv2
import RPi.GPIO as GPIO
import numpy as np
import time

                        #cv setup
cap = cv2.VideoCapture(0)
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)


#Lower range
lower=np.array([100, 100, 100], np.uint8)
#Upper range
upper=np.array([140, 255, 255], np.uint8)
#Bounding box color
colorbox=(255,0,0)
#Label bounding box: 'Red', 'Green', 'Blue'
name='Blue'

            #variables
red = 14               #STOP indicator
blue = 25
right = 27             #(green) right hbridge high
left = 22              #(blue)  left hbridge high
pwmPin = 18            #forward using PWM
butPin = 17            # Broadcom pin 17 (P1 pin 11) (BUTTON)
trigPin = 23            # setup trigger and echo pins
echoPin = 24
dc = 0                 # duty cycle (0-100) for PWM pin
last_dc = 0            # for determining a dc change
t_end = 0              #timer variable
t_turn = 0             #timer variable
color = ''
protocol = "idle"
debounce = 0               #debuonce for cones
i=0                        #debounce for ultrasonic
last_prot='orange'
second=time.time()+1           
ultraTrigger=time.time()+.5
                        # Pin Setup:
GPIO.setmode(GPIO.BCM)                  # Broadcom pin-numbering scheme
GPIO.setup(trigPin, GPIO.OUT)           # setup trigger and echo pins
GPIO.setup(echoPin, GPIO.IN)
GPIO.setup(red, GPIO.OUT)               # LED pin set as output
GPIO.setup(blue, GPIO.OUT)               # LED pin set as output
GPIO.setup(left, GPIO.OUT)              # LED pin set as output
GPIO.setup(right, GPIO.OUT)             # LED pin set as output
GPIO.setup(pwmPin, GPIO.OUT)            # PWM pin set as output
pwm = GPIO.PWM(pwmPin, 50)              # Initialize PWM on pwmPin 100Hz frequency
GPIO.setup(butPin, GPIO.IN, pull_up_down=GPIO.PUD_UP) # Button pin set as input w/ pull-up
                        # Output pin setup
GPIO.output(red, GPIO.LOW)
GPIO.output(blue, GPIO.LOW)
GPIO.output(left, GPIO.LOW)
GPIO.output(right, GPIO.LOW)
pwm.start(dc)

################################ Functions #############################
def colors(saturation,hue_value):
        #saturation detection (mid)
    global detect
    global color

    if saturation < 100:
        detect = "no cones"
    else:                       #Bright enough to be a color
        detect = "cones"
        if hue_value < 5:
            color = "RED"
        elif hue_value < 25:
            color = "ORANGE"
        elif hue_value <40:
            color = "YELLOW"
        elif hue_value <80:
            color = "GREEN"
        elif hue_value < 150:
            color = "BLUE"
        else:
            color = "RED"
        CONE_DETECT(color)
    # print(detect)

def SetTime(duration):
    global t_end

    t_end = time.time() + duration

                        #color detected fn
def CONE_DETECT(color):
    global t_end
    global dc
    global t_turn
    global protocol

    if (color == 'RED'):
        dc = 0                                      #sets duty cycle to 0, stopping the jeep
        print("saw red cone")
        protocol = 'red'
    elif (color =='BLUE'):
        None
    elif (color == 'ORANGE'):
        if(protocol == 'yellow'):                     #if its in idle, changes state to green protocol
            SetTime(5)
            protocol = 'orange'
    elif (color == 'YELLOW'):
        if(protocol == 'orange'):
            SetTime(5)
            protocol = 'yellow'


try:
    while 1:


############################################ Video Setup ####################################
        _, frame = cap.read()
        hsv_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        height, width, _ = frame.shape
        
        mask = cv2.inRange(hsv_frame, lower, upper)
        kernel = np.ones((5, 5), "uint8")
        colorMask = cv2.dilate(mask, kernel)
        res_color = cv2.bitwise_and(frame, frame, mask = colorMask)
        contours, hierarchy = cv2.findContours(mask, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
        for contour in contours:
            area = cv2.contourArea(contour)
            if(1000000>area > 2000):
                GPIO.output(red, GPIO.LOW)
                GPIO.output(blue, GPIO.HIGH)
                protocol="blue"
                x, y, w, h = cv2.boundingRect(contour)
                # print (x, ", x")
                frame = cv2.rectangle(frame, (x, y),(x + w, y + h),colorbox, 2)
                cv2.putText(frame, name+" Detected", (x, y), cv2.FONT_HERSHEY_SIMPLEX, 1,colorbox,2)
                break
            else:
                if (protocol == "blue"):
                    GPIO.output(blue, GPIO.LOW)
                    protocol = last_prot
                    
###################################################Ultrasonic################################
        if (time.time()>=ultraTrigger):
            delayTime = 0
            GPIO.output(trigPin, 0)
            time.sleep(2E-6)
            # set trigger pin high for 10 micro seconds
            GPIO.output(trigPin, 1)
            time.sleep(10E-6)
            # go back to zero - communication compete to send ping
            GPIO.output(trigPin, 0)
            # now need to wait till echo pin goes high to start the timer
            # this means the ping has been sent
            delayTime = time.time() + .2
            while GPIO.input(echoPin) == 0:
                if (time.time() > delayTime):
                    break
                pass
            # start the time - use system time
            echoStartTime = time.time()
            # wait for echo pin to go down to zero
            delayTime = time.time() + .2
            while GPIO.input(echoPin) == 1:
                if (time.time() > delayTime):
                    break
                pass
            echoStopTime = time.time()
            # calculate ping travel time
            pingTravelTime = echoStopTime - echoStartTime
            # Use the time to calculate the distance to the target.
            # speed of sound at 72 deg F is 344.44 m/s
            # from weather.gov/epz/wxcalc_speedofsound.
            # equations used by calculator at website above.
            # speed of sound = 643.855*((temp_in_kelvin/273.15)^0.5)
            # temp_in_kelvin = ((5/9)*(temp_in_F - 273.15)) + 32
            #
            # divide in half since the time of travel is out and back
            dist_cm = (pingTravelTime*34444)/2

                            #Timer Function
            print(dist_cm)
            ultraTrigger = time.time() + .5
            #red trigger
            if (dist_cm <50):
                protocol = "red"
################################### SENSOR PIXELS ##########################################

        cx1 = int(width/2-200)  #finds x values of pixels used to sense cones
        cx2 = int(width/2)
        cx3 = int(width/2+200)
        cx4 = int(width/2-100)
        cx5 = int(width/2+100)
        cx6 = cx1 -150
        cx7 = cx3 +150
        cy = int(700)           

        ly = int(height/2+200)  #sidewalk detector pixel locations (xy)
        lx = int(100)
        rx =int(width-100)
        ry = int(height/2+200)

                                            #HSV pixel setup for each 'sensor'
        Sensor1 = hsv_frame[cy,cx1]                     #
        hue1 = Sensor1[0]
        cone1 = Sensor1[1]                              
                                                        
        Sensor2 = hsv_frame[cy,cx2]                     #
        hue2 = Sensor2[0]
        cone2 = Sensor2[1]

        Sensor3 = hsv_frame[cy,cx3]                     #
        hue3 = Sensor3[0]
        cone3 = Sensor3[1]

        Sensor4 = hsv_frame[cy,cx4]                     #
        hue4 = Sensor4[0]
        cone4 = Sensor4[1]

        Sensor5 = hsv_frame[cy,cx5]                     #
        hue5 = Sensor5[0]
        cone5 = Sensor5[1]

        Sensor6 = hsv_frame[cy,cx6]                     #
        hue6 = Sensor6[0]
        cone6 = Sensor6[1]

        Sensor7 = hsv_frame[cy,cx7]                     #
        hue7 = Sensor7[0]
        cone7 = Sensor7[1]

        detector_left = hsv_frame[ly,lx]    #gets the saturation of the sidewalk detector pixels
        detector_right = hsv_frame[ry,rx]
        saturation_left = detector_left[1]
        saturation_right = detector_right[1]

        colors(cone1,hue1)                  #plugs in the saturation and hue of each cone sensor pixel into the colors fn#
        colors(cone2,hue2)
        colors(cone3,hue3)
        colors(cone4,hue4)
        colors(cone5,hue5)
        # colors(cone6,hue6)            #auxiliary sensors
        # colors(cone7,hue7)

        if (last_dc != dc):                 #updates pwm if it is changed
            pwm.ChangeDutyCycle(dc)
            last_dc = dc

        if saturation_left <20:             #Saturation Detection (Left,right)
            left_sense = "on"
        else:
            left_sense = "off"
        if saturation_right <20:
            right_sense = "on"
        else:
            right_sense = "off"

        
        ############################################# BLUE PROTOCOL ############################################
        if(protocol == "blue"):
            dc = 100
            GPIO.output(red, GPIO.LOW)
            if (x > cx2-w/2):                       #middle x value defined earlier
                GPIO.output(left, GPIO.LOW)
                GPIO.output(right, GPIO.HIGH)
            elif (x < cx2-w/2):
                GPIO.output(left, GPIO.HIGH)
            
                GPIO.output(right, GPIO.LOW)
        ############################################# ORANGE RIGHT FOLLOWING PROTOCOL ##################################
        if(protocol == "orange"):  
            dc = 100
            last_prot="orange" 
            GPIO.output(red, GPIO.LOW)
            if(right_sense == "off"):
                GPIO.output(left, GPIO.HIGH)
                GPIO.output(right, GPIO.LOW)
            else:
                GPIO.output(left, GPIO.LOW)
                GPIO.output(right, GPIO.HIGH)
                dc = 100
        ############################################# YELLO LEFT FOLLOWING PROTOCOL ##################################

        elif(protocol == "yellow"):
            last_prot='yellow'
            dc = 100    
            GPIO.output(red, GPIO.LOW)
            if(left_sense == "off"):
                GPIO.output(left, GPIO.LOW)
                GPIO.output(right, GPIO.HIGH)
            else:
                GPIO.output(left, GPIO.HIGH)
                GPIO.output(right, GPIO.LOW)

        ############################################LATCHING eSTOP protocol###############################
        elif(protocol =='red'):
            pwm.ChangeDutyCycle(0)
            dc=0
            GPIO.output(left, GPIO.LOW)
            GPIO.output(right, GPIO.LOW)
            GPIO.output(red,GPIO.HIGH)
            GPIO.output(blue, GPIO.LOW)
            
            while True:
                if GPIO.input(butPin)==GPIO.LOW:
                    SetTime(.2)
                    debounce = t_end
                    protocol = last_prot
                    print ("pressed")
                    break
        else:
            protocal ="idle"

        #Draws circles around sensing pixels
        cv2.circle(frame, (cx1, cy),5, (255, 255, 255),3)
        cv2.circle(frame, (cx2, cy),5, (255, 255, 255),3)
        cv2.circle(frame, (cx3, cy),5, (255, 255, 255),3) 
        cv2.circle(frame, (cx4, cy),5, (255, 255, 255),3)
        cv2.circle(frame, (cx5, cy),5, (255, 255, 255),3)   
        cv2.circle(frame, (cx6, cy),5, (255, 255, 255),3)
        cv2.circle(frame, (cx7, cy),5, (255, 255, 255),3)              
        cv2.circle(frame, (lx,ly),5, (255, 255, 255),3)
        cv2.circle(frame, (rx,ry),5, (255, 255, 255),3)

        # print(color)
        # print(saturation_left)
        # print(saturation_right)
        # print("left: ",left_sense)                    for Debugging purposes
        # print("right: ",right_sense)
        # print("protocol:", protocol)
        # print(t_end-time.time())
        
        #break on button press/terminate program
        if(debounce < time.time()):
            if GPIO.input(butPin)==GPIO.LOW:
                GPIO.output(blue, GPIO.LOW)
                GPIO.output(red, GPIO.LOW)
                GPIO.output(left, GPIO.LOW)
                GPIO.output(right, GPIO.LOW)
                dc=0
                break
        #show the frame!
        cv2.imshow("Frame", frame)
        key = cv2.waitKey(1)
        if key == 27:
            break

except KeyboardInterrupt: # If CTRL+C is pressed, exit cleanly:
    pwm.stop() # stop PWM
    GPIO.cleanup() # cleanup all GPIO
    cap.release()
    cv2.destroyAllWindows()
