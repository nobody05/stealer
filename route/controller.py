import json
import logging
import subprocess
from typing import Union, Optional, Any

from django.http import *
from django.shortcuts import render
from core import handler_mapper, cache, vid_download
from core.model import ErrorResult
from core.type import Video
from tools import store
import os
import ffmpeg

logger = logging.getLogger('request')


def video_convert_mp3(request):
    basedir = os.environ['video_screenshot_basedir']
    output_dir = basedir + "convert_output/"
    save_dir = basedir + "convert_save/"

    filename = request.GET.get("file_name")
    save_file = save_dir + filename

    logger.info(
        'video_convert_mp3-getrequest-filename{}--save_file{}'.format(filename, save_file))

    if os.path.exists(save_file) is False:
        return HttpResponse(json.dumps({
            "code": 91,
            'msg': 'file not found'
        }))

    try:
        probe = ffmpeg.probe(save_file)
        video_stream = next((stream for stream in probe['streams'] if stream['codec_type'] == 'video'), None)

        if video_stream is None:
            return HttpResponse(json.dumps({
                "code": 92,
                'msg': 'file empty'
            }))

        video_duration = video_stream.get("duration", 0)
        if float(video_duration) < 1:
            return HttpResponse(json.dumps({
                "code": 93,
                'msg': 'file length empty'
            }))

        output_mp3file = filename + ".mp3"
        stream = ffmpeg.input(save_file)
        stream = ffmpeg.output(stream, output_dir + output_mp3file)
        ffmpeg.run(stream)

    except Exception as e:
        logger.info('controller.video_convert_mp3.upload fail e{}'.format(str(e)))

        return HttpResponse(json.dumps({
            "code": 94,
            'msg': 'image process fail'
        }))

    return HttpResponse(json.dumps({
        'code': 200,
        'msg': "",
        'data': {
            "file": output_mp3file
        }
    }))


def video_screenshot(request):
    # basedir = "./screenshot/"
    basedir = os.environ['video_screenshot_basedir']
    output_dir = basedir + "output/"
    save_dir = basedir + "save/"

    filename = request.GET.get("file_name")
    snapshot_seconds = request.GET.get("snapshot_seconds")

    if snapshot_seconds is None or len(snapshot_seconds) == 0:
        return HttpResponse(json.dumps({
            "code": 90,
            'msg': 'argument empty'
        }))
    snapshot_seconds_slice = snapshot_seconds.split(",")
    save_file = save_dir + filename

    logger.info(
        'video_screenshot-getrequest-filename{}--save_file{}---snapshot_seconds{}'.format(filename, save_file,
                                                                                          snapshot_seconds))

    if os.path.exists(save_file) is False:
        return HttpResponse(json.dumps({
            "code": 91,
            'msg': 'file not found'
        }))

    thumb_slices = []
    try:
        probe = ffmpeg.probe(save_file)
        video_stream = next((stream for stream in probe['streams'] if stream['codec_type'] == 'video'), None)

        if video_stream is None:
            return HttpResponse(json.dumps({
                "code": 92,
                'msg': 'file empty'
            }))

        video_duration = video_stream.get("duration", 0)
        if float(video_duration) < 1:
            return HttpResponse(json.dumps({
                "code": 93,
                'msg': 'file length empty'
            }))

        for seconds in snapshot_seconds_slice:
            if int(seconds) > float(video_duration):
                continue

            if int(seconds) < 10:
                s = "00:00:0" + str(seconds)
            else:
                s = "00:00:" + str(seconds)

            thumbnail_file = filename + "_" + str(seconds) + ".png"

            (ffmpeg.input(save_file, ss=s)  # 从视频的15秒处提取缩略图
             .output(output_dir + "/" + thumbnail_file, vframes=1)  # 设置输出文件名和帧数
             .run())

            thumb_slices.append(thumbnail_file)

    except Exception as e:
        logger.info('controller.watermark_removal.upload fail e{}'.format(str(e)))

        return HttpResponse(json.dumps({
            "code": 94,
            'msg': 'image process fail'
        }))

    return HttpResponse(json.dumps({
        'code': 200,
        'msg': "",
        'data': {
            "thumbs": thumb_slices
        }
    }))


def watermark_removal(request):
    basedir = os.environ['watermark_removal_basedir']
    output_dir = basedir + "output/"
    save_dir = basedir + "save/"

    filename = request.GET.get("file_name")
    save_file = save_dir + filename
    output_file = output_dir + filename

    logger.info(
        'watermark-removal-getrequest-filename{}--save_file{}---output_file{}'.format(filename, save_file, output_file))

    if os.path.exists(save_file) is False:
        return HttpResponse(json.dumps({
            "code": 92,
            'msg': 'file not found'
        }))

    try:
        os.environ['PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION'] = 'python'
        working_dir = "/www/wwwroot/watermark-removal"

        subprocess.run(
            ["/usr/local/python3.7/bin/python3.7", "/www/wwwroot/watermark-removal/main.py", "--image", f"{save_file}",
             "--output",
             f"{output_file}",
             "--checkpoint_dir", "/www/wwwroot/watermark-removal/model/", "--watermark_type", "istock"],
            cwd=working_dir)
    except Exception as e:
        logger.info('controller.watermark_removal.upload fail e{}'.format(str(e)))

        return HttpResponse(json.dumps({
            "code": 93,
            'msg': 'image process fail'
        }))

    if os.path.exists(output_file) is False:
        return HttpResponse(json.dumps({
            "code": 94,
            'msg': 'file not found2'
        }))

    return HttpResponse(json.dumps({
        'code': 200,
        'msg': "",
        'data': {
            "image": filename
        }
    }))


def get_info(request):
    url = request.GET.get('url')
    if url is None:
        return HttpResponseBadRequest(ErrorResult.URL_NOT_PRESENT.get_data())

    vtype, url = get_vtype(url)
    if vtype is None:
        return HttpResponseBadRequest(ErrorResult.URL_NOT_INCORRECT.get_data())

    # token = store.get_token(vtype, url)
    # info = cache.get(token)
    info = None
    # if info is not None:
    #     dic = info.to_dict()
    #     dic['token'] = token
    #     return HttpResponse(json.dumps(dic))

    logger.info(f'get {vtype.value} video info ==> {url}.')

    service = handler_mapper.get_service(vtype)
    result = service.get_info(url)

    if result.is_success():
        info = result.get_data()
        # cache.save(token, info)
        dic = info.to_dict()
        dic['token'] = ""
        return HttpResponse(json.dumps(dic))
    return HttpResponseServerError(result.get_data())


def download_file(request):
    url = request.GET.get('url')
    token = request.GET.get('token')
    if url is None and token is None:
        return HttpResponseBadRequest(ErrorResult.URL_NOT_PRESENT.get_data())
    if url is not None:
        vtype, url = get_vtype(url)
        token = store.get_token(vtype, url)

    info = cache.get(token)
    if info is None:
        return HttpResponseNotFound(ErrorResult.VIDEO_INFO_NOT_FOUNT.get_data())

    logger.info(f'download {info.platform.value} ==> {info.desc}.')
    return vid_download.download(info)


def fetch(vtype: Video, request):
    url = request.GET.get('url')
    if url is None:
        return HttpResponseBadRequest(ErrorResult.URL_NOT_PRESENT.get_data())

    vtype = check_vtype(vtype, url)
    if vtype is None:
        return HttpResponseBadRequest(ErrorResult.URL_NOT_INCORRECT.get_data())

    service = handler_mapper.get_service(vtype)
    logger.info('fetch {} <== {}.'.format(vtype.label, url))
    result = service.fetch(url)
    if result.is_success():
        return HttpResponse(result.get_data())
    return HttpResponseServerError(result.get_data())


def download(vtype: Video, request):
    url = request.GET.get('url')
    if url is None:
        return HttpResponseBadRequest(ErrorResult.URL_NOT_PRESENT.get_data())

    vtype = check_vtype(vtype, url)
    if vtype is None:
        return HttpResponseBadRequest(ErrorResult.URL_NOT_INCORRECT.get_data())

    service = handler_mapper.get_service(vtype)
    logger.info('download {} <== {}.'.format(vtype.label, url))
    response = service.download(url)
    return response


def get_vtype(url: str) -> (Optional[Video], str):
    for v, service in handler_mapper.service_mapper.items():
        share_url = service.get_url(url)
        if share_url:
            return v, share_url
    return None, ''


def check_vtype(vtype: Video, url: str) -> Union[Optional[Video], Any]:
    if vtype is not Video.AUTO:
        return vtype

    for v, service in handler_mapper.service_mapper.items():
        if service.get_url(url):
            return v
    return None
