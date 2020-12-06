import os
import glob
from shutil import copyfile
import numpy as np

from keras.applications.vgg16 import VGG16, preprocess_input
from keras.models import Model
from keras.preprocessing.image import load_img, img_to_array

from sklearn.manifold import TSNE
from sklearn.cluster import DBSCAN


class ShotSegmentation:
    def __init__(self, frames_dir):
        self.frames_dir = frames_dir
        self.frame_ids, self.frames = self.get_frames()
        self.encoded_frames = None

        self.tsne_X = None
        self.db = None

    def get_frames(self):
        frames = []
        frame_ids = sorted(glob.glob(os.path.join(self.frames_dir, '*.png')))

        for frame_id in frame_ids:
            frame = load_img(frame_id, target_size=(224, 224))
            frame = img_to_array(frame)
            frame = preprocess_input(frame)
            frames.append(frame)

        return frame_ids, np.array(frames)

    def get_clusters(self, perplexity=50, eps=7, min_samples=10):
        # Encoding frames using VGG16
        vgg16 = VGG16()
        vgg16 = Model(inputs=vgg16.inputs, outputs=vgg16.layers[-2].output)

        self.encoded_frames = vgg16.predict(self.frames)

        # TSNE Reduction
        tsne = TSNE(n_components=2, init='random',
                    random_state=0, perplexity=perplexity)
        self.tsne_X = tsne.fit_transform(self.encoded_frames)

        # DBSCAN clustering
        self.db = DBSCAN(eps=eps, min_samples=min_samples).fit(self.tsne_X)

        return self.db.labels_


def shot_segmentation(frames_dir, out_dir):
    ss = ShotSegmentation(frames_dir)
    labels = ss.get_clusters()

    def get_frame_id(frame_id):
        return 'out%07d.png' % frame_id

    frame_num = 1
    for label, frame in zip(labels, ss.frame_ids):
        if label == 0 or label == -1:
            outfile = os.path.join(out_dir, get_frame_id(frame_num))
            copyfile(frame, outfile)
            frame_num += 1



