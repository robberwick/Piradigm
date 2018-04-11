from img_base_class import *
import random
import cv2.aruco as aruco
from approxeng.input.selectbinder import ControllerResource

# Image stream processing thread
class StreamProcessor(threading.Thread):
    def __init__(self, screen=None, camera=None, drive=None):
        super(StreamProcessor, self).__init__()
        self.camera = camera
        self.image_width, self.image_height = self.camera.resolution
        self.image_centre_x = self.image_width / 2.0
        self.image_centre_y = self.image_height / 2.0
        self.drive = drive
        self.drive.should_normalise_motor_speed = False
        self.screen = screen
        self.stream = picamera.array.PiRGBArray(camera)
        self.event = threading.Event()
        self.terminated = False
        self.DRIVING = True
        self.edge = False
        self.BLUR = 3
        self.mode = [self.file_selection, self.auto_calibrating, self.manual_calibrating, self.thresholding]
        self.mode_number = 0
        self.colour_limits = ((0, 0, 0), (180, 255, 255))
        self.TIMEOUT = 30.0
        self.PARAM = 60
        self.START_TIME = time.clock()
        self.END_TIME = self.START_TIME + self.TIMEOUT
        self.finished = False
        self.i = 0
        logger.info("setup complete, looking")
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

    def file_selection(self, image, screen):
        screen.fill([0, 0, 0])

    def auto_calibrating(self, image, screen):
        screenimage = cv2.cvtColor(image, cv2.COLOR_HSV2BGR)
        frame = pygame.surfarray.make_surface(cv2.flip(screenimage, 1))
        screen.fill([0, 0, 0])
        screen.blit(frame, (0, 0))
        self.show_cal_label(screen)
        self.colour_limits = self.get_limits(image, 1.5)

    def manual_calibrating(self, image, screen):
        pass

    def thresholding(self, image, screen):
        self.show_thresholding_label(screen)
        obj_range = threshold_image(image, self.colour_limits)
        frame = pygame.surfarray.make_surface(cv2.flip(obj_range, 1))
        screen.blit(frame, (0, 0))
        obj_x, obj_y, obj_a, obj_contour = find_largest_contour(obj_range)
        if obj_contour is not None:
            pygame.mouse.set_pos(obj_y, self.image_width - obj_x)
            img_name = str(self.i) + "Fimg.jpg"
        else:
            img_name = str(self.i) + "NFimg.jpg"
        image = cv2.cvtColor(image, cv2.COLOR_HSV2RGB)
        #filesave for debugging: 
        #cv2.imwrite(img_name, image)
        self.i += 1

    def get_limits(self, image, sigmas):
        """function to use the mean and standard deviation of an images
        channels in the centre of the image to create suggested threshold
        limits based on number of 'sigmas' (usually less than three).
        returns a tuple of tuples ((low1, low2, low3),(upp1, upp2, upp3))"""
        h, w = image.shape[:2]
        mask_radius = min(h, w)/2
        mask = numpy.zeros(image.shape[:2], numpy.uint8)
        cv2.circle(mask, (w/2, h/2), mask_radius, 255, -1)
        mean, stddev = cv2.meanStdDev(image, mask=mask)
        lower = mean - sigmas * stddev
        upper = mean + sigmas * stddev
        return ((lower[0][0], lower[1][0], lower[2][0]), (upper[0][0], upper[1][0], upper[2][0]))
   
    def show_cal_label(self, screen):
        font = pygame.font.Font(None, 60)
        label = font.render(str("Calibrating"), 1, (255,255,255))
        screen.blit(label, (10, 200))

    def show_thresholding_label(self, screen):
        font = pygame.font.Font(None, 60)
        label = font.render(str("Testing"), 1, (255,255,255))
        screen.blit(label, (10, 200))


    def process_image(self, image, screen):
        screen = pygame.display.get_surface()
        image = cv2.cvtColor(image, cv2.COLOR_RGB2HSV)
        self.mode[self.mode_number](image, screen)
        pygame.display.update()



class Calibrate(BaseChallenge):
    """Colour calibration function, allows any json file storing colours to be tuned"""

    def __init__(self, timeout=120, screen=None, joystick=None):
        self.image_width = 160  # Camera image width
        self.image_height = 128  # Camera image height
        self.frame_rate = 30  # Camera image capture frame rate
        self.screen = screen
        time.sleep(0.01)
        self.joystick=joystick
        super(Calibrate, self).__init__(name='Calibrate', timeout=timeout, logger=logger)

    def joystick_handler(self, button):
        if button['home']:
            self.processor.mode_number = 0
            self.logger.info("File selection mode")
        if button['select']:
            if self.processor.mode_number <> 0:
                self.logger.info("colour value set to %s" %  self.colour_limits)
                #TODO: add value save routine here 
                self.logger.info("value saved")
        if button['r1']:
            self.processor.finished = True
        if button['r2']:
            self.processor.mode_number = 3
            self.logger.info("Entering thresholding mode")
        if button['l1']:
            self.processor.mode_number = 2
            self.logger.info("Manual calibration mode")
        if button['l2']:
            self.processor.mode_number = 1
            self.logger.info("auto calibrating mode")

    def run(self):
        # Startup sequence
        logger.info('Setting up camera')
        screen = pygame.display.get_surface()
        self.camera = picamera.PiCamera()
        self.camera.resolution = (self.image_width, self.image_height)
        self.camera.framerate = self.frame_rate
        self.camera.iso = 800
        self.camera.awb_mode = 'off'
        self.camera.awb_gains = (1.149, 2.193)
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
                time.sleep(0.01)
                if self.joystick.connected:
                    self.joystick_handler(self.joystick.check_presses())
                if self.processor.finished:
                    self.stop()

        except KeyboardInterrupt:
            # CTRL+C exit, disable all drives
            self.logger.info("killed from keyboard")
            self.drive.move(0,0)
        finally:
            # Tell each thread to stop, and wait for them to end
            self.logger.info("stopping threads")
            self.drive.should_normalise_motor_speed = True
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
