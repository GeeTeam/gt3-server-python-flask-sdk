from flask import Flask, render_template, session, request, Response, jsonify

from geetest_config import GEETEST_ID, GEETEST_KEY
from sdk.geetest_lib import GeetestLib

app = Flask(__name__)


@app.route("/favicon.ico")
def favicon():
    return app.send_static_file('favicon.ico')


@app.route("/")
def index():
    return app.send_static_file("index.html")


# 验证初始化接口，GET请求
@app.route("/register", methods=["GET"])
def first_register():
    # 必传参数
    #     digestmod 此版本sdk可支持md5、sha256、hmac-sha256，md5之外的算法需特殊配置的账号，联系极验客服
    # 自定义参数,可选择添加
    #     user_id 客户端用户的唯一标识，确定用户的唯一性；作用于提供进阶数据分析服务，可在register和validate接口传入，不传入也不影响验证服务的使用；若担心用户信息风险，可作预处理(如哈希处理)再提供到极验
    #     client_type 客户端类型，web：电脑上的浏览器；h5：手机上的浏览器，包括移动应用内完全内置的web_view；native：通过原生sdk植入app应用的方式；unknown：未知
    #     ip_address 客户端请求sdk服务器的ip地址
    gt_lib = GeetestLib(GEETEST_ID, GEETEST_KEY)
    digestmod = "md5"
    user_id = "test"
    param_dict = {"digestmod": digestmod, "user_id": user_id, "client_type": "web", "ip_address": "127.0.0.1"}
    result = gt_lib.register(digestmod, param_dict)
    # 将结果状态写到session中，此处register接口存入session，后续validate接口会取出使用
    # 注意，此demo应用的session是单机模式，格外注意分布式环境下session的应用
    session[GeetestLib.GEETEST_SERVER_STATUS_SESSION_KEY] = result.status
    session["user_id"] = user_id
    # 注意，不要更改返回的结构和值类型
    return Response(result.data, content_type='application/json;charset=UTF-8')


# 二次验证接口，POST请求
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
        # 自定义参数,可选择添加
        #     user_id 客户端用户的唯一标识，确定用户的唯一性；作用于提供进阶数据分析服务，可在register和validate接口传入，不传入也不影响验证服务的使用；若担心用户信息风险，可作预处理(如哈希处理)再提供到极验
        #     client_type 客户端类型，web：电脑上的浏览器；h5：手机上的浏览器，包括移动应用内完全内置的web_view；native：通过原生sdk植入app应用的方式；unknown：未知
        #     ip_address 客户端请求sdk服务器的ip地址
        param_dict = {"user_id": user_id, "client_type": "web", "ip_address": "127.0.0.1"}
        result = gt_lib.successValidate(challenge, validate, seccode, param_dict)
    else:
        result = gt_lib.failValidate(challenge, validate, seccode)
    # 注意，不要更改返回的结构和值类型
    if result.status == 1:
        response = {"result": "success", "version": GeetestLib.VERSION}
    else:
        response = {"result": "fail", "version": GeetestLib.VERSION, "msg": result.msg}
    return jsonify(response)


if __name__ == "__main__":
    app.secret_key = GeetestLib.VERSION
    app.run(host="0.0.0.0", port=5000, debug=True)
