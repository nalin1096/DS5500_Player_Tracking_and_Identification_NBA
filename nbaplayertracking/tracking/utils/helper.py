import subprocess
import os

from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags


def create_frames(video_file, out_folder):
    process = subprocess.run(['ffmpeg', '-i', video_file, '-vf', 'fps=25', os.path.join(out_folder, 'out%07d.png')])
    return


def send_email_to_user(video_obj):
    subject = 'Basketball Tracking | Your video is ready!'
    context = {
        'results_url': 'localhost:8000/video_results/' + str(video_obj.results_id)
    }
    html_message = render_to_string('tracking/results_email.html', context=context)
    plain_message = strip_tags(html_message)
    from_email = 'Baskbetball Analytics <nalin1096@hotmail.com>'
    to = video_obj.email

    send_mail(
        subject,
        plain_message,
        from_email,
        [to],
        html_message=html_message
    )
