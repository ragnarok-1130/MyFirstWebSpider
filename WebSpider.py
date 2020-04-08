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

    while utc_time is None or utc_time >= today:
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
            # 由于时间展示在comment之前 为保持日志完整性  向后移动1位
            time_tag = times[index + 1].string
            break

    if time_tag is None:
        work_log = '快乐摸鱼'
    else:
        # 截取今日提交记录
        src_html_text = src_html_text[0:src_html_text.index(time_tag)]
        soup = BeautifulSoup(src_html_text, 'lxml')
        # 获取所有提交记录comment
        data = soup.find_all('p', dir="auto")
        regex = re.compile("Merge.*")
        # log_set  用于防重复
        log_set = set()
        count = 1
        for comment in data:
            # 过滤Merge记录
            if regex.match(comment.text):
                continue
            # 过滤重复commit记录
            if comment.text in log_set:
                continue
            work_log += str(count) + "." + comment.text + "\n"
            count = count + 1
            log_set.add(comment.text)

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
    header = {
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
        'Accept-Encoding': 'gzip, deflate',
        'Accept-Language': 'zh-CN,zh;q=0.9',
        'Cache-Control': 'no-cache',
        'Connection': 'keep-alive',
        'Content-Length': '215',
        'Content-Type': 'application/x-www-form-urlencoded',
        'Host': '172.20.20.81',
        'Origin': 'http://172.20.20.81',
        'Pragma': 'no-cache',
        'Referer': 'http://172.20.20.81/users/sign_in',
        'Upgrade-Insecure-Requests': '1',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.163 Safari/537.36'
    }
    data = {
        "utf8": "✓",
        "authenticity_token": token,
        "user[login]": username,
        "user[password]": password,
        "user[remember_me]": 0
    }
    # 禁止重定向   否则会导致被重定向导致cookie登录失效
    response = req.post(url, data=data, allow_redirects=False, headers=header, cookies=first_cookie)
    if response.status_code != 302:
        print("警告：登录失败，可能无法获取到最新日志")
    cookie = response.cookies.get_dict()
    return cookie


if __name__ == '__main__':
    gitUserName = input("请输入gitlab用户名：")
    # getpass可用于隐藏密码输入  但pycharm并不兼容
    gitPassword = getpass.getpass("请输入gitlab密码：")
    cookie_logged = get_cookie(gitUserName, gitPassword)
    today_work_log = get_work_log(gitUserName, cookie_logged)
    print("今日工作:")
    print(today_work_log)
