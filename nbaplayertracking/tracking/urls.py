from django.urls import path

from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('video_results/<str:results_id>/', views.video_results, name='video_results'),
    path('results/', views.results, name='results')
]