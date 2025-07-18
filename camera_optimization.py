from vimba import *
import cv2
import numpy as np

MIN_EXP_TIME = 1000
MAX_EXP_TIME = 1000000

MIN_GAIN = 30.0
MAX_GAIN = 100.0



vimba = Vimba.get_instance()
with vimba:
    def get_cams():
            cams = vimba.get_all_cameras()
            if(cams):
                print(f"Camera Found:{cams}")
                return cams
            raise FileNotFoundError("No cameras found")
            
    def get_frame(camera):
        with camera:
            frame = camera.get_frame()
            frame.convert_pixel_format(PixelFormat.Mono8)
            
        return frame

    def optimized_camera_values(camera):
        with camera:
            for g in np.linspace(MIN_GAIN, MAX_GAIN, 30):
                camera.Gain.set(g)
                for e in np.linspace(MIN_EXP_TIME, MAX_EXP_TIME, 100):
                    camera.ExposureTime.set(e)
                    frame = get_frame(camera)
                    cv2.imwrite(f'/raw_images/gain_{g}_exp_{e}.jpg', frame.as_opencv_image())
                    print(f"Captured image with Gain: {g}, Exposure Time: {e}")
            

    def main():
        cams = get_cams()
        cams[0].set_access_mode(AccessMode.Full)
        #frame = get_frame(cams[0])
        #cv2.imwrite('test_frame.jpg',frame.as_opencv_image())
        optimized_camera_values(cams[0])



    if __name__ == "__main__":
        main()

