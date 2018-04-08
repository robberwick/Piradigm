#!/usr/bin/env python
# coding: Latin

# this file contains all the common elements of a threaded image processing challenge
# Load library functions we want
import logging
import logging.config
import os
import time
import sys
sys.path.append('/usr/local/lib/python2.7/site-packages')

import threading
import pygame
from pygame.locals import*
import sgc
from sgc.locals import *
import picamera
import picamera.array
import cv2
import numpy
from fractions import Fraction
from base_challenge import BaseChallenge

file_path = os.path.dirname(os.path.realpath(__file__))
logging.config.fileConfig(os.path.join(file_path, 'logging.ini'))
logger = logging.getLogger('piradigm.' + __name__)
logger.debug('Libraries loaded')


# Image capture thread
class ImageCapture(threading.Thread):
    def __init__(self, camera=None, processor=None):
        super(ImageCapture, self).__init__()
        self.terminated = False
        self.camera = camera
        self.processor = processor
        self.start()

    def run(self):
        logger.debug('Start the stream using the video port')
        self.camera.capture_sequence(
            self.trigger_stream(),
            format='bgr',
            use_video_port=True
        )
        logger.debug('Terminating camera processing...')
        self.processor.terminated = True
        self.processor.join()
        logger.debug('Processing terminated.')
                        
    # Stream delegation loop
    def trigger_stream(self):
        while not self.terminated:
            if self.processor.event.is_set():
                time.sleep(0.01)
            else:
                yield self.processor.stream
                self.processor.event.set()

def threshold_image(image, limits):
        '''function to find what parts of an image lie within limits.
        returns the parts of the original image within the limits, and the mask'''
        hsv_lower, hsv_upper = limits
       
        mask = wrapping_inRange(
            image,
            numpy.array(hsv_lower),
            numpy.array(hsv_upper)
        )
        return mask

def find_largest_contour(image):
        '''takes a binary image and returns coordinates, size and contourobject of largest contour'''
        contourimage, contours, hierarchy = cv2.findContours(
            image, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE
        )
        # Go through each contour
        found_area = 1
        found_x = -1
        found_y = -1
        biggest_contour = None
        for contour in contours:
            area = cv2.contourArea(contour)
            if found_area < area:
                found_area = area
                M = cv2.moments(contour)
                found_x = int(M['m10']/M['m00'])
                found_y = int(M['m01']/M['m00'])
                biggest_contour = contour
        return found_x, found_y, found_area, biggest_contour

def wrapping_inRange(image, lower_limit, upper_limit):
    '''function to behave like opencv imrange, but allow hue to wrap around
    if hue in lower limit is higher than hue in upper limit, then it will use the wrapped range''' 
    h_lower, s_lower, v_lower = lower_limit
    h_upper, s_upper, v_upper = upper_limit
    if h_lower > h_upper:
        hsv_lower = (0, s_lower, v_lower)
        hsv_upper = (h_upper, s_upper, v_upper)
        imrange1 = cv2.inRange(
            image,
            numpy.array(hsv_lower),
            numpy.array(hsv_upper)
        )
        hsv_lower = (h_lower, s_lower, v_lower)
        hsv_upper = (180, s_upper, v_upper)
        imrange2 = cv2.inRange(
            image,
            numpy.array(hsv_lower),
            numpy.array(hsv_upper)
        )
        imrange =  cv2.bitwise_or(imrange1, imrange2)
    else:
        imrange = cv2.inRange(
            image,
            numpy.array(lower_limit),
            numpy.array(upper_limit)
        )
    return imrange
