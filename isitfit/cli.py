import logging
logger = logging.getLogger('isitfit')
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)
logger.addHandler(ch)
logger.setLevel(logging.DEBUG)

from .mainManager import MainManager


if __name__=='__main__':
    mm = MainManager()
    ifi = mm.get_ifi()
    logger.info("IFI = %0.2f%%"%ifi)
    logger.info("(IFI >= 70% is well optimized)")
    logger.info("(IFI <= 30% is underused)")
