from celery import shared_task
from celery.utils.log import get_task_logger

from .models import Video

from .utils import court_tracking, ocr, team_classification, helper

import cv2
import os
import random
import string
from pathlib import Path
from time import sleep

from django.core.mail import send_mail
from django.core.files import File
from django.core.files.base import ContentFile
from django.conf import settings

logger = get_task_logger(__name__)

@shared_task
def get_tracking(id):

    video_obj = Video.objects.get(id=id)

    filepath = os.path.join(settings.BASE_DIR, video_obj.videofile.url[1:])
    filename = os.path.splitext(os.path.basename(filepath))[0]

    outdir = os.path.join(os.path.dirname(filepath), filename)
    Path(outdir).mkdir(parents=True, exist_ok=True)

    helper.preprocess_video(filepath, outdir)

    results_dir = os.path.join(settings.BASE_DIR, 'media/tracking/tracking_results', filename)
    Path(results_dir).mkdir(parents=True, exist_ok=True)

    # team_classification.get_team_classification(outdir, results_dir)
    
    court_tracking.get_court_tracking(outdir, results_dir)
    video_obj.court_tracking_file = os.path.join('tracking', 'tracking_results', filename, 'court_tracking_results.json')

    ocr.get_ocr(outdir, results_dir)
    video_obj.ocr_file = os.path.join('tracking', 'tracking_results', filename, 'ocr_results.json')

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
