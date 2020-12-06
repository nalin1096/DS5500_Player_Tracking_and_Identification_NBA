#!/usr/bin/env python
# coding: utf-8

# In[ ]:


# import the necessary packages
import numpy as np
import imutils
import glob
import cv2
import os
import json

#Returns the template information for each frame of a given video
def court_templates(frames_dir):

    video_frames = sorted(glob.glob(os.path.join(frames_dir, '*.png')))

    final = {}

    # load the image, convert it to grayscale, and detect edges
    template_list = glob.glob(os.path.join(os.getcwd(), 'tracking/utils/court_templates/*.JPG'))
    len_template = len(template_list)

    for frame in video_frames:
        count = 0
        list_templates = []
        for template in template_list:
            template1 = cv2.imread(template)
            template1 = cv2.cvtColor(template1, cv2.COLOR_BGR2GRAY)
            template1 = cv2.Canny(template1, 50, 200)
            (tH, tW) = template1.shape[:2]
            image = cv2.imread(frame)
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            found = None
            # loop over the scales of the image
            for scale in np.linspace(0.2, 1.0, 20)[::-1]:
                # resize the image according to the scale, and keep track
                # of the ratio of the resizing
                resized = imutils.resize(gray, width = int(gray.shape[1] * scale))
                r = gray.shape[1] / float(resized.shape[1])
                # if the resized image is smaller than the template, then break
                # from the loop
                if resized.shape[0] < tH or resized.shape[1] < tW:
                    break


                # detect edges in the resized, grayscale image and apply template
                # matching to find the template in the image
                edged = cv2.Canny(resized, 50, 200)
                result = cv2.matchTemplate(edged, template1, cv2.TM_CCOEFF)
                (_, maxVal, _, maxLoc) = cv2.minMaxLoc(result)
                # if we have found a new maximum correlation value, then update
                # the bookkeeping variable
                if found is None or maxVal > found[0]:
                    found = (maxVal, maxLoc, r)
            # unpack the bookkeeping variable and compute the (x, y) coordinates
            # of the bounding box based on the resized ratio
            #(_, maxLoc, r) = found
            #(startX, startY) = (int(maxLoc[0] * r), int(maxLoc[1] * r))
            #(endX, endY) = (int((maxLoc[0] + tW) * r), int((maxLoc[1] + tH) * r))
            # draw a bounding box around the detected result and display the image
            #cv2.rectangle(image, (startX, startY), (endX, endY), (0, 0, 255), 2)

            if(count < len_template):
                list_templates.append(found)
            count = count + 1

        final[os.path.basename(frame)] = list_templates

    return final

#Returns the specific court points identified in a given frame
def court_features(final, threshold, values, innerkeys):
    result={}
    for frame in final.keys():
        result[frame]=innerkeys.copy()
        for i in range(len(final[frame])):
            if(final[frame][i][0]>threshold[i]):
                x=final[frame][i][1][0]
                y=final[frame][i][1][1]
                for j in values[i].keys():
                    new_x=round(final[frame][i][2]*(x+values[i][j][0]))
                    new_y=round(final[frame][i][2]*(y+values[i][j][1]))
                    result[frame][j]=(new_x,new_y)
    return result


def get_court_tracking(frames_dir, output_dir):
    #These are the thresholds identified for each template based on their distribution w.r.t the test video
    threshold=[40000000, 10000000, 9100000, 30000000, 6500000, 12000000, 40000000, 13000000, 8500000, 16000000, 700000, 3500000, 40000000]

    #These values represent the court points within each template that were manually picked
    values=[{'AL': (114,14),'BL': (34,119),'CL': (220,68)},
        {'DL': (18,31),'EL': (52,7)},
        {'FL': (42,10),'GL': (14,30)},
        {'HL': (317,66),'IL': (82,3), 'JL': (12,84)},
        {'KL': (21,7), 'LL': (7,21)},
        {'ML': (16,7)},
        {'AR': (126,19),'BR': (223,130),'CR': (3,75)},
        {'DR': (53,34),'ER': (22,12)},
        {'FR': (17,8),'GR': (44,26)},
        {'HR': (20,52),'IR': (244,5), 'JR': (311,87)},
        {'KR': (26,8), 'LR': (43,23)},
        {'MR': (22,11)},
        {'ZZ': (230,50)}]
    innerkeys={'AL':(),'BL':(),'CL':(),'DL':(),'EL':(),'FL':(),'GL':(),'HL':(), 'IL':(), 'JL':(), 'KL':(), 'LL':(), 'ML':(),
              'AR':(),'BR':(),'CR':(),'DR':(),'ER':(),'FR':(),'GR':(),'HR':(),'IR':(),'JR':(),'KR':(),'LR':(),'MR':(),'ZZ':()}
    final = court_templates(frames_dir)
    result = court_features(final, threshold, values, innerkeys)

    # Converting to JSON
    with open(os.path.join(output_dir, "court_tracking_results.json"), "w") as outfile:  
        json.dump(result, outfile)
    return


