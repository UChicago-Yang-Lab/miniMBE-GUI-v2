from vimba import *
import cv2


vimba = Vimba.get_instance()

def get_cams():
    with vimba:
        cams = vimba.get_all_cameras()
        if(cams):
            print(f"Camera Found:{cams}")
            return cams
        raise FileNotFoundError("No cameras found")
        
def get_frame(camera):
    with vimba:
        with camera:
            frame = camera.get_frame()
            frame.convert_pixel_format(PixelFormat.Mono8)
        
    return frame

cams = get_cams()
cams[0].set_access_mode(AccessMode.Full)
frame = get_frame(cams[0])
cv2.imwrite('test_frame.jpg',frame.as_opencv_image())
