#importing requirements
import cv2
import matplotlib.pyplot as plt
import numpy as np
from hmmlearn import hmm
from sklearn.cluster import KMeans
from scipy import stats

frames = []

def calc_hist(img):
    '''calculates b,g,r histograms of image'''
    bHist = cv2.calcHist([img],[0],None,[256],[0,256])
    gHist = cv2.calcHist([img],[1],None,[256],[0,256])
    rHist = cv2.calcHist([img],[2],None,[256],[0,256])
    return bHist,gHist,rHist

def fit_predict_HMM(X,y,lengths=None,n_components=3):
    '''fitting hmm to 2d array X and returning predictions on y'''
    model = hmm.GaussianHMM(n_components=3)
    model.fit(X,lengths=lengths)
    preds = model.predict(y)
    return preds

def check_output(frames,preds,n_classes):
    '''plotting images with their category as returned by shot segmentation'''
    output = list(zip(frames,preds))
    classes = {}
    for i in range(n_classes):
        classes[str(i)] = [x[0] for x in output if x[1]==i]
    lens = [len(classes[x]) for x in classes]
    maj = np.argmax(lens)
    others = list(set(range(n_classes))-set([maj]))
    for i in classes[str(maj)]:
        plt.imshow(i)
        #majority class should be gameplay
        plt.title('Maj class')
        plt.show()
    for j in others:
        for k in classes[str(j)]:
            plt.imshow(k)
            plt.title('Other class '+str(j))
            plt.show() 

def save_output(frames,preds,n_classes):
    '''saving images according to category returned by shot segmentation'''
    output = list(zip(frames,preds))
    #saving images to a dictionary with class as key
    classes = {}
    for i in range(n_classes):
        classes[str(i)] = [x[0] for x in output if x[1]==i]
    lens = [len(classes[x]) for x in classes]
    #majority length class is gameplay
    maj = np.argmax(lens)
    #savepath
    save_path = 'shot_segmentation/hmm_output/'

    folder_no = 1
    for i in classes:
        frames = classes[i]
        if i == str(maj):
            folder_name = 'gameplay'
            for j in range(len(frames)):
                cv2.imwrite(save_path+folder_name+"/"+str(j)+".jpg", frames[j])
        else:
            folder_name = 'other'+str(folder_no)
            for j in range(len(frames)):
                cv2.imwrite(save_path+folder_name+"/"+str(j)+".jpg", frames[j])
            folder_no += 1

videoFile = 'shot_segmentation/test1.mp4'
# videoFile = 'shot_segmentation/trimmed_shots.mp4'
sec = 0
frameRate = 1
cap = cv2.VideoCapture(videoFile)

bModes = []
gModes = []
rModes = []

while cap.isOpened(): 
    #setting current video position for 25fps capture
    sec = round(sec + frameRate,2)
    cap.set(cv2.CAP_PROP_POS_MSEC, sec*1000)
    hasFrames, image = cap.read()
    if hasFrames:      
        frames.append(image)  
        bHist,gHist,rHist = calc_hist(image)
        #adding mode of each histogram to list
        bModes.append(np.argmax(bHist))
        gModes.append(np.argmax(gHist))
        rModes.append(np.argmax(rHist))
    else:
        cap.release()

histArray = np.column_stack([bModes,gModes,rModes])
preds = fit_predict_HMM(histArray,histArray,n_components=3)
# check_output(frames,preds,3)
save_output(frames,preds,3)