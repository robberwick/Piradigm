import logging
import time

from drivetrain import DriveTrain
logging.config.fileConfig('logging.ini')
logger = logging.getLogger('piradigm.' + __name__)

class BaseChallenge(object):
    def __init__(self, logger=logger, screen=None, timeout=120, name="Unamed"):
        self.logger = logger
        self.logger.info("initialising %s" % name)
        self.screen = screen
        self.timeout = timeout
        self.start_time = time.clock()
        self.name = name
        self.killed = False
        self.drive = DriveTrain(timeout=self.timeout)

    @property
    def should_die(self):
        # TODO this should be monitored by the calling thread using a
        # combination of Timer threads and is_alive()
        timed_out = time.clock() >= (self.start_time + self.timeout)
        return timed_out or self.killed

    def stop(self):
        self.logger.info("%s challenge stopping" % self.name)
        self.killed = True

    def run(self):
        """Base implementation of challenge run() required for threading"""
        pass
