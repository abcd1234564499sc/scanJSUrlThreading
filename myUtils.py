#!/usr/bin/env python
# coding=utf-8
import datetime
import json
import os
import random
import re
import socket
import urllib.parse

import openpyxl as oxl
import requests
from bs4 import BeautifulSoup
from openpyxl.styles import Border, Side, Font, PatternFill

# 全局变量区域
borderNumDic = {-1: None, 0: "thin"}


# 访问URL,type表示请求类型，0为GET，1为POST，2为PUT
# 返回值类型如下：
# {
# "url":传入URL,
# "resultStr":访问结果字符串,
# "checkFlag":标志是否访问成功的布尔类型变量,
# "title":访问成功时的页面标题,
# "pageContent":访问成功时的页面源码，
# "status":访问的响应码
# }
def requestsUrl(url, cookie={}, header={}, data={}, type=0, reqTimeout=10, readTimeout=10, proxies=None):
    resDic = {}
    url = url.strip()

    resultStr = ""
    checkedFlag = False
    status = ""
    title = ""
    pageContent = ""
    reContent = ""
    timeout = (reqTimeout, readTimeout)
    header = header if header != {} else {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/75.0.3770.100 Safari/537.36"
    }

    try:
        if type == 0:
            response = requests.get(url, headers=header, verify=False, cookies=cookie, timeout=timeout, proxies=proxies)
        elif type == 1:
            response = requests.post(url, headers=header, verify=False, cookies=cookie, data=data, timeout=timeout,
                                     proxies=proxies)
        elif type == 2:
            response = requests.put(url, headers=header, verify=False, cookies=cookie, data=data, timeout=timeout,
                                    proxies=proxies)
        else:
            pass
        status = response.status_code
        if str(status)[0] == "2" or str(status)[0] == "3":
            # 获得页面编码
            pageEncoding = response.apparent_encoding
            # 设置页面编码
            response.encoding = pageEncoding
            # 获得页面内容
            reContent = response.text
            soup = BeautifulSoup(reContent, "lxml")
            title = "成功访问，但无法获得标题" if not soup.title else soup.title.string
            resultStr = "验证成功，标题为：{0}".format(title)
            checkedFlag = True
        else:
            resultStr = "验证失败，状态码为{0}".format(status)
            checkedFlag = False
    except Exception as e:
        resultStr = str(e)
        checkedFlag = False

    # 构建返回结果
    resDic["url"] = url
    resDic["resultStr"] = resultStr
    resDic["checkFlag"] = checkedFlag
    resDic["title"] = title
    resDic["status"] = status
    resDic["pageContent"] = reContent
    return resDic


# 判断该字符串是否是IP，返回一个布尔值
def ifIp(matchStr):
    reFlag = True
    ipReg = r"^(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$"
    if re.match(ipReg, matchStr):
        reFlag = True
    else:
        reFlag = False
    return reFlag


# 从URL中提取协议+域名部分
def getUrlDomain(url):
    try:
        urlObj = urllib.parse.urlsplit(url)
        domain = urllib.parse.urlunsplit(tuple(list(urlObj[:2]) + [""] * 3))
    except:
        domain = "0.0.0." + str(random.randint(0, 254))
    return domain


# 从URL中提取协议+域名+path部分
def getUrlWithoutFile(url):
    urlObj = urllib.parse.urlsplit(url)
    domain = urllib.parse.urlunsplit(tuple(list(urlObj[:3]) + [""] * 2))
    domainList = domain.split("/")
    if "." in domainList[-1]:
        domainList = domainList[:-1]
    else:
        pass
    domain = "/".join(domainList)
    return domain


# 判断两个域名是否属于同一主域名，如果两者都是IP则比较是否完全相同，
# 返回一个布尔值,属于返回True,否则返回False
def ifSameMainDomain(domain1, domain2):
    reFlag = True
    domainArr = [domain1, domain2]
    if ifIp(domain1) != ifIp(domain2):
        # 判断是否是IP和域名比较
        reFlag = False
    elif ifIp(domain1) and ifIp(domain2):
        # 两个参数都是IP
        reFlag = (domain1 == domain2)
    else:
        # 两个参数都是域名
        # 去除端口号
        for index, nowDomain in enumerate(domainArr):
            tempPort = nowDomain.split(":")[-1]
            if tempPort.isdigit():
                # 去除端口号
                nowDomain = ":".join(nowDomain.split(":")[:-1])
                domainArr[index] = nowDomain
            else:
                pass

        # 判断主域名是否相同
        tempMainDomain = ".".join(domainArr[0].split(".")[-2:])
        for nowDomain in domainArr:
            if ".".join(nowDomain.split(".")[-2:]) != tempMainDomain:
                reFlag = False
    return reFlag


# 从URL中提取文件后缀名
def getUrlFileSuffix(url):
    reSuffix = ""
    urlObj = urllib.parse.urlparse(url)
    suffixContent = urlObj[2].split("/")[-1]
    if "." in suffixContent:
        reSuffix = suffixContent.split(".")[-1]
    else:
        reSuffix = ""
    return reSuffix


# 获得精确到秒的当前时间
def getNowSeconed():
    formatStr = "%Y-%m-%d %H:%M:%S"
    nowDate = datetime.datetime.now()
    nowDateStr = nowDate.strftime(formatStr)
    return nowDateStr


# 删除指定路径的文件,传入一个绝对路径,返回一个布尔变量以及一个字符串变量，
# 布尔变量为True表示是否删除成功,若为False则字符串变量中写入错误信息
def deleteFile(filePath):
    deleteFlag = True
    reStr = ""
    if os.path.exists(filePath):
        try:
            os.remove(filePath)
        except Exception as ex:
            reStr = "删除失败，失败信息为：{0}".format(ex)
            deleteFlag = False
    else:
        reStr = "未找到指定路径的文件"
        deleteFlag = False
    return deleteFlag, reStr


# 获得excell的常用样式
def getExcellStyleDic():
    styleDic = {}

    # 单线边框
    thinBorder = Border(left=Side(border_style='thin', color='000000'),
                        right=Side(border_style='thin', color='000000'),
                        top=Side(border_style='thin', color='000000'),
                        bottom=Side(border_style='thin', color='000000'))

    # 文字居中
    alignStyle = oxl.styles.Alignment(horizontal='center', vertical='center')
    leftStyle = oxl.styles.Alignment(horizontal='left', vertical='center')
    rightStyle = oxl.styles.Alignment(horizontal='right', vertical='center')

    # 加粗字体
    boldFont = Font(bold=True)
    hyperLinkFont = Font(color='0000FF')
    underLineFont = Font(underline='single')

    styleDic["thin"] = thinBorder
    styleDic["align"] = alignStyle
    styleDic["bold"] = boldFont
    styleDic["left"] = leftStyle
    styleDic["right"] = rightStyle
    styleDic["link"] = hyperLinkFont
    styleDic["underLine"] = underLineFont
    return styleDic


# 写入一个标准的excell表头（居中，单线框，加粗）
def writeExcellHead(ws, headArr):
    # 获得常用样式
    styleDic = getExcellStyleDic()
    # 写入表头
    for index, head in enumerate(headArr):
        ws.cell(row=1, column=index + 1).value = head
        ws.cell(row=1, column=index + 1).border = styleDic["thin"]
        ws.cell(row=1, column=index + 1).alignment = styleDic["align"]
        ws.cell(row=1, column=index + 1).font = styleDic["bold"]
    return ws


# 写入一个内容单元格
# borderNum表示该单元格的边框对象，其值可查询全局变量styleDic
# ifAlign是一个boolean对象，True表示居中
# hyperLink表示该单元格指向的链接，默认为None，表示不指向任何链接
# fgColor表示该单元格的背景颜色，为一个RGB16进制字符串，默认为“FFFFFF”（白色）
# otherAlign表示当ifAlign为False时指定的其他对齐方式，是一个数字型变量，默认为None，当其为0时表示左对齐，1为右对齐
def writeExcellCell(ws, row, column, value, borderNum, ifAlign, hyperLink=None, fgColor="FFFFFF", otherAlign=None):
    value = str(value)
    ILLEGAL_CHARACTERS_RE = re.compile(r'[\000-\010]|[\013-\014]|[\016-\037]')
    value = ILLEGAL_CHARACTERS_RE.sub("", value)
    # 获得常用样式
    styleDic = getExcellStyleDic()
    # 获得指定单元格
    aimCell = ws.cell(row=row, column=column)
    # 设置值
    aimCell.value = value
    # 设置边框
    styleObjKey = borderNumDic[borderNum]
    if not styleObjKey:
        pass;
    else:
        styleObj = styleDic[styleObjKey]
        aimCell.border = styleObj
    # 设置居中
    if ifAlign:
        aimCell.alignment = styleDic["align"]
    elif otherAlign is not None:
        otherAlign = int(otherAlign)
        if otherAlign == 0:
            aimCell.alignment = styleDic["left"]
        else:
            aimCell.alignment = styleDic["right"]
    else:
        pass

    # 设置超链接
    if hyperLink:
        # 写入超链接
        aimCell.hyperlink = hyperLink
        # 设置当前单元格字体颜色为深蓝色，并添加下划线
        aimCell.font = styleDic["link"]
    else:
        pass

    # 设置填充颜色
    fill = PatternFill("solid", fgColor=fgColor)
    aimCell.fill = fill

    return ws


# 写入一个空格单元格，防止上一列文本超出
def writeExcellSpaceCell(ws, row, column):
    # 设置值
    ws.cell(row=row, column=column).value = " "

    return ws


# 设置excell的列宽
def setExcellColWidth(ws, colWidthArr):
    for colWidindex in range(len(colWidthArr)):
        ws.column_dimensions[chr(ord("A") + colWidindex)].width = colWidthArr[colWidindex]

    return ws


# 保存excell文件
def saveExcell(wb, saveName):
    savePath = ""
    # 处理传入的文件名
    saveName = saveName.split(".")[0] + ".xlsx"
    savePath = "{0}\\{1}".format(os.getcwd(), saveName)

    # 检测当前目录下是否有该文件，如果有则清除以前保存文件
    if os.path.exists(savePath):
        deleteFile(savePath)
    wb.save(savePath)
    return True


# 根据传入的contentDic写入配置文件，若配置文件不存在会创建
# contentDic格式为：{"配置名":"配置值"}，
# 对list和dict格式的值会使用json.dumps进行转换
def writeToConfFile(filePath, contentDic):
    with open(filePath, "w+", encoding="utf-8") as fr:
        for key, value in contentDic.items():
            if isinstance(value, list) or isinstance(value, dict):
                value = json.dumps(value)
            content = "{0}={1}".format(key, value)
            fr.write(content + "\n")


# 读取配置文件，生成一个配置字典，
# 字典结构为：{"配置名":"配置值"}，
# 文件结构为：配置名=配置值，对list和dict格式的值会使用json.loads进行转换
# 配置字典的最后一项固定为"confHeader":配置名列表
def readConfFile(filePath):
    confDic = {}
    headerList = []
    with open(filePath, "r", encoding="utf-8") as fr:
        fileLines = fr.readlines()
    fileLines = [a.replace("\r\n", "\n").replace("\n", "") for a in fileLines if a != ""]
    for fileLine in fileLines:
        fileLine = fileLine.replace("\r\n", "\n").replace("\n", "")
        tempList = fileLine.split("=")
        key = tempList[0].strip()
        value = "=".join(tempList[1:]).strip()
        try:
            value = json.loads(value)
        except:
            pass
        confDic[key] = value
        headerList.append(key)
    confDic["confHeader"] = headerList

    return confDic


def joinUrl(mainUrl, link):
    completeUrl = ""
    if mainUrl[-1] == "/":
        mainUrl = mainUrl[:-1]
    else:
        if link[0] != "/":
            link = "/" + link
    completeUrl = mainUrl + link
    return completeUrl


# 测试指定IP的指定端口是否能联通
def connectIpPort(ip, port):
    ifConnected = False
    socketObj = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    result = socketObj.connect_ex((ip, port))
    if result == 0:
        ifConnected = True
    else:
        ifConnected = False
    return ifConnected


# 判断URL最后的URI是否与输入的相同
def ifSameUri(uri, url):
    reFlag = False
    if uri == url[-1 * len(uri):]:
        reFlag = True
    else:
        reFlag = False
    return reFlag

# 传入一个URL，去除该URL参数的值，返回类似：http:domain:port/a1=&a2= 的字符串
def parseUrlWithoutArgsValue(url):
    reUrl = ""
    splitList = urllib.parse.urlsplit(url)
    nowArgs = splitList[3]
    # 去除参数值
    tmpArgsList = nowArgs.split("&")
    if len(tmpArgsList)==1 and tmpArgsList[0]=="":
        reUrl = url
    else:
        for argIndex,tmpArg in enumerate(tmpArgsList):
            tmpArgList = tmpArg.split("=")
            tmpList = tmpArgList[:1]+[""]
            tmpArgsList[argIndex]="=".join(tmpList)
        finalArgStr = "&".join(tmpArgsList)

        reUrl=urllib.parse.urlunsplit(tuple(list(splitList[:3])+[finalArgStr]+list(splitList[4:])))

    return reUrl