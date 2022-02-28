from statistics import mean

import cv2
import sys

'''''

Program:
Finding the distances of meteors and UFO(s) in relation to stereo cameras using images provided

Output: 
Frame number, list of colours and distances 
'''''


'''''
-create masks for images to detect specific colours
-mask can be used to find distances
-converts image hsv range before finding the mask
'''''
def get_color_mask_imgs(img):
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    # create mask for each colour

    mask_red = cv2.inRange(hsv, (0, 100,100), (10, 255, 255)) # Create the mask
    mask_blue = cv2.inRange(hsv, (110, 100, 100), (130, 255, 255))
    cyan = cv2.inRange(hsv, (80, 100, 100), (110, 255, 255))
    mask_yellow = cv2.inRange(hsv, (30, 100, 100), (50, 255, 255))
    mask_white = cv2.inRange(hsv, (0, 0, 50), (10, 100, 255))
    mask_orange = cv2.inRange(hsv, (15, 100, 100), (25, 255, 255))
    mask_green = cv2.inRange(hsv, (50, 100, 100), (60, 255, 255))

    #mask assigned lower and upper hsv bounds of the colour
    #dictionary stores colour names and masks

    masks = {"Blue":mask_blue,"Red":mask_red, "Green":mask_green,"Cyan":cyan, "Yellow":mask_yellow, "White":mask_white, "Orange":mask_orange}
    return masks

#find contours using the colour masks
def find_img_mask(masked_image):
    # from lab 3 Thresholding and contours
    blur = cv2.GaussianBlur(masked_image, (5, 5), 0)
    cont, _ = cv2.findContours(blur, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    return cont #returns the positions of the coordinates


#find the center coordinates of the contour using moments
#adapted from
#https://learnopencv.com/find-center-of-blob-centroid-using-opencv-cpp-python/
def get_contour_center(contours):
    # calculate moments of the image
    M = cv2.moments(contours)
    try:
        # calculate x,y coordinate of center
        cX = int(M["m10"] / M["m00"])
        cY = int(M["m01"] / M["m00"])
        co_ords = cX,cY
        return co_ords
    except:
        return None


#https://stackoverflow.com/questions/53029540/find-centroid-coordinate-of-whole-frame-in-opencv
#finds the distance from the center of a contour to the center of the frame
def x_distance_from_centre(x_pos):
    width = 640
    return x_pos - width/2


def get_disparity(distance_left, distance_right):
    #uses the x_left and x_right values, then multiplies them by the pixel size
    return (distance_left - distance_right) * 10 ** -5


#finds distance between two cameras,the disparity
#disparity = focal length * base_line / (x_left - x_right)
#adapted from lecture 8: Stereo
def find_camera_distance(disparity):
    base_line = 3500
    focal_length = 12
    try:
        z = (focal_length * base_line)/(disparity)
        return z
    except ZeroDivisionError:
        return None


#find the difference between the current frames x,y points and the next frames x,y points
def difference_in_color_positions(co_ords):
    current_points_vs_new_points = []
    for i in range(1, len(co_ords)): #loop through all the coordinates
        x = (co_ords[i]) - (co_ords[i-1]) #current frame coordinates minus new frame cordinates
        current_points_vs_new_points.append(x)
    return current_points_vs_new_points


#find the difference between the x and y coordinates for the left and right image
def get_frame_differences(position_list):
    diffs = []
    for i in range(0, len(position_list)): #loop through the list of position for each frame
        if i == 0:
            continue
        x_diff = abs(position_list[i][0] - position_list[i - 1][0])
        y_diff = abs(position_list[i][1] - position_list[i - 1][1])
        diffs.append(x_diff+y_diff)
    return diffs


#calculating the variance
#adapted from
#https://stackabuse.com/calculating-variance-and-standard-deviation-in-python/
def variance(data):
    n = len(data)
    mean = sum(data) / n  # mean of the data
    return sum((x - mean) ** 2 for x in data) / (n - 0)  #square deviations
frame_data = []
print("frame   identity    distance")
#taken from assignment brief
nframes = int(sys.argv[1])
for frame in range(0, nframes):
    frame_number = frame - 1
    fn_left = sys.argv[2] % frame #get each file name for left & right frame
    fn_right = sys.argv[3] % frame
    img_right = cv2.imread(fn_right)
    img_left = cv2.imread(fn_left)
    masks_left = get_color_mask_imgs(img_left) #passing the image into the mask function
    masks_right = get_color_mask_imgs(img_right)

    '''''
    -loop through every frame and finds:
    -the contours of every color
    -centre coordinates of every contour
    -distance from centre of the contours to the frame centre
    -disparity of the left and right distances 
     '''''
    for i, masked_img in enumerate(masks_left.items()):
        left_image = masked_img[1]
        colour_name = masked_img[0]
        right_image = masks_right[colour_name]
        left_conts = find_img_mask(left_image)
        try:
            lx, ly = get_contour_center(left_conts[0])
            right_conts = find_img_mask(right_image) #finding contour colour for each right frame
            rx, ry = get_contour_center(right_conts[0]) #store right frame x and contour centres
            distance_left = x_distance_from_centre(lx) #finds the distance from the center of a contour to the center of the frame
            distance_right = x_distance_from_centre(rx)
            disparity = get_disparity(distance_left, distance_right)
            distance = find_camera_distance(disparity) #finds distance between two cameras
            frame_data.append((frame_number, masked_img[0],(lx,ly),distance))
        except IndexError:
            continue
find_count = []
movement = []


#finding difference between current frame xy positions and new frame xy positions
for colour in ["White","Red","Blue","Orange","Green", "Cyan", "Yellow"]: #checks through the colours
    positions =[]
    for o in frame_data: #storing colour and frame into new array o
        if o[1]==colour:
            positions.append(o[2]) #storing positions into array o
    movement.append((colour, get_frame_differences(positions)))
    find_count.append((colour,len(positions)))


#calulating each colours mean in terms of the xy movements from the frames
average_movement = []
for c in movement:
    average_movement.append(mean(c[1]))
all_mean = mean(average_movement)


#standard deviation calculation of x and y coordinates
stds = []
for c in movement:
    std = mean(c[1]) / all_mean
    stds.append((c[0],std))


#formatting and printing the frame,colors and distance calculated
#adapted from
#https://realpython.com/python-formatted-output/
#https://stackoverflow.com/questions/6913532/display-a-decimal-in-scientific-notation
for o in frame_data: #takes data from frame_data and puts it in o
    print('{}\t\t{} \t\t{:.2e}'.format(int(o[0] +1),o[1],o[3])) #distance calculated formatted into 2sf scientific notation


'''''
checks to see if the standard deviation for a colors x and y positions in each frame is greater than 1.2.
If the s.d of the colours x and y positions is greater than 1.2, this means the colour has many changes in its 
x and y coordinates. This means the colour is not moving in a straight line 
meaning it must be a ufo
'''''

print("UFO: ",end="")
for c in stds:
    if(c[1] > 1.2):
        print(c[0],end="") #prints which colour is the UFO
