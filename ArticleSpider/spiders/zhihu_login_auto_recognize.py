import time
from random import choice
from time import sleep
import requests

from zheye import zheye

try:
    import cookielib
except:
    import http.cookiejar as cookielib
import re

try:
    from PIL import Image
except:
    pass

header = {
    "HOST": "www.zhihu.com",
    "Referer": "https://www.zhihu.com",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; WOW64; rv:54.0) Gecko/20100101 Firefox/54.0"
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


# 随机暂停，模拟人访问
def random_sleep():
    while choice([0, 1]):
        sleep(choice([0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8]))


# 获取验证码图片
def get_image_data():
    while True:
        t = str(int(time.time() * 1000))
        captcha_url = "https://www.zhihu.com/captcha.gif?r=%s&type=login&lang=cn" % t
        random_sleep()
        response = session.get(captcha_url, headers=header)
        # 写入图片
        with open("captcha.jpg", 'wb') as file:
            file.write(response.content)
            file.close()
            # 解析图片
        z = zheye()
        img_yanzheng = z.Recognize('captcha.jpg')
        # 把获得的坐标按x进行排序 [(48.647850377664284, 315.97586850515023), (49.944977855563351, 146.27730894630022)]
        img_yanzheng.sort(key=lambda x: x[1])
        # 知乎提交的位置数据和zheye解析的数据位置相反，置换成知乎要求的数据
        img_data = []
        for y, x in img_yanzheng:
            # zheye中图片为400*88像数，知乎要求为200*44，所有每个值都要除以2
            img_data.append((x / 2, y / 2))
        # 有数据表示解析成功，没数据重新请求数据再次解析
        if img_data:
            break
    return img_data


# 获取图片验证码
def get_captcha(img_data):
    """通过字符串格式化得到知乎想要的captcha值"""
    # captcha:{"img_size":[200,44],"input_points":[[120.375,34],[160.375,36]]}
    # first, second, third分别对应第一、第二、第三值，x，y 对应其中x，y坐标值
    first, second, third, x, y = 0, 1, 2, 0, 1
    if len(img_data) == 1:
        captcha = '{"img_size":[200,44],"input_points":[[%.2f,%.2f]]}' \
                  % (img_data[first][x], img_data[first][y])
    elif len(img_data) == 2:
        captcha = '{"img_size":[200,44],"input_points":[[%.2f,%.2f],[%.2f,%.2f]]}' \
                  % (img_data[first][x], img_data[first][y], img_data[second][x], img_data[second][y])
    elif len(img_data) == 3:
        captcha = '{"img_size":[200,44],"input_points":[[%.2f,%.2f],[%.2f,%.2f],[%.2f,%.2f]]}' \
                  % (
                      img_data[first][x], img_data[first][y], img_data[second][x], img_data[second][y],
                      img_data[third][x],
                      img_data[third][y])
    return captcha


# 通过查看用户个人信息来判断是否已经登录
def isLogin():
    url = "https://www.zhihu.com/settings/profile"
    login_code = session.get(url, headers=header, allow_redirects=False).status_code
    if int(x=login_code) == 200:
        return True
    else:
        return False


# 知乎登录操作
def login(account, password):
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
        post_data["captcha_type"] = "cn"
        post_data["captcha"] = get_captcha(get_image_data())
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


def clean_session_bug():
    # http://blog.csdn.net/sky247391475/article/details/69788246
    from keras import backend as K
    K.clear_session()


if __name__ == '__main__':
    if isLogin():
        print("您已经登录")
    else:
        account = input("请输入用户名\n>")
        password = input("请输入密码\n>")
        login(account, password)
    # bug fix
    clean_session_bug()
