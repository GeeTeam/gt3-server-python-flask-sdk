from flask import Flask, render_template, session, request

from geetest_config import GEETEST_ID, GEETEST_KEY
from sdk.geetest_lib import GeetestLib

app = Flask(__name__)


@app.route("/")
def login():
    return render_template("index.html")


@app.route("/register", methods=["GET"])
def first_register():
    gt_lib = GeetestLib(GEETEST_ID, GEETEST_KEY)
    user_id = "test"
    digestmod = "md5"
    param_dict = {}
    param_dict["digestmod"] = digestmod  # 必传参数，此版本sdk可支持md5、sha256、hmac-sha256，md5之外的算法需特殊配置的账号，联系极验客服
    # 以下自定义参数,可选择添加
    param_dict["user_id"] = user_id  # 网站用户id
    param_dict["client_type"] = "web"  # web:电脑上的浏览器; h5:手机上的浏览器,包括移动应用内完全内置的web_view; native:通过原生SDK植入APP应用的方式
    param_dict["ip_address"] = "127.0.0.1"  # 传输用户请求验证时所携带的IP
    result = gt_lib.register(digestmod, param_dict)
    # 将结果状态设置到session中
    # 注意，此处api1接口存入session，api2会取出使用，格外注意session的存取和分布式环境下的应用场景
    session[GeetestLib.GEETEST_SERVER_STATUS_SESSION_KEY] = result.status
    session["user_id"] = user_id
    # 注意，不要更改返回的结构和值类型
    return result.data


@app.route("/validate", methods=["POST"])
def second_validate():
    challenge = request.form.get(GeetestLib.GEETEST_CHALLENGE, None)
    validate = request.form.get(GeetestLib.GEETEST_VALIDATE, None)
    seccode = request.form.get(GeetestLib.GEETEST_SECCODE, None)
    status = session.get(GeetestLib.GEETEST_SERVER_STATUS_SESSION_KEY, None)
    user_id = session.get("user_id", None)
    # session必须取出值，若取不出值，直接当做异常退出
    if status is None:
        return {"result": "fail", "version": GeetestLib.VERSION, "msg": "session取key发生异常"}
    gt_lib = GeetestLib(GEETEST_ID, GEETEST_KEY)
    if status == 1:
        param_dict = {}
        # 自定义参数,可选择添加
        param_dict["user_id"] = user_id  # 网站用户id
        param_dict["client_type"] = "web"  # web:电脑上的浏览器; h5:手机上的浏览器,包括移动应用内完全内置的web_view; native:通过原生SDK植入APP应用的方式
        param_dict["ip_address"] = "127.0.0.1"  # 传输用户请求验证时所携带的IP
        result = gt_lib.successValidate(challenge, validate, seccode, param_dict)
    else:
        result = gt_lib.failValidate(challenge, validate, seccode)
    if result.status == 1:
        response = {"result": "success", "version": GeetestLib.VERSION}
    else:
        response = {"result": "fail", "version": GeetestLib.VERSION, "msg": result.msg}
    return response


if __name__ == "__main__":
    app.secret_key = "python-flask:3.1.0"
    app.run(host="0.0.0.0", port=5000, debug=True)
