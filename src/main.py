#Importing Needed Packages
from imutils.video import VideoStream
from imutils.video import FPS
import argparse
import imutils
import time
import cv2
import RPi.GPIO as GPIO
import pygame






#Constructing Argument Parser and Parsing the arguments
ap = argparse.ArgumentParser()
ap.add_argument("-v","--video",type=str,help="path to input video file")
ap.add_argument("-t","--tracker",type=str,default="kcf",help="OpenCV object tracker type")
args = vars(ap.parse_args())




#Extracting the OpenCV version info
(major,minor) = cv2.__version__.split(".")[:2]




#Function to Create Object Tracker Constructor
if(int(major==3) and int(minor)<2):
  tracker= cv2.Tracker_create(args["tracker"].upper())




#Initializes Dictionary that Maps Strings to their corresponding OpenCV Object Tracker Implementation
else:
  OPENCV_OBJECT_TRACKERS = {
      "csrt": cv2.TrackerCSRT_create,
      "kcf": cv2.TrackerKCF_create,
      "boosting": cv2.TrackerBoosting_create,
      "mil": cv2.TrackerMIL_create,
      "tld": cv2.TrackerTLD_create,
      "medianflow": cv2.TrackerMedianFlow_create,
      "mosse": cv2.TrackerMOSSE_create
  }




#Grab the appropriate Object Tracker via the dictionary created
tracker = OPENCV_OBJECT_TRACKERS[args["tracker"]]()




#Initialize Bounding Box Coordinates of Object we will Track
initBB = None








#If a video path is not supplied user reference to webcam
if not args.get('video',False):
  print("[INFO] starting video stream...")
  vs = VideoStream(src=0).start()
  time.sleep(1.0)




#Otherwise get reference to the video file
else:
  vs = cv2.VideoCapture(args["video"])




#Initialize Frames-Per-Second
fps = None


#Set GPIO mode to BCM
GPIO.setmode(GPIO.BCM)


redPin = 27
greenPin = 17


#Set Up GPIO Pins as Output
GPIO.setup(redPin,GPIO.OUT)
GPIO.setup(greenPin,GPIO.OUT)


#Initialize Pygame and Pygame Mixer


pygame.init()
pygame.mixer.init(channels=2)


#Load Audio Files and Sound into Channels
goodSquat = 'Good-Squat.wav'
badSquat = 'Bad-Squat.wav'


goodChannel = pygame.mixer.Channel(0)
badChannel = pygame.mixer.Channel(1)


goodSound = pygame.mixer.Sound(goodSquat)
badSound = pygame.mixer.Sound(badSquat)


#Loop over frames from video stream
while True:




  #Grab current frame, then use either VideoStream or VideoCapture Object
  frame = vs.read()
  frame = frame[1]if args.get("video",False) else frame




  #If the stream is over end the looping
  if frame is None:
      break




  #Resize frame to process it faster and grab dimensions
  frame = imutils.resize(frame, width=500)
  (H,W) = frame.shape[:2]




  #Check to see if we are currently tracking an object
  if initBB is not None:
      #Grab the new bounding box coordinates of the object
      (success,box) = tracker.update(frame)




      #Check to see if tracking success
      if success:
          (x, y, w, h) = [int(v) for v in box]
          cv2.rectangle(frame, (x,y), (x+w,y+h),
          (0,255,0), 2)
        
          #Find the center of the y-coordinates and x-coordinates
          center_y = y+h//2
          center_x = x+w//2


          #Determine whether the bounding box is moving up, down, or staying still and displays the direction
            
          if center_y > 2* frame.shape[0]//3:
              direction = "Squat in Progress"
          elif center_y <frame.shape[0]//3:
              direction = "Squat Finished"  
          else:
              direction = "Squat Not Started"
          cv2.putText(frame, f"Direction: {direction}",(10,30), cv2.FONT_HERSHEY_SIMPLEX,1,(0,0,255),2)
         
          #Checking the form of the squat by analyzing user's forward lean
          if direction == "Squat in Progress":
              if center_x <frame.shape[1]//2.5:
                  squat = "Bad Form"
                  cv2.putText(frame, f"Squatting Form: {squat}",(10,300), cv2.FONT_HERSHEY_SIMPLEX,1,(0,0,255),2)
                  GPIO.output(redPin,GPIO.HIGH)
                  badChannel.play(badSound)
                 


              else:
                  squat = "Good Form"
                  cv2.putText(frame, f"Squatting From: {squat}",(10,300), cv2.FONT_HERSHEY_SIMPLEX,1,(0,255,0),2)
                  GPIO.output(greenPin,GPIO.HIGH)
                  goodChannel.play(goodSound)
                 


          if direction == "Squat Finished":
              squat = ""
              cv2.putText(frame, f" {squat}",(10,300), cv2.FONT_HERSHEY_SIMPLEX,1,(0,0,255),2)
             
      #Update FPS counter
      fps.update()
      fps.stop()




      #Initializes the set of info to be displayed on the screen
      info = [
          ("Tracker",args["tracker"]),
          ("Success", "Yes" if success else "No"),
          ("FPS", "{:.2f}".format(fps.fps())),
      ]




      #Loop over info tuples and draw them on the frame
      for (i, (k,v)) in enumerate(info):
          text = "{}: {}".format(k,v)
          cv2.putText(frame, text, (10, H - ((i*20)+20)),
                      cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0,0,255),2)




  #Show the output frame
  cv2.imshow("Frame", frame)
  key = cv2.waitKey(1) & 0xFF




  #If the "s" key is selected, we are going to "select" a bounding box to track
  if key == ord("s"):




      #Select the bounding box of the object we want to track and press "Enter" or "Space" after selecting
      initBB = cv2.selectROI("Frame", frame, fromCenter=False,
              showCrosshair=True) 








      #Start OpenCV object tracker using bounding box and start FPS estimator
      tracker.init(frame, initBB)
      fps = FPS().start()












  #If "q" is pressed, end the loop
  elif key == ord("q"):
      break








#If using a webcam, release pointer
if not args.get("video", False):
  vs.stop()




#Otherwise, release the file pointer
else:
  vs.release()




#Close All Windows, Turn Off LEDs, and Turn Off All Audio
pygame.mixer.quit()
pygame.quit()
GPIO.output(redPin,GPIO.LOW)
GPIO.output(greenPin,GPIO.LOW)
GPIO.cleanup()
cv2.destroyAllWindows()
