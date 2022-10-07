import ctypes

import requests_html
import json
import queue
import threading
import time
import os
import sys
from concurrent.futures import ThreadPoolExecutor
from threading import Thread
import requests
import uvicorn
from fastapi.responses import HTMLResponse
from starlette.responses import FileResponse
from copy import deepcopy
from fastapi import FastAPI


class Init:
    """
        负责初始化一些配置，包括运行时配置、标题文件、账号文件、初始化驱动
    """

    def __init__(self):
        self.debug = True
        self.log = []
        self.account_item_list = []
        self.properties_tmp = {}
        self.log_location = current_path + "\\data\\log\\runtime.log"
        self.title_location = current_path + '\\data\\conf\\title.txt'
        self.runtime_conf_location = current_path + '\\data\\conf\\runtime_conf.properties'
        self.account_text_location = current_path + '\\data\\conf\\account.txt'
        self.login_url = "https://xiezuocat.com/login"
        self.user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/105.0.0.0 Safari/537.36 Edg/105.0.1343.50"
        self.referer = "https://xiezuocat.com/"

    @staticmethod
    def init_fast_api():

        # 静态资源
        @app.get("/static/{file_path:path}")
        async def static(file_path: str):
            return FileResponse(current_path + "\\data\\static\\" + file_path)

        @app.get("/{pwd}", response_class=HTMLResponse)
        async def server(pwd: str):
            with open(current_path + "\\data\\static\\pwd.html", mode="r", encoding="utf-8") as f:
                html = f.read()

            html = html.replace("{{ pwd }}", pwd)
            return html

        Thread(target=uvicorn.run, kwargs={"app": app, "host": "127.0.0.1", "port": 8000}).start()

    def load_account_info(self):

        """
            加载账号文件，生成账号 json 文件，并返回 json 字典
        :return: json 字典
        """

        if not os.path.exists(self.account_text_location) and not os.path.exists(account_json_location):
            self.__static_print_log_and_force_write_log(
                "程序终止，没有在程序当前目录下找到 {}".format('account.txt ，请创建一个名为 account.txt 或 account.json 文件'))

        if not os.path.exists(account_json_location):
            if not self.__static_create_account_json_file(self.account_text_location, account_json_location):
                self.__static_print_log_and_force_write_log('初始化失败，原因是创建账号 json 文件失败')

        with open(file=account_json_location, mode='r', encoding='utf-8') as j:
            return json.load(j)

    def load_title_info(self):

        """
            加载 title.txt 并得到一个装满标题的队列
            :return: queue 队列
        """

        if not os.path.exists(self.title_location):
            self.__static_print_log_and_force_write_log(
                "程序终止，没有在程序当前目录下找到 {}".format('title.txt ，请创建一个名为 title.txt 的文本文档'))

        print(time.strftime("[%Y-%m-%d %H:%M:%S]", time.localtime()) + "：加载标题列表...")
        tmp_queue = queue.Queue()

        with open(file=self.title_location, mode='r', encoding='utf-8') as file:
            for i in file.readlines():
                tmp_queue.put(i)

        return tmp_queue

    def load_runtime_conf(self):

        self.__static_print(time.strftime("[%Y-%m-%d %H:%M:%S]", time.localtime()) + "：加载运行时配置...")

        if self.runtime_conf_location == '' or not os.path.exists(self.runtime_conf_location):
            input('程序终止，没有在程序当前目录下找到 runtime_conf.properties 配置文件')
            sys.exit()

        with open(file=self.runtime_conf_location, mode='r', encoding='utf-8') as conf:
            for line in conf:
                if line.find('=') > 0:
                    line = line.replace('\n', '').split('=')
                    self.properties_tmp[line[0]] = line[1]

        return self.properties_tmp

    def __static_create_account_json_file(self, account_text_location, account_json_location):
        print("登陆所有账号")
        self.account_item_list.clear()
        with open(file=account_text_location, mode='r', encoding='utf-8') as text:
            for line in text.readlines():
                line = line.split("------")
                default_account_max_product_size = int(runtime_conf.get('default_account_max_product_size'))
                username = line[0].replace('\n', '')
                password = line[1].replace('\n', '')
                account_item = {
                    "status": 1,
                    "username": username,
                    "password": password,
                    "account_max_product_size": default_account_max_product_size,
                    "account_can_use_size": default_account_max_product_size,
                    "account_use_size": 0,
                    "login_response": self.__static_login(username, password)
                }

                self.account_item_list.append(account_item)

        with open(file=account_json_location, mode='w+', encoding='utf-8') as write_json:
            write_json.write(json.dumps({"accounts": self.account_item_list,
                                         "last_modify_time": time.time()}))

        return os.path.exists(account_json_location)

    def __static_login(self, username, password):

        data = {
            "login_by": "account",
            "account": username,
            "pwd": ""}

        url = "http://127.0.0.1:8000/" + password

        # 自动下载驱动
        session = requests_html.HTMLSession()
        r = session.get(url)

        data["pwd"] = r.html.render(script="a()", timeout=200).strip()

        resp = requests.post(url=self.login_url, headers={
            "user-agent": self.user_agent,
            "referer": self.referer,
        }, data=data)

        return resp.json()

    def __static_print_log_and_force_write_log(self, info):

        """
            初始化过程中发生意外将调用这个方法并调用 __static_force_write_log 打印并生成日志
            :param info: 异常信息
            :return: None
        """

        self.__static_print(info)

        with open(file=self.log_location, mode='w+', encoding='utf-8') as f:
            f.writelines(info + '\n\n')

    @staticmethod
    def __static_print(info):
        print(time.strftime("[%Y-%m-%d %H:%M:%S]", time.localtime()) + info)


class DocumentProduce:
    def __init__(self):
        self.title_queue = title_queue
        self.login_url = "https://xiezuocat.com/html/generate/pc/document?isSampleDocument=false"
        self.user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.159 Safari/537.36"
        self.referer = "https://xiezuocat.com/"
        self.origin = "https://xiezuocat.com"
        self.content_type = "application/json"
        self.accept = "application/json, text/plain, */*; charset=utf-8"
        self.executor_queue = queue.Queue()

    def run(self):

        global __thread
        while True:
            if not self.title_queue.empty():
                task = []
                for i in range(int(runtime_conf.get("step"))):
                    if not self.title_queue.empty():
                        __title = self.title_queue.get().replace('\n', '')
                        __account = account_manager(force_update=False)
                        __request_body = self.__request_param_wrapper(__account.get("login_response").get("data"),
                                                                      __title)

                        task.append(threading.Thread(target=self.__request_and_write_document,
                                                     args=([__request_body, __title, __account])))

                for t in task:
                    t.start()
                while len(task) != 0:
                    print("等待线程响应...")
                    time.sleep(2)
                    for t in task:
                        if not t.is_alive():
                            print("子线程完成：" + task.pop().getName())

            else:
                print("没有更多标题，程序结束")
                sys.exit()

    # 请求参数包装
    def __request_param_wrapper(self, data, title):
        __uid = data.get("uid")
        __sid = data.get("sid")
        headers = {
            "User-Agent": self.user_agent,
            "referer": self.referer,
            "origin": self.origin,
            "content-type": self.content_type,
            "accept": "",
            "cookie": "uid={}; sid={};".format(__uid, __sid)
        }
        data = {
            "length": "default",
            "data": {"title": title}
        }

        return {"headers": headers, "data": data}

    def __request_and_write_document(self, request_body, title, __account):
        print("处理：" + title)
        __response_json = requests.post(url=self.login_url, headers=request_body.get("headers"),
                                        json=request_body.get("data")).json()
        print(__response_json)
        if __response_json.get("errCode") == 0:
            # success

            with open(file=current_path + "\\data\\document\\{}.txt".format(title), mode='w', encoding='utf-8') as j:
                intro = __response_json.get("data").get("result").get("intro") + '\n\n'
                contents_list = __response_json.get("data").get("result").get("contents")
                j.write(intro)
                for item in contents_list:
                    j.write(item.get("title") + "\n\n")
                    j.write(item.get("intro") + "\n\n")
                j.flush()

        elif __response_json.get("errCode") == 401:
            # 有异常时把标题返回队列
            self.title_queue.put(title)
            print("账号被禁止登陆")
            pass
        elif __response_json.get("errCode") == 4001:
            # threshold
            # 有异常时把标题返回队列
            self.title_queue.put(title)
            # lock.release()
            print(account_big_json_dict)
            if account_manager(force_update=True) is None:
                lock.release()

        # json.dump(__response_json.json(),
        #           open(current_path + "data/document/{}.txt".format(title), mode='w+', encoding='utf-8'),
        #           ensure_ascii=False, indent=4)


first_get_account = True
pop_account = []
backup_big_json_account = {}


def account_manager(force_update):
    global first_get_account, current_use_account, account_big_json_dict, backup_big_json_account

    if force_update:
        print("给定的账号意外不可用：" + str(current_use_account))
        current_use_account.update({"status": 0})
        # 这里是为了本地更新
        update_account(current_use_account)
        pop_account.append(current_use_account)
        if len(account_big_json_dict.get("accounts")) == 0:
            print("已经没有可用的账号")
            return None
        else:
            current_use_account = account_big_json_dict.get("accounts").pop()
            print("切换新的账号：{}".format(current_use_account))
            lock.release()
            return current_use_account

    lock.acquire()

    not_size = 0
    if first_get_account:
        account_big_json_dict = init.load_account_info()
        for j in account_big_json_dict.get("accounts"):
            if j.get("status") == 0:
                not_size += 1
        if not_size == len(account_big_json_dict.get("accounts")):
            print("没有可用账号")
            sys.exit()

        backup_big_json_account = deepcopy(account_big_json_dict)
        current_use_account = account_big_json_dict.get("accounts").pop()
        first_get_account = False
        print("获取账号：" + str(current_use_account))

    # 对当前账号 current_use_account 进行校验
    while (
            current_use_account.get("status") == 0
            and current_use_account.get("account_can_use_size") == 0
            and current_use_account.get("account_use_size") == current_use_account.get("account_max_product_size")
    ):
        # 没有更多的可用账号
        if len(account_big_json_dict.get("accounts")) == 0:
            print(
                "已经没有可用的账号，但线程可能还会继续")
            return current_use_account
        else:
            pop_account.append(current_use_account)
            current_use_account = account_big_json_dict.get("accounts").pop()
            print("切换新的账号：{}".format(current_use_account))

    # 这里开始请求
    print("发起请求，当前使用账号：" + str(current_use_account))

    update_account(current_use_account)

    lock.release()

    return current_use_account


def update_account(current_use_account):
    """
    更新当前使用账号的信息，这个方法线程安全，不要对 account_big_json_dict 中的 accounts 做任何修改，这个任务应该交给 account_manager
    :return: None
    """

    if time.strftime("%d", time.localtime(account_big_json_dict.get("last_modify_time"))) != time.strftime("%d",
                                                                                                           time.localtime(
                                                                                                               time.time())):
        # 检查时间，如果过了 12 点刷新所有账号状态
        print("距离上次账号的最后修改时间已经过去一天了，将重新加载所有账号信息")
        if os.path.exists(account_json_location):
            os.remove(account_json_location)
        global first_get_account
        first_get_account = True
        return

    if (
            current_use_account.get("account_can_use_size") - 1 < 0
            and current_use_account.get("account_use_size") + 1 > current_use_account.get("account_max_product_size")
    ):
        current_use_account.update(
            {
                "status": 0,
            }
        )
    else:
        current_use_account.update(
            {
                "account_can_use_size": current_use_account.get("account_can_use_size") - 1,
                "account_use_size": current_use_account.get("account_use_size") + 1
            }
        )

    account_big_json_dict.update(
        {
            "last_modify_time": time.time()
        }
    )

    update_account_json(current_use_account)


def update_account_json(current_use_account):
    # 实时更新本地 json 文件，这个方法应该是 update_account 执行完后被调用

    with open(file=account_json_location, mode='w+', encoding='utf-8') as update:
        account_list = backup_big_json_account.get("accounts")
        for item in account_list:
            if item.get("username") == current_use_account.get("username"):
                item.update(current_use_account)
        print("实时更新 account.json")
        print(backup_big_json_account)
        update.write(json.dumps(backup_big_json_account))


def write_runtime_log_and_close_resource():
    """
        负责生成运行时日志，并关闭所有资源
    :return:
    """

    pass


def run():
    produce = DocumentProduce()
    produce.run()


if __name__ == '__main__':
    ctypes.windll.kernel32.SetConsoleTitleW("QQ：2243321642")
    current_path = os.path.dirname(os.path.realpath(sys.argv[0]))

    account_json_location = current_path + '\\data\\conf\\account.json'
    app = FastAPI()

    init = Init()
    init.init_fast_api()
    time.sleep(3)
    lock = threading.Lock()

    title_queue = init.load_title_info()
    runtime_conf = init.load_runtime_conf()

    visit = 0
    first_start = True
    main_url = runtime_conf.get('url')

    run()
