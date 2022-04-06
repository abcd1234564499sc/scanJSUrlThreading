# 扫描网站JS中的URL（多线程版）    
开发语言：python  
使用图形界面库：pyqt5  
多线程库：QThread  
使用pyinstaller打包成exe可执行程序   
是用来扫描JS中URL的扫描器，程序处理流程如下：   
1、输入一个URL   
2、自动获取网站上a标签的链接（只获取与输入URL主域名相同的链接），加入爬虫列表   
3、自动获取网站上script标签的js链接 ，加入爬虫列表   
4、爬虫请求爬虫列表的链接，对于js文件，使用正则匹配所有疑似URL信息，与以下地址结合：   
(1) 输入的URL   
(2) 输入URL的域名   
(3) 当前JS文件的域名   
(4) 当前JS文件的URL   
(5) 当前输入的额外URL   
结合方式是urllib.parse.join()函数，将生成的地址去重后加入爬虫列表   
5、爬虫对于其他文件（html、jsp等网页文件），使用requests库访问，若访问成功则记录响应码和标题，并显示在图形界面   
   
扫描地址用于发起扫描，额外地址不会参加扫描，但会参与到URL结合过程中，参考上述过程4   
配置界面可以设置最大线程、代理、敏感信息关键词以及对扫描结果的过滤   
界面截图如下：   
![主界面](https://github.com/abcd1234564499sc/scanJSUrlThreading/blob/main/img/main.jpg "主界面")    
   
![配置界面](https://github.com/abcd1234564499sc/scanJSUrlThreading/blob/main/img/conf.jpg "配置界面")
