from celery import shared_task
from celery.utils.log import get_task_logger

from .models import Video

import cv2
import os
import random
import string
from time import sleep

from django.core.mail import send_mail
from django.core.files import File
from django.core.files.base import ContentFile
from django.conf import settings

logger = get_task_logger(__name__)

@shared_task
def send_email_task(id):
    video_obj = Video.objects.get(id=id)

    logger.info(settings.BASE_DIR)
    filepath = os.path.join(settings.BASE_DIR, video_obj.videofile.url[1:])
    filename = os.path.splitext(os.path.basename(filepath))[0]

    outdir = os.path.dirname(filepath)
    outfilename = filename + '_processed.mp4'
    outfilepath = os.path.join(outdir, outfilename)

    logger.info(filepath)
    logger.info(video_obj.videofile.url)
    logger.info(video_obj.email)

    cap = cv2.VideoCapture(filepath)

    ret, frame = cap.read()
    logger.info('ret =', ret, 'W =', frame.shape[1], 'H =', frame.shape[0], 'channel =', frame.shape[2])

    fps = 20.0
    framesize = (frame.shape[1], frame.shape[0])
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')

    out = cv2.VideoWriter(outfilepath, fourcc, fps, framesize, 0)

    while cap.isOpened():
        ret, frame = cap.read()

        # check for successfulness of cap.read()
        if not ret: break

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        frame = gray

        # Save the video
        out.write(frame)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    out.release()
    cv2.destroyAllWindows()

    video_obj.processed_videofile = os.path.join('tracking', 'videos', outfilename)
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
