import os
import sys
import queue
from selenium.webdriver.chrome.service import Service
import time
from selenium import webdriver
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By


# 初始化驱动
def init_web_driver():
    executable_path = current_path + 'chromedriver'

    if executable_path == '' or not os.path.exists(executable_path):
        input('没有在程序当前目录下找·到 chromedriver')
        sys.exit()

    options = webdriver.ChromeOptions()
    options.add_argument("--headless")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-images")
    options.add_argument("--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/101.0.0.0 Safari/537.36")

    return webdriver.Chrome(service=Service(executable_path=executable_path), options=options)


# 读取当前程序下的用户名、密码信息

def load_account_info():
    location = current_path + 'account.txt'

    if not os.path.exists(location):
        print("没有在程序当前目录下找到 {}".format('account.xlsx ，请创建一个名为 account.txt 的文本文档'))
        return

    print(time.strftime("[%Y-%m-%d %H:%M:%S]", time.localtime()) + "：读取账户信息...")
    tmp_queue = queue.Queue()

    with open(file=location, mode='r') as file:
        for i in file.readlines():
            tmp_queue.put(i)

    return tmp_queue


# 读取当前程序目录下的标题

def load_title_info():
    location = current_path + 'title.txt'
    if not os.path.exists(location):
        print("没有在程序当前目录下找到 {}".format('title.xlsx ，请创建一个名为 title.txt 的文本文档'))
        return

    print(time.strftime("[%Y-%m-%d %H:%M:%S]", time.localtime()) + "：读取标题列表...")
    tmp_queue = queue.Queue()

    with open(file=location, mode='r') as file:
        for i in file.readlines():
            tmp_queue.put(i)

    return tmp_queue


def into_document_produce():
    print(time.strftime("[%Y-%m-%d %H:%M:%S]", time.localtime()) + "：加载文档搜索页面...")
    try:
        WebDriverWait(web_driver, 30, 0.5).until(EC.element_to_be_clickable((By.XPATH, '//*[@id="app"]/div/div[5]/div/div[1]/button/i'))).click()
        WebDriverWait(web_driver, 30, 0.5).until(EC.element_to_be_clickable((By.CLASS_NAME, 'menu-user-login'))).click()
        WebDriverWait(web_driver, 30, 0.5).until(EC.element_to_be_clickable((By.XPATH, '//*[@id="login-wrap"]/div/div/span'))).click()
        WebDriverWait(web_driver, 30, 0.5).until(EC.element_to_be_clickable((By.XPATH, '//*[@id="login-wrap"]/div/div/ul[2]/li[3]/form/div[1]/div/div[1]/input'))).send_keys(account[0])
        WebDriverWait(web_driver, 30, 0.5).until(EC.element_to_be_clickable((By.XPATH, '//*[@id="login-wrap"]/div/div/ul[2]/li[3]/form/div[2]/div/div[1]/input'))).send_keys(account[1])
        WebDriverWait(web_driver, 30, 0.5).until(EC.element_to_be_clickable((By.XPATH, '//*[@id="login-wrap"]/div/div/ul[2]/li[3]/div/button'))).click()
        # --------------------------------------避免操作太快造成页面 BUG-------------------------------------- #
        time.sleep(2)
        # -------------------------------------------------------------------------------------------------#
        WebDriverWait(web_driver, 30, 0.5).until(EC.presence_of_element_located((By.XPATH, '//*[@id="menu"]/li[4]'))).click()
        WebDriverWait(web_driver, 30, 0.5).until(EC.element_to_be_clickable((By.XPATH, '//*[@id="app"]/div/div/div[3]/div/div'))).click()
    except Exception as e:
        info1 = time.strftime("[%Y-%m-%d %H:%M:%S]", time.localtime()) + "：发生错误，原因是 {} ，程序结束，日志以记录".format(e)
        print(info1)
        log.append(info1)
        web_driver.close()


if __name__ == '__main__':

    main_url = "https://xiezuocat.com/"
    current_path = sys.argv[0].replace(sys.argv[0].split(os.sep)[-1], '')

    account_queue = load_account_info()
    title_queue = load_title_info()
    web_driver = init_web_driver()

    log = []
    visit = 0

    account = account_queue.get().split('------')

    # -------------------------------------对主页发起 GET 请求------------------------------------- #
    print(time.strftime("[%Y-%m-%d %H:%M:%S]", time.localtime()) + "：等待页面响应...")
    web_driver.get(main_url)

    into_document_produce()
    # -------------------------------------如果还有标题，那就继续 poll 出数据------------------------------------- #
    while not title_queue.empty():
        if visit == 35:
            # -----------------------------该账号已经生成 35 次文章，切换下一个账号，并重置次数----------------------------- #
            print(time.strftime("[%Y-%m-%d %H:%M:%S]", time.localtime()) + "：当前账号 {} 已达最大文章生成次数，正在切换，并重置次数")
            account = account_queue.get().split('------')
            visit = 0
        visit += 1

        # ----------------------------------poll 出一个标题数据---------------------------------- #
        title = title_queue.get().replace('\n', '')

        try:
            document_search_navigation = WebDriverWait(web_driver, 30, 0.5).until(EC.element_to_be_clickable((By.XPATH, '//*[@id="app"]/div/div/div[2]/div[1]/input')))
            document_search_navigation.send_keys(title)
            WebDriverWait(web_driver, 30, 0.5).until(EC.element_to_be_clickable((By.XPATH, '//*[@id="app"]/div/div/div[2]/div[3]'))).click()

            print(time.strftime("[%Y-%m-%d %H:%M:%S]", time.localtime()) + "：文档生成中，等待目标响应...")

            # 这里开始获取文本，文本分为标题部分、前言部分、段落部分（段落部分可能有 1 个或多个，应该一次性获取所有的段落，也就是每个 li 标签，每个 li 标签中含有段落名称以及对应的内容）
            resp_title_p = WebDriverWait(web_driver, 60, 0.5).until(EC.presence_of_element_located((By.XPATH, '//*[@id="textArea"]/li/p[1]'))).text
            resp_reface_p = WebDriverWait(web_driver, 60, 0.5).until(EC.presence_of_element_located((By.XPATH, '//*[@id="textArea"]/li/p[2]'))).text
            resp_paragraphs = WebDriverWait(web_driver, 60, 0.5).until(EC.presence_of_element_located((By.XPATH, '//*[@id="textArea"]/li/ul')))
            resp_lis = resp_paragraphs.find_elements(By.TAG_NAME, 'li')

            # --------------------------------------写入数据-------------------------------------- #
            document_location = current_path + title + ".txt"
            print(time.strftime("[%Y-%m-%d %H:%M:%S]", time.localtime()) + "：正在将文章 [{}] 写入到 {}".format(title,
                                                                                                       document_location))
            with open(file=document_location, mode='w') as out:
                out.writelines(resp_title_p + '\n\n')
                out.writelines(resp_reface_p + '\n\n')
                for li in resp_lis:
                    ps = li.find_elements(By.TAG_NAME, 'p')
                    for p in ps:
                        out.writelines(p.text + '\n\n')
                out.flush()

            print(time.strftime("[%Y-%m-%d %H:%M:%S]", time.localtime()) + "：清空搜索栏")
            document_search_navigation.clear()
        except Exception as e:
            info2 = time.strftime("[%Y-%m-%d %H:%M:%S]", time.localtime()) + "：发生错误，原因是 {} ，本次文档 {} 可能不生成，日志已记录".format(e, title)
            print(info2)
            log.append(info2)
            pass

    log_location = current_path + 'runtime.log'
    with open(file=log_location, mode='w+') as f:
        if len(log) == 0:
            f.writelines("\n\n运行期间没有发生任何异常\n\n")

        for item in log:
            f.writelines(item + '\n\n')
    print(time.strftime("[%Y-%m-%d %H:%M:%S]", time.localtime()) + "：关闭驱动，程序结束，运行时日志已生成于 {} 下，再见".format(log_location))
    web_driver.close()
