### 项目结构


#### local_get_document 目录
- /local_get_document 根目录
    - /main.py 程序源代码
        - /data
            - /conf 程序运行配置目录
                - account.txt 存放账号和密码，用 ------ 分隔
                - title.txt 标题，根据这些标题生成文章
                - runtime_conf.properties 运行时配置，用于初始化 account.json 文件
                - account.json 根据 account.txt 生成的 account.json 文件，记录了账号的详细信息
            - /static 登陆密码破解目录
                - jsencrypt.min.js 加密模块
                - pwd.html 调用加密模块页面
            - /document 产生的文档存放目录
    
#### web_login 目录
- /web_login 根目录
    - flask_web.py 程序源代码
    - account.txt 存放账号和密码，用 ------ 分隔
    - account.json 根据 account.txt 生成的 account.json 文件，记录了账号的详细信息、包括是否第一次登陆，以及首次登陆的唯一标识
    - app-runtime-log.log 运行时产生的日志文件
