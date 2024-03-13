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
import ffmpeg
import os
from http import HTTPStatus
from urllib.parse import urlparse, unquote
from pathlib import PurePosixPath
import requests
from dashscope import ImageSynthesis

logger = logging.getLogger('request')


def get_ali_audio_models(request):
    model_list = [
        {"model": "sambert-zhinan-v1", "people": "广告男声", "lang": "中文+英文", "sample_rate": "48k"},
        {"model": "sambert-zhiqi-v1", "people": "温柔女声", "lang": "中文+英文", "sample_rate": "48k"},
        {"model": "sambert-zhichu-v1", "people": "舌尖男声", "lang": "中文+英文", "sample_rate": "48k"},
        {"model": "sambert-zhide-v1", "people": "新闻男声", "lang": "中文+英文", "sample_rate": "48k"},
        {"model": "sambert-zhijia-v1", "people": "标准女声", "lang": "中文+英文", "sample_rate": "48k"},
        {"model": "sambert-zhiru-v1", "people": "新闻女声", "lang": "中文+英文", "sample_rate": "48k"},
        {"model": "sambert-zhiquan-v1", "people": "资讯女声", "lang": "中文+英文", "sample_rate": "48k"},
        {"model": "sambert-zhixiang-v1", "people": "磁性男声", "lang": "中文+英文", "sample_rate": "48k"},
        {"model": "sambert-zhiwei-v1", "people": "萝莉女声", "lang": "中文+英文", "sample_rate": "48k"},
        {"model": "sambert-zhihao-v1", "people": "咨询男声", "lang": "中文+英文", "sample_rate": "16k"},
        {"model": "sambert-zhijing-v1", "people": "严厉女声", "lang": "中文+英文", "sample_rate": "16k"},
        {"model": "sambert-zhiming-v1", "people": "诙谐男声", "lang": "中文+英文", "sample_rate": "16k"},
        {"model": "sambert-zhimo-v1", "people": "情感男声", "lang": "中文+英文", "sample_rate": "16k"},
        {"model": "sambert-zhina-v1", "people": "浙普女声", "lang": "中文+英文", "sample_rate": "16k"},
        {"model": "sambert-zhishu-v1", "people": "资讯男声", "lang": "中文+英文", "sample_rate": "16k"},
        {"model": "sambert-zhistella-v1", "people": "知性女声", "lang": "中文+英文", "sample_rate": "16k"},
        {"model": "sambert-zhitong-v1", "people": "电台女声", "lang": "中文+英文", "sample_rate": "16k"},
        {"model": "sambert-zhxiao-v1", "people": "资讯女声", "lang": "中文+英文", "sample_rate": "16k"},
        {"model": "sambert-zhiya-v1", "people": "严厉女声", "lang": "中文+英文", "sample_rate": "16k"},
        {"model": "sambert-zhiye-v1", "people": "青年男声", "lang": "中文+英文", "sample_rate": "16k"},
        {"model": "sambert-zhiying-v1", "people": "软萌童声", "lang": "中文+英文", "sample_rate": "16k"},
        {"model": "sambert-zhiyuan-v1", "people": "知心姐姐", "lang": "中文+英文", "sample_rate": "16k"},
        {"model": "sambert-zhigui-v1", "people": "直播女声", "lang": "中文+英文", "sample_rate": "16k"},
        {"model": "sambert-zhisuo-v1", "people": "自然男声", "lang": "中文+英文", "sample_rate": "16k"},
        {"model": "sambert-zhimiao-emo-v1", "people": "多种情感女声", "lang": "中文+英文", "sample_rate": "16k"},
        {"model": "sambert-zhimao-v1", "people": "直播女声", "lang": "中文+英文", "sample_rate": "16k"},
        {"model": "sambert-zhilun-v1", "people": "悬疑解说", "lang": "中文+英文", "sample_rate": "16k"},
        {"model": "sambert-zhifei-v1", "people": "激昂解说", "lang": "中文+英文", "sample_rate": "16k"},
        {"model": "sambert-zhida-v1", "people": "标准男声", "lang": "中文+英文", "sample_rate": "16k"},
        {"model": "sambert-camila-v1", "people": "西班牙语女声", "lang": "西班牙语", "sample_rate": "16k"},
        {"model": "sambert-perla-v1", "people": "意大利语女声", "lang": "意大利语", "sample_rate": "16k"},
        {"model": "sambert-indah-v1", "people": "印尼语女声", "lang": "印尼语", "sample_rate": "16k"},
        {"model": "sambert-clara-v1", "people": "法语女声", "lang": "法语", "sample_rate": "16k"},
        {"model": "sambert-hanna-v1", "people": "德语女声", "lang": "德语", "sample_rate": "16k"},
        {"model": "sambert-beth-v1", "people": "咨询女声", "language": "美式英文", "sample_rate": "16k"},
        {"model": "sambert-betty-v1", "people": "客服女声", "language": "美式英文", "sample_rate": "16k"},
        {"model": "sambert-cally-v1", "people": "自然女声", "language": "美式英文", "sample_rate": "16k"},
        {"model": "sambert-cindy-v1", "people": "对话女声", "language": "美式英文", "sample_rate": "16k"},
        {"model": "sambert-eva-v1", "people": "陪伴女声", "language": "美式英文", "sample_rate": "16k"},
        {"model": "sambert-donna-v1", "people": "教育女声", "language": "美式英文", "sample_rate": "16k"},
        {"model": "sambert-brian-v1", "people": "客服男声", "language": "美式英文", "sample_rate": "16k"},
        {"model": "sambert-waan-v1", "people": "泰语女声", "language": "泰语", "sample_rate": "16k"}
    ]
    return HttpResponse(json.dumps({
        'code': 200,
        'msg': "",
        'data': {
            "list": model_list
        }
    }))


def text2image(request):
    basedir = os.environ['textimage_basedir']
    prompt = request.GET.get("prompt")
    image_number = int(request.GET.get("number"))

    if len(prompt) == 0:
        return HttpResponse(json.dumps({
            "code": 80,
            'msg': 'prompt empty'
        }))

    if image_number > 4:
        return HttpResponse(json.dumps({
            "code": 81,
            'msg': 'image max 4'
        }))
    logger.info(
        'controller.text2image.request-prompt:{}-basedir:{}-image_number:{}'.format(basedir, prompt, image_number))

    rsp = ImageSynthesis.call(model=ImageSynthesis.Models.wanx_v1,
                              api_key=os.environ['DASHSCOPE_API_KEY'],
                              prompt=prompt,
                              n=image_number,
                              size='1024*1024')

    logger.info('controller.text2image.response:{}'.format(str(rsp)))

    file_list = []
    if rsp.status_code == HTTPStatus.OK:

        for result in rsp.output.results:
            file_name = PurePosixPath(unquote(urlparse(result.url).path)).parts[-1]
            full_name = basedir + '%s' % file_name

            try:
                with open(full_name, 'wb+') as f:
                    f.write(requests.get(result.url).content)
            except Exception as e:
                logger.info('controller.text2image.save fail e:{}'.format(str(e)))

                return HttpResponse(json.dumps({
                    "code": 94,
                    'msg': 'text process fail'
                }))

            file_list.append(file_name)

    else:
        # print('Failed, status_code: %s, code: %s, message: %s' %
        #       (rsp.status_code, rsp.code, rsp.message))
        return HttpResponse(json.dumps({
            "code": 99,
            'msg': 'text process fail'
        }))

    if len(file_list) > 0:
        return HttpResponse(json.dumps({
            'code': 200,
            'msg': "",
            'data': {
                "file_list": file_list
            }
        }))

    return HttpResponse(json.dumps({
        'code': 200,
        'msg': "",
        'data': {
            "file_list": file_list
        }
    }))


def text2audio(request):
    import dashscope
    from dashscope.audio.tts import SpeechSynthesizer

    text = request.GET.get("text")
    if len(text) > 2000:
        return HttpResponse(json.dumps({
            "code": 89,
            'msg': 'text too long'
        }))

    model = request.GET.get("model", "sambert-zhichu-v1")
    ext_format = request.GET.get("format", "mp3")
    volume = request.GET.get("volume", "50")
    rate = request.GET.get("rate", "1.0")

    dashscope.api_key = os.environ['DASHSCOPE_API_KEY']

    logger.info('controller.text2audio.request-text:{}-model:{}'.format(text, model))

    result = SpeechSynthesizer.call(model=model,
                                    text=text,
                                    format=ext_format,
                                    volume=volume,
                                    rate=rate,
                                    sample_rate=48000)

    logger.info('controller.text2audio.response-result:{}'.format(result))

    basedir = os.environ['textaudio_basedir']

    import uuid
    uids = uuid.uuid4()
    filename = f'{uids}.' + ext_format
    fullname = basedir + filename

    if result.get_audio_data() is not None:
        try:
            with open(fullname, 'wb') as f:
                f.write(result.get_audio_data())
        except Exception as e:
            logger.info('controller.text2audio.process fail e:{}'.format(str(e)))

            return HttpResponse(json.dumps({
                "code": 94,
                'msg': 'text process fail'
            }))
    else:
        return HttpResponse(json.dumps({
            "code": 91,
            'msg': 'generate fail'
        }))

    if os.path.exists(fullname) is False:
        return HttpResponse(json.dumps({
            "code": 92,
            'msg': 'file not found'
        }))

    return HttpResponse(json.dumps({
        'code': 200,
        'msg': "",
        'data': {
            "file": filename
        }
    }))


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
