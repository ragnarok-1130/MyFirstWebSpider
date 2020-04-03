import requests as req
from bs4 import BeautifulSoup
from datetime import datetime, timedelta, timezone
import re

gitUserName = input("请输入gitlab用户名：")
offset = 0

today = datetime.now().replace(tzinfo=timezone(timedelta(hours=8)))
today = today.replace(today.year, today.month, today.day, 0, 0, 0, 0)

print("今日工作:")

srcHtmlText = ''
utcTime = None

while utcTime is None or utcTime > today:
    url = "http://172.20.20.81/" + gitUserName + ".atom?limit=20&offset=" + str(offset)
    srcHtml = req.get(url)
    srcHtmlText += srcHtml.text
    soup = BeautifulSoup(srcHtmlText, 'lxml')
    times = soup.select('updated')
    utcTime = datetime.strptime(times[len(times) - 1].string, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
    offset += 20

soup = BeautifulSoup(srcHtmlText, 'lxml')
data = soup.find_all('p', dir="auto")
regex = re.compile("Merge.*")
logSet = set()
workLog = ''
count = 1
for comment in data:
    if regex.match(comment.string):
        continue
    if comment.string in logSet:
        continue
    workLog += str(count) + "." + comment.string + "\n"
    count = count + 1
    logSet.add(comment.string)

print(workLog)
