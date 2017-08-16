import os

import requests
import time

try:
    import cookielib
except:
    import http.cookiejar as cookielib
import re

try:
    from PIL import Image
except:
    pass

# Mozilla/5.0 (Windows NT 10.0; WOW64; rv:54.0) Gecko/20100101 Firefox/54.0
agent = "Mozilla/5.0 (Windows NT 10.0; WOW64; rv:54.0) Gecko/20100101 Firefox/54.0"
header = {
    "HOST": "www.zhihu.com",
    "Referer": "https://www.zhihu.com",
    "User-Agent": agent
}

session = requests.session()
session.cookies = cookielib.LWPCookieJar(filename="cookies.txt")


# 获取xsrf code
def get_xsrf():
    index_url = "https://www.zhihu.com"
    response = session.get(index_url, headers=header)
    match_obj = re.match('.*name="_xsrf" value="(.*?)"', response.text, re.DOTALL)  # 启用DOTALL模式
    if match_obj:
        return match_obj.group(1)
    else:
        return ""


# 获取图片验证码
def get_captcha():
    t = str(int(time.time() * 1000))
    captcha_url = 'https://www.zhihu.com/captcha.gif?r=' + t + "&type=login"
    r = session.get(captcha_url, headers=header)
    with open('captcha.jpg', 'wb') as f:
        f.write(r.content)
        f.close()
    # 用pillow 的 Image 显示验证码
    # 如果没有安装 pillow 到源代码所在的目录去找到验证码然后手动输入
    try:
        im = Image.open('captcha.jpg')
        im.show()
        im.close()
    except:
        print(u'请到 %s 目录找到captcha.jpg 手动输入' % os.path.abspath('captcha.jpg'))
    captcha = input("please input the captcha\n>")
    return captcha


# 通过查看用户个人信息来判断是否已经登录
def isLogin():
    url = "https://www.zhihu.com/settings/profile"
    login_code = session.get(url, headers=header, allow_redirects=False).status_code
    if int(x=login_code) == 200:
        return True
    else:
        return False


def login(account, password):
    # 知乎登录
    if re.match("^1\d{10}", account):
        print("手机号码登录")
        post_url = "https://www.zhihu.com/login/phone_num"
        post_data = {
            "_xsrf": get_xsrf(),
            "phone_num": account,
            "password": password,
        }
    else:
        if "@" in account:
            print("邮箱登录")
            post_url = "https://www.zhihu.com/login/email"
            post_data = {
                "_xsrf": get_xsrf(),
                "email": account,
                "password": password,
            }

    # 不需要验证码登录
    response = session.post(post_url, data=post_data, headers=header)
    print(response.text)
    print(response.status_code)
    if response.json()['r'] != 0:
        # 不输入验证码登录失败
        # 使用需要输入验证码的方式登录
        post_data["captcha"] = get_captcha()
        response = session.post(post_url, data=post_data, headers=header)
        print(response.text)
        print(response.status_code)
        if response.json()['r'] == 0 and response.status_code == 200:
            print("登录成功!")
    # 保存 cookies 到文件，
    # 下次可以使用 cookie 直接登录，不需要输入账号和密码
    session.cookies.save()
    if isLogin():
        print("您已经登录")


if __name__ == '__main__':
    if isLogin():
        print("您已经登录")
    else:
        account = input("请输入用户名\n>")
        password = input("请输入密码\n>")
        login(account, password)
