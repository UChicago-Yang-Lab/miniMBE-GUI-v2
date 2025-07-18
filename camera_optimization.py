from vimba import *
import cv2


vimba = Vimba.get_instance()

def get_cams():
    cams = vimba.get_all_cameras
    if(cams):
        print(f"Camera Found:{cams}")
        return cams
    else:
        raise FileNotFoundError
    
def get_frame(camera):
    with camera:
        frame = camera.get_frame()
        frame.convert_pixel_format(PixelFormat.Mono8)
        
    return frame


frame = get_frame(get_cams()[0])
cv2.imwrite('test_frame.jpg',frame.as_opencv_image())
