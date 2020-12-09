import os
import random
import string
import uuid
from pathlib import Path

import dramatiq
from django.conf import settings

from .models import Video
from .utils import shot_segmentation, court_tracking, ocr, team_classification, helper, \
    player_tracking_transformation, player_tracking_smoothing


@dramatiq.actor
def get_tracking(id):

    id = uuid.UUID(id)
    # get video information
    video_obj = Video.objects.get(id=id)

    filepath = os.path.join(settings.BASE_DIR, video_obj.videofile.url[1:])
    filename = os.path.splitext(os.path.basename(filepath))[0]

    # create frames from video
    frames_dir = os.path.join(os.path.dirname(filepath), filename, 'all_frames')
    Path(frames_dir).mkdir(parents=True, exist_ok=True)
    helper.create_frames(filepath, frames_dir)

    # shot segmentation
    segmented_frames_dir = os.path.join(os.path.dirname(filepath), filename, 'segmented_frames')
    Path(segmented_frames_dir).mkdir(parents=True, exist_ok=True)
    shot_segmentation.shot_segmentation(frames_dir, segmented_frames_dir)

    results_dir = os.path.join(settings.BASE_DIR, 'media/tracking/tracking_results', filename)
    Path(results_dir).mkdir(parents=True, exist_ok=True)

    # Team classification
    team_classification.get_team_classification(segmented_frames_dir, results_dir)
    player_tracking_filepath = os.path.join('tracking', 'tracking_results', filename, 'player_tracking_results.json')
    video_obj.player_tracking_file = player_tracking_filepath

    # Court Tracking
    court_tracking.get_court_tracking(segmented_frames_dir, results_dir)
    court_tracking_filepath = os.path.join('tracking', 'tracking_results', filename, 'court_tracking_results.json')
    video_obj.court_tracking_file = court_tracking_filepath

    # Scoreboard Tracking
    ocr.get_ocr(segmented_frames_dir, results_dir)
    ocr_filepath = os.path.join('tracking', 'tracking_results', filename, 'ocr_results.json')
    video_obj.ocr_file = ocr_filepath

    # Post Processing
    player_tracking_transformation.postprocess_coordinates(os.path.join(settings.BASE_DIR, 'media', player_tracking_filepath),
                                                           os.path.join(settings.BASE_DIR, 'media', court_tracking_filepath),
                                                           results_dir)
    player_tracking_transformation_filepath = os.path.join('tracking', 'tracking_results',
                                                           filename, 'player_tracking_transformation_results.json')
    video_obj.player_tracking_transformation_file = player_tracking_transformation_filepath

    # Player Smoothing
    player_tracking_smoothing.coordinate_smoothing(os.path.join(settings.BASE_DIR, 'media', player_tracking_transformation_filepath),
                                                   results_dir)
    player_tracking_smoothing_filepath = os.path.join('tracking', 'tracking_results',
                                                      filename, 'player_tracking_smoothing_results.json')
    video_obj.player_tracking_smoothing_file = player_tracking_smoothing_filepath

    # create unique ID for video
    video_obj.results_id = ''.join(random.choices(string.ascii_uppercase + string.digits, k=32))

    helper.send_email_to_user(video_obj)

    video_obj.save()

    return 
