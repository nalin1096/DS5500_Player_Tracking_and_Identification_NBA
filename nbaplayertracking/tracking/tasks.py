# from celery import shared_task
# from celery.utils.log import get_task_logger

import dramatiq

from .models import Video
from .utils import shot_segmentation, court_tracking, ocr, team_classification, helper

import os
import uuid
import random
import string
from pathlib import Path

from django.core.mail import send_mail
from django.conf import settings

# logger = get_task_logger(__name__)


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
    video_obj.player_tracking_file = os.path.join('tracking', 'tracking_results', filename, 'player_tracking_results.json')
    
    # Court Tracking
    court_tracking.get_court_tracking(segmented_frames_dir, results_dir)
    video_obj.court_tracking_file = os.path.join('tracking', 'tracking_results', filename, 'court_tracking_results.json')

    # Scoreboard Tracking
    ocr.get_ocr(segmented_frames_dir, results_dir)
    video_obj.ocr_file = os.path.join('tracking', 'tracking_results', filename, 'ocr_results.json')

    # create unique ID for video
    video_obj.results_id = ''.join(random.choices(string.ascii_uppercase + string.digits, k=32))

    send_mail(
        'Your video is ready!',
        'Please go to the following link \n\n localhost:8000/video_results/' + str(video_obj.results_id),
        'nalin1096@hotmail.com',
        [video_obj.email],
        fail_silently=False,
    )

    video_obj.save()

    return 
