import numpy as np
import easyocr
import cv2

#reading in test image and converting to grayscale for easier processing
i = 1
img = cv2.imread("test_imgs/"+str(i)+".jpg", cv2.IMREAD_GRAYSCALE)

#setting dimensions for cropping the lower quarter of the image
y,x = img.shape
x1,y1 = 0,round(0.75*y)
x2,y2 = x, y

#cropped image
cropped = img[y1:y2,x1:x2]

#loading english ocr reader
reader = easyocr.Reader(["en"])

#detecting text from cropped and full image
result_img = reader.readtext(img)
result_crop = reader.readtext(cropped)

#detecting text from cropped and full image - with inverted colors 
#goal is to reverse white/gray text on black as it is harder to recognize
result_img_inv = reader.readtext(np.invert(img))
result_crop_inv = reader.readtext(np.invert(cropped))

#compiling text and confidence of prediction from normal + inverted versions of the full and cropped images
text_img = []
text_crop = []
conf_img = []
conf_crop = []

#combining inverted and normal image results for full and cropped imgs
img_results = result_img + result_img_inv
cropped_results = result_crop + result_crop_inv

#sorting results by x coord 
sorted_img = sorted(img_results, key=lambda x:x[0][0][0])
sorted_crop = sorted(cropped_results, key=lambda x:x[0][0][0])

#miny denotes approx height at which scoreboard results start 
miny = min([x[0][0][1] for x in sorted_crop])+round(0.75*img.shape[0])

result_dict = {}

#creating dictionaries with key = first x,y coord of text, value = (text, confidence)
for i in sorted_img:
    if i[0][0][1] >= miny:
        k = str(i[0][0][0])
        if (k not in result_dict) and (i[2] >= 0.5):
            result_dict[k] = [(i[1],i[2])]
        elif (k in result_dict) and (i[2] >= 0.5):
            result_dict[k].append((i[1],i[2]))

for i in sorted_crop:
    k = str(i[0][0][0])
    if (k not in result_dict) and (i[2] >= 0.5):
        result_dict[k] = [(i[1],i[2])]
    elif (k in result_dict) and (i[2] >= 0.5):
        result_dict[k].append((i[1],i[2]))

final_text = []
final_pos = []
for x,y in result_dict.items():
    max_val = max(y)
    if max_val[0] not in final_text:
        final_text.append(max_val[0])
        final_pos.append(round(float(x)))


[y[1] for y in sorted(list(zip(final_pos, final_text)),key=lambda x:x[0])]