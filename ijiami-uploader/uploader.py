import httplib
import mimetypes 
import os
import random
import json
import time
import threading
import urllib2
import urllib
import re

global userName
global password
global outputPath
global inputPath

uploadThreadList = []
downloadThreadList = []
signThreadList = []
uploadLock = threading.Lock()
downloadLock = threading.Lock()
signLock = threading.Lock()

def loadConfig():
  global userName
  global password
  global outputPath
  global inputPath

  data = {}
  fp = open("param.conf", "r")
  for line in fp.readlines():
    line = line.strip()
    if line == "":
      continue

    fields = line.split("=")
    if len(fields) != 2:
      raise Exception("load config error:%s" % line)

    data[fields[0]] = fields[1]

  userName = data["userName"]
  password = data["password"]
  outputPath = data["outputPath"]
  inputPath = data["inputPath"]
  fp.close()

def login(username, password):
  headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/51.0.2704.79 Safari/537.36 Edge/14.14393",
    "Pragma": "no-cache",
    "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8"
  }

  params = {
    "email": userName,
    "pwd": password,
    "loginFlag": 1,
  };

  conn = httplib.HTTPConnection("ijiami.cn", 80)
  conn.request("POST", "/toLogin", urllib.urlencode(params), headers)

  rep = conn.getresponse()
  if rep.status == 200:
    ret = json.loads(rep.read())
    isSuccess = ret["result"]
    if isSuccess:
      print "[*] Login success"
    else:
      raise Exception("Login fail, may be password error")
  else:
    raise Exception("request error")

  cookie = rep.getheader("set-cookie")
  rexge = re.compile("JSESSIONID=(\w+);?")
  result = rexge.findall(cookie)
  if len(result) == 0:
    raise Exception("cookie invalid")

  return result[0]

def getContentType(filename): 
  return mimetypes.guess_type(filename)[0] or 'application/octet-stream'
 
def readDataFromFile(fileName):
  fp = open(fileName, "rb")
  data = fp.read()
  fp.close()

  return data


def appendFormData(data, boundary, key, value, isFileType) : 
    if isFileType:
      data.append("--%s\r\n" % boundary) 
      data.append("Content-Disposition: form-data; name=\"%s\"; filename=\"%s\"\r\n" % (key, os.path.basename(value)))
      data.append("Content-Type: %s\r\n" % getContentType(value)) 
      data.append("\r\n")
      data.append(readDataFromFile(value))
    else:
      data.append("--%s\r\n" % boundary) 
      data.append("Content-Disposition: form-data; name=\"%s\"\r\n" % key)
      data.append("\r\n")
      data.append(value)

    data.append("\r\n")

def appendFormFinish(data, boundary):
    data.append("--%s--" % boundary) 

def uploadFile(filePath, userName, session):
  boundary = "----------%s" % "".join(random.sample("0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ", 30))
  headers = {
    "Cookie" : "JSESSIONID=%s;Ijiami_apply_first=0;ckchck=1" % session,
    "Content-Type": "multipart/form-data; boundary=%s" % boundary,
    "Accept": "text/*",
    "User-Agent": "Shockwave Flash",
  }
  data = []
  appendFormData(data, boundary, "Filename", os.path.basename(filePath), False)
  appendFormData(data, boundary, "ucc", userName, False)
  appendFormData(data, boundary, "upload", filePath, True)
  appendFormData(data, boundary, "Upload", "Submit Query", False)
  appendFormFinish(data, boundary)

  conn = httplib.HTTPConnection("ijiami.cn", 80)
  conn.request("POST", "/upload/", "".join(data), headers)
  rep = conn.getresponse()
  info = rep.read()

  return info.split("$#$")

def getAppList(sessionId, size):
  param = "pageNum=1&psize=%d&selStr=" % size
  headers = {
    "Cookie" : "JSESSIONID=%s" % sessionId,
    "Content-Type": "application/x-www-form-urlencoded; charset=utf-8",
    "User-Agent": "Shockwave Flash",
    "Pragma": "no-cache",
  }

  conn = httplib.HTTPConnection("ijiami.cn", 80)
  conn.request("POST", "/apply/encryptLogsByList", param, headers)
  rep = conn.getresponse()
  return rep.read()

def uploadToIjiami(sessionId, appval, cxcc, bbh, bm, apkUrl, iconUrl, md5, package, size, files):
  headers = {
    "Cookie" : "JSESSIONID=%s" % sessionId,
    "Content-Type": "application/x-www-form-urlencoded; charset=utf-8",
    "User-Agent": "Shockwave Flash",
  }

  formatStr = "check=&values=&appval=%s&app_type=12&en_app_type=0&cxmc=%s&bbh=%s&bm=%s&apkUrl=%s&iconUrl=%s&md5=%s&package=%s&msg_content=&size=%s&files=%s&_=%lu" % \
               (appval, cxcc, bbh, bm, apkUrl, iconUrl, md5, package, size, files, time.time())

  conn = httplib.HTTPConnection("ijiami.cn", 80)
  conn.request("GET", "/uploadApp?%s" % formatStr, headers=headers)
  rep = conn.getresponse()
  return rep.read()

def getDownloadList(session, records, firstAppId):
  downloadList = []
  ret = json.loads(getAppList(session, 100))
  result = ret["result"]
  if result == None:
    return None
  else:
    total = result["ptoal"]
    appList = result["plist"]
    isFinish = True
    for node in appList:
      appId = node["iUserAppID"]
      downloadURL = node["nvcDownloadURL"]

      if firstAppId != None:
        if appId == firstAppId:
          return downloadList, isFinish
        
      if not appId in records:
        if downloadURL != None:
          downloadList.append(downloadURL)
          records[appId] = True
        else:
          isFinish = False
    
    return downloadList, isFinish

def downloadTask(session, url, outputPath):
  if outputPath[-1] != "/":
    outputPath = outputPath + "/"

  if not os.path.exists(outputPath):
    os.makedirs(outputPath)

  fileName = url.split("/")[-1]
  print "[*] Downloading %s" % fileName
  rep = urllib2.urlopen(url)

  filePath = outputPath + fileName
  fp = open(filePath, "wb")
  fp.write(rep.read())

  print "[+] %s Download complete" % filePath
  fp.close()

def uploadTask(session, username, filePath):
  print "[*] Uploading %s" % filePath
  fields = uploadFile(filePath, userName, session)
  if len(fields) < 12:
    print "[-] %s file is invalid. please check it" % filePath
    return
  else:
    print "[*] %s Upload success" % filePath

  appval = os.path.basename(filePath)
  cxmc = fields[0]
  bm = appval[:appval.find(".apk")]
  bbh = fields[4]
  size = fields[1]
  apkUrl = fields[2]
  iconUrl = fields[3]
  md5Sum = fields[5]
  package = fields[6]
  files = fields[11]
  appkey = fields[7]

  ret = uploadToIjiami(session, appval, cxmc, bbh, bm, apkUrl, iconUrl, md5Sum, package, size, files)
  ret = json.loads(ret)
  if ret["re"] == 1:
    print "[*] %s Commit success" % appval
  else:
    raise Exception("%s Commit Fail" % appval)

def downloadFiles(session, downloadList, outputPath):
  for url in downloadList:
    task = threading.Thread(target=downloadTask, args=(session, url, outputPath))
    downloadThreadList.append(task)
    task.start()

def uploadFiles(session, username, uploadList):
  for filePath in uploadList:
    task = threading.Thread(target=uploadTask, args=(session, username, filePath))
    uploadLock.acquire()
    uploadThreadList.append(task)
    uploadLock.release()
    task.start()

def checkFileToDownload(session, outputPath):
  downloadRecords = {}
  isFinish = False
  while not isFinish:
    downloadList, isFinish = getDownloadList(session, downloadRecords, firstAppId)
    downloadFiles(session, downloadList, outputPath)
    if not isFinish:
      time.sleep(1)

def getFirstAppId(session):
  ret = json.loads(getAppList(session, 1))
  result = ret["result"]
  if result == None:
    return None
  else:
    total = result["ptoal"]
    appList = result["plist"]
    return appList[0]["iUserAppID"]

def waitForUploadThread():
  while True:
    isAlive = False
    uploadLock.acquire()
    for thread in uploadThreadList:
      isAlive = thread.is_alive()
      if isAlive:
        break

    uploadLock.release()
    if isAlive:
      time.sleep(1)
    else:
      break

def waitForDownloadThread():
  while True:
    isAlive = False
    downloadLock.acquire()
    for thread in downloadThreadList:
      isAlive = thread.is_alive()
      if isAlive:
        break

    downloadLock.release()
    if isAlive:
      time.sleep(1)
    else:
      break

def getFiles(inputPath):
  fileList = []

  for parent, _, filenames in os.walk(inputPath):
    for filename in filenames:
      if filename[-4:] == ".apk":
        fileList.append(os.path.join(parent,filename))

  return fileList

def sign(filename):
    os.system("./sign.sh %s" % filename)

def signFiles():
    global outputPath

    files = getFiles(outputPath) 
    for filename in files:
        if filename[-4:] == ".apk":
            task = threading.Thread(target=sign, args=(filename,))
            signLock.acquire()
            signThreadList.append(task)
            signLock.release()
            task.start()

def waitForSignThread():
  while True:
    isAlive = False
    signLock.acquire()
    for thread in signThreadList:
      isAlive = thread.is_alive()
      if isAlive:
        break

    signLock.release()
    if isAlive:
      time.sleep(1)
    else:
      break

try:
  loadConfig()
  os.system("rm -f %s/*" % outputPath)
  session = login(userName, password)
  firstAppId = getFirstAppId(session)
  files = getFiles(inputPath)

  uploadFiles(session, userName, files)
  waitForUploadThread()
  print "[*] Waitting for Encryption..."
  checkFileToDownload(session, outputPath)
  waitForDownloadThread()
  print "[*] Waitting for Sign..."
  signFiles()
  waitForSignThread()
except Exception, msg:
  print "[-]", msg
