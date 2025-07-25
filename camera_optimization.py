from vimba import *
import cv2
import os
import numpy as np
import skimage.data
from skimage.restoration import estimate_sigma
from skimage import img_as_float

#TODO:
# - Add a warning for light instability(i.e. flashing or etc.)

#Minimum times searched for Gain & Exposure Time
MIN_EXP_TIME = 1000
MAX_EXP_TIME = 1000000
MIN_GAIN = 30.0
MAX_GAIN = 100.0

#Minimum & Maximum Brightness(0-255)
MIN_BRIGHTNESS = 20
MAX_BRIGHTNESS = 235


#Unused - Temp Folder Name
TEMP_FOLDER = 'temp'
#Check gray-scaled image for brightness(if too low or too high)
#TODO: Refactor this method name
#TODO: Research better methods of determining brigthness and other basic image sanity checks to run before choosing to discard the given image. 
# also check for what the most reasonable MIN & MAX brightness values actually are
def basic_image_check(gray_img) -> bool:
    avg_brightness = np.average(gray_img)
    if avg_brightness < MIN_BRIGHTNESS or avg_brightness > MAX_BRIGHTNESS:
        return False
    return True



vimba = Vimba.get_instance()
with vimba:
    def get_cams():
            #TODO: Add Special Exception for if another camera is connected 
            cams = vimba.get_all_cameras()
            if(cams):
                print(f"Camera Found:{cams}")
                return cams
            raise FileNotFoundError("No cameras found")
            
    def get_frame(camera):
        with camera:
            frame = camera.get_frame()
            frame.convert_pixel_format(PixelFormat.Bgr8)
        return frame

    
    def optimized_camera_values(camera):
        #TODO: consider using expspace or logspace bcuz of scale of values.
        
        #Value of all weights should add up to 1
        L_VAR_WEIGHT = 0.5
        SIGMA_WEIGHT = 0.5 
        image_stats = []
        with camera:
            for g in np.linspace(MIN_GAIN, MAX_GAIN, 30):
                camera.Gain.set(g)
                for e in np.linspace(MIN_EXP_TIME, MAX_EXP_TIME, 100):
                    #TODO: Set up a limitation for images which are too bright or too dark
                    camera.ExposureTime.set(e)
                    frame = get_frame(camera)
                    cv_frame = frame.as_opencv_image()

                    gray_frame = cv2.cvtColor(cv_frame,cv2.COLOR_BGR2GRAY)
                    
                    if not basic_image_check(gray_img=gray_frame):
                        continue
                    
                    #calculate laplacian variance of image
                    laplacian_var = cv2.Laplacian(gray_frame,cv2.CV_64F).var()
                    #calculate noise using skimage's estimate noise
                    sigma = estimate_sigma(gray_frame, average_sigmas=True)

                    #Question: Should I normalize the values in each of the image stats(Laplacian Variance & Sigma)?
                    img_score = L_VAR_WEIGHT * laplacian_var + SIGMA_WEIGHT * sigma

                    #Save to dictionary
                    image_stats.append({'gain':g,'exp_time':e,'score':img_score, 'laplacian_var':laplacian_var,'sigma':sigma})
                    print(f"Captured image with Gain: {g}, Exposure Time: {e}")

        #Get the minimum score
        min_score = min('score' for img in image_stats)
        min_index = ['score' for img in image_stats].index(min_score)

        print(f'*****\n\nOptimal Image Settings Found\nScore = {min_score}\nGain = {image_stats[min_index]['gain']}dB\nExposure_Time = {image_stats[min_index]['exp_time']}\nLap. Var & sigma= [{image_stats[min_index]['laplacian_var']},{image_stats[min_index]['sigma']}] \n\n*****')
    
        
    
            

    def main():
        cams = get_cams()
        cams[0].set_access_mode(AccessMode.Full)
        optimized_camera_values(cams[0])



    if __name__ == "__main__":
        main()

