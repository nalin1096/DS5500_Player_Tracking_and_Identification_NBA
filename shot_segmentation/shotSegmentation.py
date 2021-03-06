#importing requirements
import cv2
import matplotlib.pyplot as plt
import numpy as np
from hmmlearn import hmm
from sklearn.cluster import KMeans
from scipy import stats

def calc_hist(img):
    '''calculates b,g,r histograms of image'''
    bHist = cv2.calcHist([img],[0],None,[256],[0,256])
    gHist = cv2.calcHist([img],[1],None,[256],[0,256])
    rHist = cv2.calcHist([img],[2],None,[256],[0,256])
    return bHist,gHist,rHist

def findMean(hist):
    hist = np.reshape(hist,(256,))
    bins = list(range(256))
    return (np.dot(hist,bins))/sum(hist)

def findMedian(hist):
    hist = np.reshape(hist,(256,))
    median = sum(hist)/2
    total_sum = 0
    for i in range(len(hist)):
        total_sum+=hist[i]
        if median <= total_sum:
            return i

def fit_predict_HMM(X,y,lengths=None,n_components=3):
    '''fitting hmm to 2d array X and returning predictions on y'''
    model = hmm.GaussianHMM(n_components=n_components)
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

    print("Total no. of frames in video", len(frames))

    print("Preds", preds)

    for x in classes:
        print("Class", x)
        print("No. of frames", len(classes[x]))

    save_no = 1
    for i in classes:
        frames = classes[i]
        height , width , layers =  frames[0].shape
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        if i == str(maj):
            save_name = 'gameplay'
            video = cv2.VideoWriter(save_path+save_name+'.mp4',fourcc,1,(width,height))
            for j in range(len(frames)):
                # cv2.imwrite(save_path+folder_name+"/"+str(j)+".jpg", frames[j])
                video.write(frames[j])
        else:
            save_name = 'other'+str(save_no)
            video = cv2.VideoWriter(save_path+save_name+'.mp4',fourcc,1,(width,height))
            for j in range(len(frames)):
                # cv2.imwrite(save_path+folder_name+"/"+str(j)+".jpg", frames[j])
                video.write(frames[j])
            save_no += 1
    cv2.destroyAllWindows()
    video.release()

def train_predict(videoFile,sec=0,frameRate=0.04):
    frames = []
    cap = cv2.VideoCapture(videoFile)

    bArray = []
    gArray = []
    rArray = []

    while cap.isOpened(): 
        #setting current video position for 25fps capture
        sec = round(sec + frameRate,2)
        cap.set(cv2.CAP_PROP_POS_MSEC, sec*1000)
        hasFrames, image = cap.read()
        if hasFrames:      
            frames.append(image)  
            bHist,gHist,rHist = calc_hist(image)
            #adding mode of each histogram to list
            bArray.append(np.argmax(bHist))
            gArray.append(np.argmax(gHist))
            rArray.append(np.argmax(rHist))
            # # adding mean of each histogram to list
            # bArray.append(findMean(bHist))
            # gArray.append(findMean(gHist))
            # rArray.append(findMean(rHist))
            # # adding median of each histogram to list
            # bArray.append(findMedian(bHist))
            # gArray.append(findMedian(gHist))
            # rArray.append(findMedian(rHist))
        else:
            cap.release()

    histArray = np.column_stack([bArray,gArray,rArray])
    preds = fit_predict_HMM(histArray,histArray,n_components=3)
    return preds
        
if __name__ == '__main__':
    
    # videoFile = 'shot_segmentation/test1.mp4'
    # videoFile = 'shot_segmentation/trimmed_shots.mp4'
    videoFile = 'shot_segmentation/shots2.mp4'
    # videoFile = 'shot_segmentation/transitions2.mp4'
    # videoFile = 'shot_segmentation/other_transitions.mp4'
    
    sec = 0
    frameRate = 0.04
    
    preds = train_predict(videoFile,sec,frameRate)
    print(preds)
    # check_output(frames,preds,3)
    # save_output(frames,preds,3)


