import getpass
import re
from datetime import datetime, timedelta, timezone

import requests as req
from bs4 import BeautifulSoup


def get_work_log(username, cookie):
    today = datetime.now().replace(tzinfo=timezone(timedelta(hours=8)))
    today = today.replace(today.year, today.month, today.day, 0, 0, 0, 0)
    offset = 0
    work_log = ''
    src_html_text = ''
    utc_time = None
    times = None
    time_tag = None

    while utc_time is None or utc_time > today:
        url = "http://172.20.20.81/" + username + ".atom?limit=20&offset=" + str(offset)
        src_html = req.get(url=url, cookies=cookie)
        src_html_text += src_html.text
        soup = BeautifulSoup(src_html_text, 'lxml')
        times = soup.select('updated')
        utc_time = datetime.strptime(times[len(times) - 1].string, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
        offset += 20

    # 仅截取当日git提交记录
    for index in range(len(times) - 1, -1, -1):
        utc_time = datetime.strptime(times[index].string, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
        if utc_time > today:
            time_tag = times[index].string
            break

    if time_tag is None:
        src_html_text = ''
    else:
        src_html_text = src_html_text[0:src_html_text.index(time_tag)]
        soup = BeautifulSoup(src_html_text, 'lxml')
        data = soup.find_all('p', dir="auto")
        regex = re.compile("Merge.*")
        log_set = set()
        count = 1
        for comment in data:
            # 过滤Merge记录
            if regex.match(comment.string):
                continue
            # 过滤重复commit记录
            if comment.string in log_set:
                continue
            work_log += str(count) + "." + comment.string + "\n"
            count = count + 1
            log_set.add(comment.string)

    return work_log


def get_gitlab_html(url):
    """
    这里用于获取登录页的html，以及cookie
    :param url: 登录页url
    :return: 登录页面的HTML,以及第一次的cookie
    """
    response = req.get(url)
    first_cookie = response.cookies.get_dict()
    return response.text, first_cookie


def get_token(html):
    """
    处理登录后页面的html
    :param html:
    :return: 获取csrftoken
    """
    soup = BeautifulSoup(html, 'lxml')
    res = soup.find("input", attrs={"name": "authenticity_token"})
    token = res["value"]
    return token


def get_cookie(username, password):
    url = "http://172.20.20.81/users/sign_in"
    login_html, first_cookie = get_gitlab_html(url)
    token = get_token(login_html)
    data = {
        "utf8": "✓",
        "authenticity_token": token,
        "user[login]": username,
        "user[password]": password,
        "user[remember_me]": 0
    }
    response = req.post(url, data=data, cookies=first_cookie)
    if response.status_code != 200:
        raise Exception("response code:" + response.status_code)
    cookie = response.cookies.get_dict()
    return cookie


if __name__ == '__main__':
    gitUserName = input("请输入gitlab用户名：")
    gitPassword = getpass.getpass("请输入gitlab密码：")
    cookie_logged = get_cookie(gitUserName, gitPassword)
    today_work_log = get_work_log(gitUserName, cookie_logged)
    print("今日工作:")
    print(today_work_log)
