import string
import random
import json
import requests
import hmac
import hashlib

from .geetest_lib_result import GeetestLibResult


# sdk lib包，核心逻辑。
class GeetestLib:
    IS_DEBUG = True  # 调试开关，是否输出调试日志
    API_URL = "http://api.geetest.com"
    REGISTER_URL = "/register.php"
    VALIDATE_URL = "/validate.php"
    JSON_FORMAT = 1
    NEW_CAPTCHA = True
    VERSION = "python-flask:3.1.0"
    GEETEST_CHALLENGE = "geetest_challenge"  # 极验二次验证表单传参字段 chllenge
    GEETEST_VALIDATE = "geetest_validate"  # 极验二次验证表单传参字段 validate
    GEETEST_SECCODE = "geetest_seccode"  # 极验二次验证表单传参字段 seccode
    GEETEST_SERVER_STATUS_SESSION_KEY = "gt_server_status"  # 极验验证API服务状态Session Key

    def __init__(self, geetest_id, geetest_key):
        self.geetest_id = geetest_id
        self.geetest_key = geetest_key
        self.libResult = GeetestLibResult()

    def gtlog(self, message):
        if self.IS_DEBUG:
            print("gtlog: " + message)

    # 一次验证
    def register(self, digestmod, param_dict):
        self.gtlog("register(): 开始一次验证, digestmod={0}.".format(digestmod));
        origin_challenge = self.request_register(param_dict)
        self.build_register_result(origin_challenge, digestmod)
        self.gtlog("register(): 一次验证, lib包返回信息={0}.".format(self.libResult));
        return self.libResult

    def request_register(self, param_dict):
        param_dict["gt"] = self.geetest_id
        param_dict["json_format"] = self.JSON_FORMAT
        register_url = self.API_URL + self.REGISTER_URL
        self.gtlog("requestRegister(): 一次验证, 向极验发送请求, url={0}, params={1}.".format(register_url, param_dict))
        try:
            res = requests.get(register_url, params=param_dict, timeout=2)
            if res.status_code == requests.codes.ok:
                res_body = res.text
            else:
                res_body = ""
            self.gtlog("requestRegister(): 一次验证, 与极验网络交互正常, 返回码={0}, 返回body={1}.".format(res.status_code, res_body))
            res_dict = json.loads(res_body)
            origin_challenge = res_dict["challenge"]
        except Exception as e:
            self.gtlog("requestRegister(): 一次验证, 请求异常，后续流程走failback模式, " + repr(e))
            origin_challenge = ""
        return origin_challenge

    # 构建一次验证返回数据
    def build_register_result(self, origin_challenge, digestmod):
        # origin_challenge为空或者值为0代表失败
        if not origin_challenge or origin_challenge == "0":
            # 本地随机生成32位字符串
            challenge = "".join(random.sample(string.ascii_letters + string.digits, 32))
            data = {"success": 0, "gt": self.geetest_id, "challenge": challenge, "new_captcha": self.NEW_CAPTCHA}
            self.libResult.set_all(0, data, "请求极验register接口失败，后续流程走failback模式")
        else:
            if digestmod == "md5":
                challenge = self.md5_encode(origin_challenge + self.geetest_key)
            elif digestmod == "sha256":
                challenge = self.sha256_endode(origin_challenge + self.geetest_key)
            elif digestmod == "hmac-sha256":
                challenge = self.hmac_sha256_endode(origin_challenge, self.geetest_key)
            else:
                challenge = self.md5_encode(origin_challenge + self.geetest_key)
            data = {"success": 1, "gt": self.geetest_id, "challenge": challenge, "new_captcha": self.NEW_CAPTCHA}
            self.libResult.set_all(1, data, "")

    # 正常流程下（即一次验证请求成功），二次验证
    def successValidate(self, challenge, validate, seccode, param_dict):
        self.gtlog(
            "successValidate(): 开始二次验证 正常模式, challenge={0}, validate={1}, seccode={2}.".format(challenge, validate,
                                                                                               seccode))
        if not self.check_param(challenge, validate, seccode):
            self.libResult.set_all(0, "", "正常模式，本地校验，参数challenge、validate、seccode不可为空")
        else:
            response_seccode = self.requestValidate(challenge, validate, seccode, param_dict)
            if not response_seccode:
                self.libResult.set_all(0, "", "请求极验validate接口失败")
            elif response_seccode == "false":
                self.libResult.set_all(0, "", "极验二次验证不通过")
            else:
                self.libResult.set_all(1, "", "")
        self.gtlog("successValidate(): 二次验证 正常模式, lib包返回信息={0}.".format(self.libResult))
        return self.libResult

    # 异常流程下（即failback模式），二次验证
    # 注意：由于是failback模式，初衷是保证验证业务不会中断正常业务，所以此处只作简单的参数校验，可自行设计逻辑。
    def failValidate(self, challenge, validate, seccode):
        self.gtlog(
            "failValidate(): 开始二次验证 failback模式, challenge={0}, validate={1}, seccode={2}.".format(challenge, validate,
                                                                                                  seccode))
        if not self.check_param(challenge, validate, seccode):
            self.libResult.set_all(0, "", "failback模式，本地校验，参数challenge、validate、seccode不可为空.")
        else:
            self.libResult.set_all(1, "", "")
        self.gtlog("failValidate(): 二次验证 failback模式, lib包返回信息={0}.".format(self.libResult))
        return self.libResult

    # 向极验发送二次验证的请求，POST方式
    def requestValidate(self, challenge, validate, seccode, param_dict):
        param_dict["seccode"] = seccode
        param_dict["json_format"] = self.JSON_FORMAT
        param_dict["challenge"] = challenge
        param_dict["sdk"] = self.VERSION
        param_dict["captchaid"] = self.geetest_id
        validate_url = self.API_URL + self.VALIDATE_URL
        self.gtlog("requestValidate(): 二次验证 正常模式, 向极验发送请求, url={0}, params={1}.".format(validate_url, param_dict))
        try:
            res = requests.post(validate_url, data=param_dict, timeout=2)
            if res.status_code == requests.codes.ok:
                res_body = res.text
            else:
                res_body = ""
            self.gtlog(
                "requestValidate(): 二次验证 正常模式, 与极验网络交互正常, 返回码={0}, 返回body={1}.".format(res.status_code, res_body))
            res_dict = json.loads(res_body)
            seccode = res_dict["seccode"]
        except Exception as e:
            self.gtlog("requestValidate(): 二次验证 正常模式, 请求异常, " + repr(e))
            seccode = ""
        return seccode

    # 校验二次验证的三个参数，校验通过返回true，校验失败返回false
    def check_param(self, challenge, validate, seccode):
        return challenge and validate and seccode

    def md5_encode(self, value):
        md5 = hashlib.md5()
        md5.update(value.encode("utf-8"))
        return md5.hexdigest()

    def sha256_endode(self, value):
        sha256 = hashlib.sha256()
        sha256.update(value.encode("utf-8"))
        return sha256.hexdigest()

    def hmac_sha256_endode(self, value, key):
        return hmac.new(key.encode("utf-8"), value.encode("utf-8"), digestmod=hashlib.sha256).hexdigest()
