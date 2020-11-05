import json
import numpy as np
from collections import defaultdict
import cv2
import glob
from sklearn.cluster import KMeans

BOX_RADIUS = 15

def reformat_json(json):
    #Build a new dictionary for the desired format
    new_json = defaultdict(dict)
    for i in range(len(json)):
        #get each component
        image_id = json[i]['image_id']
        idx = json[i]['idx']
        keypoints = json[i]['keypoints']
        score = json[i]['score']
        bbox = json[i]['box']
        category_id = json[i]['category_id']
        #define another layer deep
        new_json[image_id][idx] = {}
        #set each nested component to its value
        new_json[image_id][idx]['keypoints'] = keypoints
        new_json[image_id][idx]['score'] = score
        new_json[image_id][idx]['bbox'] = bbox
        new_json[image_id][idx]['category_id'] = category_id
        #new_json[image_id][idx]['image_id'] = image_id
        #new_json[image_id][idx]['pose_tracking_id'] = idx
    return new_json

def trim_low_confidence(json):
    #initial trim using the confidence scores - < 2 looks safe
    new_json = json.copy()
    for frame_id, values in json.items():
        for player_id, player_data in values.copy().items():
            if player_data['score'] < 2:
                #cut out that player
                new_json[frame_id].pop(player_id)
    return new_json

def get_clusters(frame, json, frame_id, model = None):

    #build features matrix for kmeans
    rows = []
    for player_id in json[frame_id]:
        #extract bbox coordinates
        bbox_coords = json[frame_id][player_id]['bbox']
        x = round(bbox_coords[0])
        y = round(bbox_coords[1])
        w = round(bbox_coords[2])
        h = round(bbox_coords[3])
        # create mask for bbox
        mask = np.zeros(frame.shape[:2], np.uint8)
        mask[y:y+h, x:x+w] = 255

        #convert to image
        mask_img = cv2.bitwise_and(frame,frame,mask = mask)

        #extract mean and standard deviation from each channel
        (means, stds) = cv2.meanStdDev(mask_img)
        row = np.concatenate([means, stds]).flatten()
        rows.append(row)

    #fit the clusters on the first frame
    if frame_id == 'out0000001.png':
        kmeans = KMeans(n_clusters = 2)
        kmeans_model = kmeans.fit(rows)
        clusters = kmeans_model.labels_
        #return the model to use on subsequent frames as well as the labels for the first frame
        return kmeans_model, clusters
    #then not the first frame so just compute the clusters
    else:
        clusters = model.predict(rows)
        return clusters

def trim_json(json, frame_id, clusters, players_cluster):
    for i, player_id in enumerate(json[frame_id].copy()):
        #if the entity is not in the players cluster
        if clusters[i] != players_cluster:
            #drop them
            json[frame_id].pop(player_id)
        else:
            pass
    return json

def separate_players_and_noise(json, all_images):
    if len(json) != len(all_images):
        print('Json and images lengths vary.')
    else:
        for image_id, image in zip(json, all_images):
            #if first frame
            if image_id == 'out0000001.png':
                #get kmeans model and clusters for frame 1
                model, clusters = get_clusters(image, json, image_id)
                #grab max cluster representing the players cluster - players will be more colorful
                centers = model.cluster_centers_
                players_cluster = np.argmax(np.max(centers, axis = 1))
                #remove any entities not in the players cluster and return updated json
                json = trim_json(json, image_id, clusters, players_cluster)
            else:
                #for every subsequent frame compute the clusters using the model fit in frame 1
                clusters = get_clusters(image, json, image_id, model)
                #and trim any entity not in players cluster
                json = trim_json(json, image_id, clusters, players_cluster)
        #return trimmed down json
        return json

def cluster_players(frame, json, frame_id, model = None):

    #similar process as first clustering but now to classify teams using center area of bbox
    rows = []
    for player_id in json[frame_id]:
        #extract bbox coordinates
        bbox_coords = json[frame_id][player_id]['bbox']
        x = round(bbox_coords[0])
        y = round(bbox_coords[1])
        w = round(bbox_coords[2])
        h = round(bbox_coords[3])

        #crop the image to the bbox
        crop_img = frame[y:y+h, x:x+w].copy()
        #get the bottom right coords of the bbox
        x_right = x+w
        y_right = y+h
        #calculate the center of the bbox
        x_center = int((x + x_right) / 2.0)
        y_center = int((y + y_right) / 2.0)

        #create square mask that radiates out from the center at a certain radius
        mask = np.zeros(frame.shape[:2], np.uint8)
        mask[y_center - BOX_RADIUS : y_center + BOX_RADIUS, x_center - BOX_RADIUS : x_center + BOX_RADIUS] = 255

        #convert to image
        mask_img = frame[y_center - BOX_RADIUS : y_center + BOX_RADIUS, x_center - BOX_RADIUS : x_center + BOX_RADIUS].copy()

        #extract mean and standard deviation from each channel
        (means, stds) = cv2.meanStdDev(mask_img)
        row = np.concatenate([means, stds]).flatten()
        rows.append(row)

    #fit the clusters on the first frame
    if frame_id == 'out0000001.png':
        #one cluster for each team
        kmeans = KMeans(n_clusters = 2)
        kmeans_model = kmeans.fit(rows)
        clusters = kmeans_model.labels_
        #return the model to use on subsequent frames as well as the labels for the first frame
        return kmeans_model, clusters
    else:
        clusters = model.predict(rows)
        return clusters

def classify_teams(json, all_images):
    for image_id, image in zip(json, all_frames):
        if image_id == 'out0000001.png':
            model, clusters = cluster_players(image, json, image_id)
            for i, player_id in enumerate(json[image_id].copy()):
                #set the cluster in our json as the player's team
                json[image_id][player_id]['team'] = int(clusters[i])
        else:
            clusters = cluster_players(image, json, image_id, model)
            for i, player_id in enumerate(json[image_id].copy()):
                #set the cluster in our json as the player's team
                json[image_id][player_id]['team'] = int(clusters[i])
    return json

#histograms show more confidence in finding hips than ankles so will use average of hips to get center of mass x,y
def center_of_mass(json):
    for image_id in json:
        for player_id in json[image_id]:
            lhip_x = json[image_id][player_id]['keypoints'][33]
            lhip_y = json[image_id][player_id]['keypoints'][34]
            #lhip_conf = json[image_id][player_id]['keypoints'][35]

            rhip_x = json[image_id][player_id]['keypoints'][36]
            rhip_y = json[image_id][player_id]['keypoints'][37]
            #rhip_conf = json[image_id][player_id]['keypoints'][38]

            hip_x_avg = (lhip_x + rhip_x) / 2.0
            hip_y_avg = (lhip_y + rhip_x) / 2.0

            json[image_id][player_id]['x'] = hip_x_avg
            json[image_id][player_id]['y'] = hip_y_avg
    return json

if __name__ == '__main__':
    #load in json results from alphapose
    with open('./data/alphapose-results.json') as input:
        jsonData = json.load(input)

    #reform the json input into the desired structure
    our_player_tracking_all = reformat_json(jsonData)

    #first trim, removes low confidence score entities which mostly refer to noise
    our_player_tracking = trim_low_confidence(our_player_tracking_all)

    #read in the frames split from FFmpeg on the video input as RGB
    all_frames = [cv2.cvtColor(cv2.imread(image), cv2.COLOR_BGR2RGB) for image in sorted(glob.glob('./test_images/*.png'))]

    #first clustering approach to distinguish the players from fans, refs, bench, etc.
    our_player_tracking = separate_players_and_noise(our_player_tracking, all_frames)

    #second clustering approach to classify the two teams on the court
    our_player_tracking = classify_teams(our_player_tracking, all_frames)

    #calculate center of mass position for each player
    our_player_tracking = center_of_mass(our_player_tracking)

    #export and pass along the final player tracking json output
    with open('./player_tracking_w_teams.json', 'w') as output:
        json.dump(our_player_tracking, output)
