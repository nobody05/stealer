from django.urls import path

from core import apis
from route import controller

urlpatterns = [
    path('list', apis.video_mapper, name='list'),
    path('fetch', apis.fetch, name='fetch'),
    path('download2', apis.download, name='download2'),
    path('info', controller.get_info, name='info'),
    path('watermark_removal', controller.watermark_removal, name='watermark_removal'),
    path('video_screenshot', controller.video_screenshot, name='video_screenshot'),
    path('video_convert_mp3', controller.video_convert_mp3, name='video_convert_mp3'),
    path('text2audio', controller.text2audio, name='text2audio'),
    path('text2image', controller.text2image, name='text2image'),
    path('get_ali_audio_models', controller.get_ali_audio_models, name='get_ali_audio_models'),
    path('download', controller.download_file, name='download'),
]
