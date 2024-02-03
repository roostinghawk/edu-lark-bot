import argparse
import os

import pendulum
import requests
from BingImageCreator import ImageGen
from github import Github
import json
from lark_oapi.api.im.v1 import *
import lark_oapi as lark

# 1 real get up
GET_UP_ISSUE_NUMBER = 1
GET_UP_MESSAGE_TEMPLATE = (
    "\r\n今天的一句诗:\r\n {sentence} \r\n"
)
SENTENCE_API = "https://v1.jinrishici.com/all"
DEFAULT_SENTENCE = "赏花归去马如飞\r\n去马如飞酒力微\r\n酒力微醒时已暮\r\n醒时已暮赏花归\r\n"
TIMEZONE = "Asia/Shanghai"

def login(token):
    return Github(token)


def get_one_sentence(up_list):
    try:
        r = requests.get(SENTENCE_API)
        if r.ok:
            concent = r.json().get("content")
            if concent in up_list:
                return get_one_sentence(up_list)
            return concent
        return DEFAULT_SENTENCE
    except:
        print("get SENTENCE_API wrong")
        return DEFAULT_SENTENCE


def get_today_get_up_status(issue):
    comments = list(issue.get_comments())
    if not comments:
        return False, []
    up_list = []
    for comment in comments:
        try:
            s = comment.body.splitlines()[6]
            up_list.append(s)
        except Exception as e:
            print(str(e), "!!")
            continue
    latest_comment = comments[-1]
    now = pendulum.now(TIMEZONE)
    latest_day = pendulum.instance(latest_comment.created_at).in_timezone(
        "Asia/Shanghai"
    )
    is_today = (latest_day.day == now.day) and (latest_day.month == now.month)
    return is_today, up_list


def make_pic_and_save(sentence, bing_cookie):
    # for bing image when dall-e3 open drop this function
    print("ImageGen init...")
    i = ImageGen(bing_cookie)
    # prompt = f"revise `{sentence}` to a DALL-E prompt"
    # completion = client.chat.completions.create(
    #     messages=[{"role": "user", "content": prompt}],
    #     model="gpt-4-1106-preview",
    # )
    # sentence = completion.choices[0].message.content.encode("utf8").decode()
    # print(f"revies: {sentence}")

    print("Start images creation from ImageGen")
    images = i.get_images(sentence)
    date_str = pendulum.now().to_date_string()
    new_path = os.path.join("OUT_DIR", date_str)
    if not os.path.exists(new_path):
        os.mkdir(new_path)
    i.save_images(images, new_path)
    return new_path + "0.jpeg"


def make_get_up_message(bing_cookie, up_list):
    sentence = get_one_sentence(up_list)
    pic_path = ""
    try:
        pic_path = make_pic_and_save(sentence, bing_cookie)
        print("pic path: " + pic_path)
    except Exception as e:
        print(str(e))
        # give it a second chance
        try:
            sentence = get_one_sentence(up_list)
            print(f"Second: {sentence}")
            pic_path = make_pic_and_save(sentence, bing_cookie)
        except Exception as e:
            print(str(e))
    body = GET_UP_MESSAGE_TEMPLATE.format(sentence=sentence)
    print(body, pic_path)
    return body, pic_path


def send_to_lark(message, pic_path, lark_app_key, lark_app_secret, lark_webhook_url):

    # 上传图片
    image_key = upload_image_to_lark(pic_path, lark_app_key, lark_app_secret)
    print("image_key: " + image_key)

    # 构造富文本消息数据
    data = {
        "msg_type": "post",
        "content": {
            "post": {
                "zh_cn": {  
                    "title": "",
                    "content": [
                        [
                            {
                                "tag": "img",
                                "image_key": image_key
                            },
                            {
                                "tag": "text",
                                "text": message
                            }
                        ]
                    ]
                }
            }
        }
    }


    # 发送POST请求
    response = requests.post(lark_webhook_url, headers={'Content-Type': 'application/json'}, data=json.dumps(data))

    # 打印响应结果
    print(response.text)
    return

def upload_image_to_lark(pic_path, lark_app_key, lark_app_secret):

     # 创建client
    client = lark.Client.builder() \
        .app_id(lark_app_key) \
        .app_secret(lark_app_secret) \
        .log_level(lark.LogLevel.DEBUG) \
        .build()

    # 构造请求对象
    file = open(pic_path, "rb")
    request: CreateImageRequest = CreateImageRequest.builder() \
        .request_body(CreateImageRequestBody.builder()
            .image_type("message")
            .image(file)
            .build()) \
        .build()


    response: CreateImageResponse = client.im.v1.image.create(request)

    # print("飞书图片上传是否成功：" + response.success())

    # 处理失败返回
    if not response.success():
        lark.logger.error(
            f"client.im.v1.image.create failed, code: {response.code}, msg: {response.msg}, log_id: {response.get_log_id()}")
        return

    # 处理业务结果
    lark.logger.info(lark.JSON.marshal(response.data, indent=4))

    return response.data.image_key

def image2byte():
    '''
    图片转byte
    image: 必须是PIL格式
    image_bytes: 二进制
    '''

    # 创建一个字节流管道
    img_bytes = io.BytesIO()
    #把PNG格式转换成的四通道转成RGB的三通道，然后再保存成jpg格式
    image = image.convert("RGB")
    # 将图片数据存入字节流管道， format可以按照具体文件的格式填写
    image.save(img_bytes, format="JPEG")
    # 从字节流管道中获取二进制
    image_bytes = img_bytes.getvalue()
    return image_bytes


def main(
    github_token,
    repo_name,
    bing_cookie,
    weather_message,
    lark_app_key,
    lark_app_secret,
    lark_webhook_url
):
    u = login(github_token)
    repo = u.get_repo(repo_name)
    issue = repo.get_issue(GET_UP_ISSUE_NUMBER)
    up_list = get_today_get_up_status(issue)
    early_message, pic_path = make_get_up_message(
        bing_cookie, up_list
    )
    message = early_message
    if weather_message:
        weather_message = f"现在的天气是{weather_message}\n"
        message = weather_message + early_message
    # send to lark
    if lark_app_key and lark_app_secret:
        send_to_lark(message, pic_path, lark_app_key, lark_app_secret, lark_webhook_url)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("github_token", help="github_token")
    parser.add_argument("repo_name", help="repo_name")
    parser.add_argument(
        "--weather_message", help="weather_message", nargs="?", default="", const=""
    )
    parser.add_argument("bing_cookie", help="bing cookie")
    parser.add_argument(
        "--lark_app_key", help="lark_app_key", nargs="?", default="", const=""
    )
    parser.add_argument(
        "--lark_app_secret", help="lark_lark_app_secretapp_key", nargs="?", default="", const=""
    )
    parser.add_argument(
        "--lark_webhook_url", help="lark_webhook_url", nargs="?", default="", const=""
    )
    options = parser.parse_args()
    main(
        options.github_token,
        options.repo_name,
        options.bing_cookie,
        options.weather_message,
        options.lark_app_key,
        options.lark_app_secret,
        options.lark_webhook_url
    )