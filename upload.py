import httplib
import mimetypes 
import os
import random
import json
import time
import threading
import urllib2

userName = "rexgene@hotmail.com"
password = ""
filePath = "test.apk"
outPath = "./out"
threadList = []

def login(username, password):
  return "FAB0EBD6E4887C97A4FA21F15E1F98CC"

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

def downloadTask(session, url, outPath):
  if outPath[-1] != "/":
    outPath = outPath + "/"

  if not os.path.exists(outPath):
    os.makedirs(outPath)

  fileName = url.split("/")[-1]
  print "[*] Downloading %s" % fileName
  rep = urllib2.urlopen(url)

  fp = open(outPath + fileName, "wb")
  fp.write(rep.read())

  print "[*] %s Download complete" % fileName
  fp.close()

def uploadTask(session, username, filePath):
  print "[*] Uploading %s" % filePath
  fields = uploadFile(filePath, userName, session)
  print "[+] %s Upload success" % filePath

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
    print "[+] %s Commit success" % appval
  else:
    print "[-] %s Commit Fail" % appval

def downloadFiles(session, downloadList, outPath):
  for url in downloadList:
    task = threading.Thread(target=downloadTask, args=(session, url, outPath))
    threadList.append(task)
    task.start()

def uploadFiles(session, username, uploadList):
  for filePath in uploadList:
    task = threading.Thread(target=uploadTask, args=(session, username, filePath))
    threadList.append(task)
    task.start()

def checkFileToDownload(session, outPath):
  downloadRecords = {}
  isFinish = False
  while not isFinish:
    downloadList, isFinish = getDownloadList(session, downloadRecords, firstAppId)
    downloadFiles(session, downloadList, outPath)
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

def waitForAllThread():
  while True:
    isAlive = False
    for thread in threadList:
      isAlive = isAlive or thread.is_alive()
    
    if isAlive:
      time.sleep(1)
    else:
      break

try:
  session = login(userName, password)
  firstAppId = getFirstAppId(session)

  files = []
  files.append("test.apk")

  uploadFiles(session, userName, files)
  checkFileToDownload(session, outPath)
  waitForAllThread()
except:
  pass
