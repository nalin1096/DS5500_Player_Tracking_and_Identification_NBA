import uuid

from django.shortcuts import render
from django.http import HttpResponseRedirect, HttpResponse

from .models import Video
from .forms import VideoForm
from .tasks import send_email_task


def index(request):
    lastvideo = Video.objects.last()
    videofile = lastvideo

    form = VideoForm(request.POST or None, request.FILES or None)
    if form.is_valid():
        new_video = form.save()
        print(new_video.id)
        send_email_task.delay(new_video.id)

    context = {
        'videofile': videofile,
        'form': form
    }

    return render(request, 'tracking/index.html', context)

def results(request):
    return render(request, 'tracking/results.html')

def video_results(request, results_id):
    video_obj = Video.objects.get(results_id = results_id)
    return render(request, 'tracking/video_results.html', {'processed_videofile': video_obj.processed_videofile, 'videofile': video_obj.videofile})
