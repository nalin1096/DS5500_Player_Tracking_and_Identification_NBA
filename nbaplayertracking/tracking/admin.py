from django.contrib import admin

from .models import Video

class VideoAdmin(admin.ModelAdmin):
    fieldsets = [
    (None, {'fields': ['results_id', 'email']}),
    ('Video Information', {'fields': ['season', 'home_team', 'videofile']}),
    ('Tracking Results', {'fields': ['player_tracking_file', 'court_tracking_file', 'ocr_file']}),
    ]

    list_display = ('email', 'videofile')

admin.site.register(Video, VideoAdmin)
