import re
from datetime import datetime, timedelta, timezone

import requests as req
from bs4 import BeautifulSoup

gitUserName = input("请输入gitlab用户名：")
offset = 0

today = datetime.now().replace(tzinfo=timezone(timedelta(hours=8)))
today = today.replace(today.year, today.month, today.day, 0, 0, 0, 0)

print("今日工作:")

workLog = ''
srcHtmlText = ''
utcTime = None
times = None
timeTag = None

while utcTime is None or utcTime > today:
    url = "http://172.20.20.81/" + gitUserName + ".atom?limit=20&offset=" + str(offset)
    srcHtml = req.get(url)
    srcHtmlText += srcHtml.text
    soup = BeautifulSoup(srcHtmlText, 'lxml')
    times = soup.select('updated')
    utcTime = datetime.strptime(times[len(times) - 1].string, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
    offset += 20

#仅截取当日git提交记录
for index in range(len(times) - 1, -1, -1):
    utcTime = datetime.strptime(times[index].string, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
    if utcTime > today:
        timeTag = times[index].string
        break

if timeTag is None:
    srcHtmlText = ''
else:
    srcHtmlText = srcHtmlText[0:srcHtmlText.index(timeTag)]
    soup = BeautifulSoup(srcHtmlText, 'lxml')
    data = soup.find_all('p', dir="auto")
    regex = re.compile("Merge.*")
    logSet = set()
    count = 1
    for comment in data:
        # 过滤Merge记录
        if regex.match(comment.string):
            continue
        #过滤重复commit记录
        if comment.string in logSet:
            continue
        workLog += str(count) + "." + comment.string + "\n"
        count = count + 1
        logSet.add(comment.string)

print(workLog)
