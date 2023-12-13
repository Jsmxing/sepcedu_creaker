import argparse
import base64
import json
import os
import random
import time

import requests

import pytesseract
from PIL import Image

random_string = None
acc_token = None
name = None

last_page = 0
subject_id = []  # 科目ID 科目节数 开始ID


def get_captcha():
    url = 'https://manage.sepcedu.com/v1/pc/dz/captcha/get-captcha?random=' + random_string

    response = requests.get(url)

    if response.status_code == 200:
        parsed_data = json.loads(response.text)
        captcha_data = parsed_data["data"]["captcha"]

        # 提取base64编码的部分
        encoded_data = captcha_data.split(",")[1]

        image_data = base64.b64decode(encoded_data)

        # 将图像数据写入本地文件
        with open("captcha.png", "wb") as file:
            file.write(image_data)

        choose = input('是否手动验证码 0或1: ')

        if choose == '1':
            os.startfile("captcha.png")
            captcha_self = input('请输入验证码: ')
            return captcha_self
        else:
            # 打开图像文件
            image = Image.open('captcha.png')
            # 使用Tesseract OCR提取文本
            text = pytesseract.image_to_string(image)
            # 打印识别结果
            return text[:4]

    else:
        return "请求失败，状态码：" + str(response.status_code)


def generate_random_string():
    global random_string

    t = []
    n = "0123456789abcdef"

    for i in range(25):
        t.append(n[random.randint(0, 15)])

    t[14] = "4"
    t[19] = n[3 & int(t[19], 16) | 8]
    t[8] = t[13] = t[18] = t[23] = "_"

    random_string = "".join(t)
    return random_string


def getLoginJson(account, password):
    data = {
        "account": account,
        "password": encrypt(password),
        "captcha": get_captcha(),
        "random": random_string
    }
    # json_data = json.dumps(data)

    # print(data)
    return data


def encrypt(input_str):
    constant_str = "xCjIhFMUbC78O7Me"
    combined_str = constant_str + input_str
    encoded_str = base64.b64encode(combined_str.encode()).decode()[::-1]
    replaced_str = encoded_str.replace("+", "%").replace("/", "(").replace("=", ")")
    return replaced_str


def login(account, password):
    global acc_token
    global name

    url = "https://manage.sepcedu.com/v1/pc/dz/user/login"

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) "
                      "Chrome/119.0.0.0 Safari/537.36 Edg/119.0.0.0",
        "authority": "manage.sepcedu.com",
        "method": "POST",
        "path": "/v1/pc/dz/user/login",
        "scheme": "https",
        "accept": "application/json, text/plain, */*",
        "accept-encoding": "gzip, deflate, br",
        "accept-language": "zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6",
        "origin": "https://elearning.sepcedu.com",
        "referer": "https://elearning.sepcedu.com/",
        "sec-ch-ua": "\"Microsoft Edge\";v=\"119\", \"Chromium\";v=\"119\", \"Not?A_Brand\";v=\"24\"",
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": "\"Windows\"",
        "sec-fetch-dest": "empty",
        "sec-fetch-mode": "cors",
        "sec-fetch-site": "same-site",
        "token": ""
    }

    session = requests.Session()
    data = getLoginJson(account, password)
    # print(data)
    response = session.post(url, headers=headers, json=data)

    # 获取响应内容
    parsed_data = json.loads(response.text)

    acc_token = parsed_data["data"]["token"]

    name = parsed_data["data"]["info"]["name"]
    mobile = parsed_data["data"]["info"]["mobile"]
    student_id = parsed_data["data"]["info"]["student_no"]
    department = parsed_data["data"]["info"]["department"]
    major = parsed_data["data"]["info"]["major"]
    year = parsed_data["data"]["info"]["year"]
    _class = parsed_data["data"]["info"]["class"]

    print('登录成功，您的信息如下\n'
          f'姓名: {name}\n'
          f'手机号: {mobile}\n'
          f'学号: {student_id}\n'
          f'系名称: {department}\n'
          f'专业名称: {major}\n'
          f'入学年份: {year}\n'
          f'班级: {_class}\n')

    # print(f'token: {acc_token}')


def read_section(id, sections_name, subject_name):
    global acc_token

    url = "https://manage.sepcedu.com/v1/pc/dz/course/check-module/" + str(id)
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) "
                      "Chrome/119.0.0.0 Safari/537.36 Edg/119.0.0.0",
        "authority": "manage.sepcedu.com",
        "accept": "application/json, text/plain, */*",
        "accept-encoding": "gzip, deflate, br",
        "accept-language": "zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6",
        "origin": "https://elearning.sepcedu.com",
        "referer": "https://elearning.sepcedu.com/",
        "sec-ch-ua": '"Microsoft Edge";v="119", "Chromium";v="119", "Not?A_Brand";v="24"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"Windows"',
        "token": acc_token
    }

    response = requests.get(url, headers=headers)
    parsed_data = json.loads(response.text)
    # code = parsed_data["code"]
    msg = parsed_data["msg"]
    # data = parsed_data["data"]
    print(f'{subject_name} -> {sections_name} -> {msg}')


def get_subject_1():
    global acc_token
    global last_page
    url = "https://manage.sepcedu.com/v1/pc/dz/student/get-enroll-course-list-by-type?type=1&perpage=3"

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36 Edg/119.0.0.0",
        "authority": "manage.sepcedu.com",
        "accept": "application/json, text/plain, */*",
        "accept-encoding": "gzip, deflate, br",
        "accept-language": "zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6",
        "origin": "https://elearning.sepcedu.com",
        "referer": "https://elearning.sepcedu.com/",
        "sec-ch-ua": '"Microsoft Edge";v="119", "Chromium";v="119", "Not?A_Brand";v="24"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"Windows"',
        "sec-fetch-dest": "empty",
        "sec-fetch-mode": "cors",
        "sec-fetch-site": "same-site",
        "token": acc_token
    }

    response = requests.get(url, headers=headers)
    parsed_data = json.loads(response.text)
    last_page = parsed_data["data"]["last_page"]
    print(f'目录共{last_page}页')


def get_subject_2():
    global acc_token
    global last_page
    global subject_id

    url = "https://manage.sepcedu.com/v1/pc/dz/student/get-enroll-course-list-by-type?type=1"

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) "
                      "Chrome/119.0.0.0 Safari/537.36 Edg/119.0.0.0",
        "authority": "manage.sepcedu.com",
        "accept": "application/json, text/plain, */*",
        "accept-encoding": "gzip, deflate, br",
        "accept-language": "zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6",
        "origin": "https://elearning.sepcedu.com",
        "referer": "https://elearning.sepcedu.com/",
        "sec-ch-ua": '"Microsoft Edge";v="119", "Chromium";v="119", "Not?A_Brand";v="24"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"Windows"',
        "sec-fetch-dest": "empty",
        "sec-fetch-mode": "cors",
        "sec-fetch-site": "same-site",
        "token": acc_token
    }

    response = requests.get(url, headers=headers)
    parsed_data = json.loads(response.text)
    subject_id = []
    for item in parsed_data["data"]["data"]:
        id = item["id"]
        count = item["mod_count"]
        if item["id"] not in subject_id:
            subject_list = [id, count]
            subject_id.append(subject_list)
    # print(subject_id)


def get_subject_3():
    global acc_token
    global subject_id

    schedule_count = 0
    schedule_all = 0
    schedule_single = 0

    subject_len = len(subject_id)

    for i in range(subject_len):
        schedule_count += subject_id[i][1]

    print(f'共{schedule_count}节 开始刷课')

    for i in range(subject_len):
        url = "https://manage.sepcedu.com/v1/pc/dz/course/info/" + str(subject_id[i][0])

        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36 Edg/119.0.0.0",
            "authority": "manage.sepcedu.com",
            "accept": "application/json, text/plain, */*",
            "accept-encoding": "gzip, deflate, br",
            "accept-language": "zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6",
            "origin": "https://elearning.sepcedu.com",
            "referer": "https://elearning.sepcedu.com/",
            "sec-ch-ua": '"Microsoft Edge";v="119", "Chromium";v="119", "Not?A_Brand";v="24"',
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": '"Windows"',
            "sec-fetch-dest": "empty",
            "sec-fetch-mode": "cors",
            "sec-fetch-site": "same-site",
            "token": acc_token
        }

        response = requests.get(url, headers=headers)
        parsed_data = json.loads(response.text)
        subject_name = parsed_data["data"]["name"]

        for sections in parsed_data["data"]["sections"]:
            for modules in sections["modules"]:
                id = modules["id"]
                sections_name = modules["name"]
                read_section(id, sections_name, subject_name)

                schedule_all += 1
                schedule_single += 1

                speed_all = str(int(round(schedule_all/schedule_count, 2) * 100))
                speed_single = str(int(round(schedule_single/subject_id[i][1], 2) * 100))
                os.system(f'title {name} 全刷模式 总进度{speed_all}% 分支{subject_name}进度{speed_single}%')
    print("全刷模式完成！")


def get_subject_4(subject_id_in):
    global acc_token
    global subject_id

    schedule = 0
    schedule_count = 0

    subject_len = len(subject_id)
    for i in range(subject_len):
        if subject_id_in == str(subject_id[i][0]):
            schedule_count = subject_id[i][1]
            break

    print(f'共{schedule_count}节 开始刷课')

    url = "https://manage.sepcedu.com/v1/pc/dz/course/info/" + str(subject_id_in)

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36 Edg/119.0.0.0",
        "authority": "manage.sepcedu.com",
        "accept": "application/json, text/plain, */*",
        "accept-encoding": "gzip, deflate, br",
        "accept-language": "zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6",
        "origin": "https://elearning.sepcedu.com",
        "referer": "https://elearning.sepcedu.com/",
        "sec-ch-ua": '"Microsoft Edge";v="119", "Chromium";v="119", "Not?A_Brand";v="24"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"Windows"',
        "sec-fetch-dest": "empty",
        "sec-fetch-mode": "cors",
        "sec-fetch-site": "same-site",
        "token": acc_token
    }

    response = requests.get(url, headers=headers)
    parsed_data = json.loads(response.text)
    subject_name = parsed_data["data"]["name"]

    for sections in parsed_data["data"]["sections"]:
        for modules in sections["modules"]:
            id = modules["id"]
            sections_name = modules["name"]
            read_section(id, sections_name, subject_name)

            schedule += 1

            speed = str(int(round(schedule / schedule_count, 2) * 100))
            os.system(f'title {name} 单刷模式 总进度{speed}%')
    print("单刷模式完成！")


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--account', type=str, default=None)
    parser.add_argument('--password', type=str, default=None)
    parser.add_argument('--subject', type=str, default=None)  # 单刷模式下 设置科目ID
    args = parser.parse_args()

    random_string = generate_random_string()

    account = args.account
    password = args.password

    if account is None:
        account = input("请输入账号: ")

    if password is None:
        password = input("请输入密码: ")

    acc_token = "123456"
    login(account, password)

    get_subject_2()

    if args.subject is None:
        print("全刷模式")
        get_subject_3()
    else:
        print("单刷模式")
        get_subject_4(args.subject)
