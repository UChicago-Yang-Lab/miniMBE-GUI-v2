from vimba import *


vimba = Vimba.get_instance()

def get_cams():
    cams = vimba.get_all_cameras
    if(cams):
        print(cams)
        return cams
    else:
        raise FileNotFoundError


get_cams()