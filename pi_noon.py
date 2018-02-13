from img_base_class import *
import cv2.aruco as aruco

# Image stream processing thread
class StreamProcessor(threading.Thread):
    def __init__(self, screen=None, camera=None, drive=None):
        super(StreamProcessor, self).__init__()
        self.camera = camera
        self.image_width, self.image_height = self.camera.resolution
        self.image_centre_x = self.image_width / 2.0
        self.image_centre_y = self.image_height / 2.0
        self.drive = drive
        self.screen = screen
        self.stream = picamera.array.PiRGBArray(camera)
        self.event = threading.Event()
        self.terminated = False
        self.DRIVING = False
        self.TURN_TIME = 0.05
        self.TURN_SPEED = 1
        self.SETTLE_TIME = 0.05
        self.MIN_BALLOON_SIZE = 3
        self.TURN_AREA = 5000  #6000 turns right at edge, 9000 too high
        self.TURN_HEIGHT = 26
        self.BACK_AWAY_START = 60
        self.BACK_AWAY_STOP = 40
        self.back_away = False
        self.edge = False
        self.last_t_error = 0
        self.TURN_P = 2
        self.TURN_D = 0.3
        self.STRAIGHT_SPEED = 1
        self.SLIGHT_TURN = 0.1
        self.STEERING_OFFSET = 0.0  #more positive make it turn left
        self.CROP_WIDTH = 160
        self.CROP_HEIGHT = 55
        self.TIMEOUT = 30.0
        self.START_TIME = time.clock()
        self.END_TIME = self.START_TIME + self.TIMEOUT
        self.found = False
        self.finished = False
        self.i = 0
        logger.info("setup complete, looking")
        time.sleep(1)
        self.start()

    def run(self):
        # This method runs in a separate thread
        while not self.terminated:
            # Wait for an image to be written to the stream
            if self.event.wait(1):
                try:
                    # Read the image and do some processing on it
                    self.stream.seek(0)
                    self.process_image(self.stream.array, self.screen)
                finally:
                    # Reset the stream and event
                    self.stream.seek(0)
                    self.stream.truncate()
                    self.event.clear()

    def find_balloon(self, image):
        '''function to find the largest circle (balloon) in the image'''
        circles = cv2.HoughCircles(image, cv2.HOUGH_GRADIENT, 1, 2, param1=50,param2=15,minRadius=0,maxRadius=10)
        #param1=50 = less than half gets ball
        #param1 = 75 = about 1in10
        #param1 = 25 = less than half
        # Go through each contour
        found_r = None
        found_x = None
        found_y = None
        i=0
        if circles is not None:
            circles = numpy.round(circles[0, :]).astype("int")
            for (x, y, r) in circles:
                i+=1
                if found_r < r:
                    found_r = r
                    found_x = x
                    found_y = y
            print i
        else:
            print "circle not found"
        return [found_x, found_y, found_r]

        
    def seek(self):
        self.drive.move(self.TURN_SPEED, 0)
        time.sleep(self.TURN_TIME)
        self.drive.move(0,0)
        time.sleep(self.SETTLE_TIME)
    
    def process_image(self, image, screen):
        screen = pygame.display.get_surface()
        image = image[self.CROP_HEIGHT:self.image_height, (self.image_centre_x - self.CROP_WIDTH/2):(self.image_centre_x + self.CROP_WIDTH/2)]
        # Our operations on the frame come here
        screenimage = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        frame = pygame.surfarray.make_surface(cv2.flip(screenimage, 1))
        screen.fill([0, 0, 0])
        screen.blit(frame, (0, 0))
        image = cv2.cvtColor(image, cv2.COLOR_RGB2HSV)
        # We want to extract the 'Hue', or colour, from the image. The 'inRange'
        hue, sat, val = cv2.split(image)
        sat.fill(255)
        val.fill(255)
        screenimage = cv2.merge([hue, sat, val])
        screenimage = cv2.cvtColor(screenimage, cv2.COLOR_HSV2BGR)
        frame = pygame.surfarray.make_surface(cv2.flip(screenimage, 1))
        screen.blit(frame, (70, 0))

        pygame.display.update()
        # Find the contours
        screenimage=cv2.cvtColor(screenimage, cv2.COLOR_BGR2GRAY)
        canny = cv2.Canny(screenimage,50,100)
        frame = pygame.surfarray.make_surface(cv2.flip(canny, 1))
        screen.blit(frame, (150, 0))
        balloon_x, balloon_y, balloon_r = self.find_balloon(screenimage)
        if balloon_r is not None:
            pygame.mouse.set_pos(balloon_y, self.CROP_WIDTH - balloon_x)
        if balloon_r > self.MIN_BALLOON_SIZE:
                #opponent is disrupting countour shape, making it concave
                print ("found balloon: position %d, %d, radius %d" % (balloon_x, balloon_y, balloon_r))
                self.found = True
                t_error = (self.image_centre_x - balloon_x) / self.image_centre_x
                turn = self.TURN_P * t_error
                if balloon_r > self.BACK_AWAY_START or (balloon_r > self.BACK_AWAY_STOP and self.back_away):
                    #we're probably close, back off
                    self.back_Away = True
                    if self.DRIVING:
                        self.drive.move(turn/2, -self.STRAIGHT_SPEED/2)
                else:
                    self.back_away = False
                    if self.DRIVING:
                        self.drive.move(turn, self.STRAIGHT_SPEED)
        else:
            self.edge = False
            if self.found:
                #if we were trackign and we've ended up here, we're probably super close
                #print "just lost the opponent, trying backing off first"
                self.back_away = True
                self.found = False
                if self.DRIVING:
                    self.drive.move(0, -self.STRAIGHT_SPEED)
            else:
                #print "no opponent, no red spotted"
                self.back_away = False
                self.found = False
                if self.DRIVING:
                    self.seek()
        
        image = cv2.cvtColor(image, cv2.COLOR_HSV2RGB)
        if self.found:
            img_name = str(self.i) + "Fimg.jpg"
        else:
            #if self.edge:
                #cv2.imwrite(str(self.i) + "imrange.jpg", imrange)
            img_name = str(self.i) + "NFimg.jpg"
        #filesave for debugging: 
        #cv2.imwrite(img_name, image)
        self.i += 1



class PiNoon(BaseChallenge):
    """Pi Noon challenge class"""

    def __init__(self, timeout=120, screen=None, joystick=None):
        self.image_width = 160  # Camera image width
        self.image_height = 128  # Camera image height
        self.frame_rate = 30  # Camera image capture frame rate
        self.screen = screen
        time.sleep(0.01)
        self.joystick=joystick
        super(PiNoon, self).__init__(name='PiNoon', timeout=timeout, logger=logger)


    def run(self):
        # Startup sequence
        logger.info('Setting up camera')
        screen = pygame.display.get_surface()
        self.camera = picamera.PiCamera()
        self.camera.resolution = (self.image_width, self.image_height)
        self.camera.framerate = self.frame_rate
        self.camera.iso = 800
        self.camera.awb_mode = 'incandescent'
        self.camera.shutter_speed = 12000
        logger.info('Setup the stream processing thread')
        # TODO: Remove dependency on drivetrain from StreamProcessor
        self.processor = StreamProcessor(
            screen=self.screen,
            camera=self.camera,
            drive=self.drive,
        )
        logger.info('Wait ...')
        time.sleep(2)
        logger.info('Setting up image capture thread')
        self.image_capture_thread = ImageCapture(
            camera=self.camera,
            processor=self.processor
        )
        pygame.mouse.set_visible(True)
        try:
            while not self.should_die:
                time.sleep(0.1)
                if self.processor.finished:
                    self.timeout = 0

        except KeyboardInterrupt:
            # CTRL+C exit, disable all drives
            self.logger.info("killed from keyboard")
            self.drive.move(0,0)
        finally:
            # Tell each thread to stop, and wait for them to end
            self.logger.info("stopping threads")
            self.image_capture_thread.terminated = True
            self.image_capture_thread.join()
            self.processor.terminated = True
            self.processor.join()
            #release camera
            self.camera.close()
            self.camera = None
            self.logger.info("stopping drive")
            self.drive.stop()
            pygame.mouse.set_visible(False)
            self.logger.info("bye")
            pygame.event.post(pygame.event.Event(USEREVENT+1,message="challenge finished"))
