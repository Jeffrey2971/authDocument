import os
import sys
import json
from flask import Flask, request
from copy import deepcopy
import threading
import logging

current_path = os.path.dirname(os.path.realpath(sys.argv[0]))
app = Flask(__name__)
lock = threading.Lock()
logger = logging.getLogger()
log_path = current_path + "/app-runtime-log.log"
logger.setLevel(level=logging.INFO)
handler = logging.FileHandler(log_path, mode='w', encoding='utf-8')
handler.setFormatter(logging.Formatter(fmt='%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
logger.addHandler(handler)


class Account:

    def __init__(self):
        self.account_json_file = current_path + "/account.json"
        self.account_text_file = current_path + "/account.txt"

    def start(self, reload):

        if reload:
            lock.acquire()
            if os.path.exists(self.account_json_file):
                os.remove(self.account_json_file)
            lock.release()

        if os.path.exists(self.account_json_file):
            app.logger.info("尝试读取已存在的账号文件：" + self.account_json_file)
            with open(file=self.account_json_file, mode='r', encoding='utf-8') as f:
                data = f.read()
                if len(data) != 0:
                    global runtime_conf
                    runtime_conf = json.loads(data)
                else:
                    self.__create_account_json_file(self.account_json_file)

        else:
            self.__create_account_json_file(self.account_json_file)

    def update_local_account_json(self):
        app.logger.info("账号信息变动，更新账号信息，操作已加锁")
        with open(file=self.account_json_file, mode='w+', encoding='utf-8') as update:
            update.write(json.dumps(runtime_conf))

    def __create_account_json_file(self, account_json_file):
        app.logger.info("加载原始账号文件，创建账号配置文件：" + self.account_text_file)

        with open(file=self.account_text_file, mode='r', encoding='utf-8') as f:
            accounts = f.readlines()
            supports_account = []
            for account in accounts:
                account = account.replace('\n', '').split("------")
                account = {
                    "username": account[0],
                    "password": account[1],
                    "authorization_code": '',
                    "first_login": True
                }
                supports_account.append(account)

        global runtime_conf
        runtime_conf = {"accounts": supports_account}
        with open(file=account_json_file, mode='w+', encoding='utf-8') as f:
            app.logger.info("写入账号配置文件" + account_json_file)
            f.write(json.dumps(runtime_conf))


@app.route('/login', methods=['POST'])
def login():
    if request.method == 'POST':
        app.logger.info("用户发起 POST 请求")

        # bytes 类型
        content = request.get_json()

        username = content.get('uname')
        password = content.get("pwd")
        only_code = content.get("code")

        app.logger.info("=============DEBUG=============")
        app.logger.info("接收参数:" + username)
        app.logger.info("接收参数：" + password)
        app.logger.info("接收参数：" + only_code)

        if username is None or username == '' or password is None or password == '' or only_code is None or only_code == '':
            return fail_response("用户登陆失败，原因是用户上传的所需信息不全")

        accounts_list = runtime_conf.get("accounts")

        for account in accounts_list:
            app.logger.info("比对参数：" + account.get("username"))
            app.logger.info("比对参数：" + account.get("password"))
            app.logger.info("=============DEBUG=============")
            if username == account.get("username") and password == account.get("password"):
                # 判断是否首次登陆
                if account.get("first_login"):
                    app.logger.info("用户首次登陆成功，已记录首次登陆机器码，如下次登陆和本次登陆机器码不符将拒绝登陆")
                    lock.acquire()
                    # 保存首次登陆的机器码，并设置首次登陆为 False
                    account["first_login"] = False
                    account["authorization_code"] = only_code
                    runtime_conf.update({"accounts": accounts_list})
                    account_init.update_local_account_json()
                    lock.release()
                    return success_response("用户登陆成功：" + username)
                else:
                    # 不是首次登陆，检查机器码是否匹配
                    lock.acquire()
                    if account.get("authorization_code") == only_code:
                        lock.release()
                        return success_response("用户登陆成功：" + username)
                    else:
                        lock.release()
                        return fail_response("用户登陆失败，原因是虽然用户尝试使用账号密码登陆成功，但本次登陆和首次登陆时的唯一标识不符")

        return fail_response("用户登陆失败，原因是账号或密码不存在于 account.json 文件中")
    else:
        return fail_response("用户登陆失败，原因是用户使用了错误的请求方式")


@app.route('/reload', methods=['GET'])
def reload():
    user = request.args.get("name")
    code = request.args.get("code")
    print(user)
    print(code)
    if user == 'admin' and code == 'XZMCNZXJCKLWEQJCKXZC2347839475___2347xcvbhjxkcbv':
        app.logger.info("程序接收到远程重载账号指令，加锁操作" + log_path)
        account_init.start(reload=True)
        return success_response("已重载账号配置")
    else:
        return fail_response("非法操作")


def fail_response(msg):
    app.logger.info(msg)
    return json.dumps({
        "status": "fail",
        "reason": msg
    }, ensure_ascii=False)


def success_response(msg):
    app.logger.info(msg)
    return json.dumps(
        {
            "status": "success",
            "reason": msg
        },
        ensure_ascii=False
    )


if __name__ == '__main__':
    app.logger.info("程序启动，日志生成于：" + log_path)

    account_init = Account()
    account_init.start(reload=False)
    backups_account_data = deepcopy(runtime_conf)

    print("程序启动，日志生成于：" + log_path)
    app.config['JSON_AS_ASCII'] = False
    app.run(host='0.0.0.0', port=8080)
