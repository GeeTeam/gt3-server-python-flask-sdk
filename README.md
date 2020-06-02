# gt3-server-python-flask-sdk

## 示例开发环境
|项目|说明|
|----|------|
|操作系统|Ubuntu 16.04.6 LTS|
|python版本|3.5.2|

## 部署流程
### 下载sdk demo
```
git clone https://github.com/GeeTeam/gt3-server-python-flask-sdk.git
```

### 配置密钥，修改请求参数
> 配置密钥

从[极验管理后台](https://auth.geetest.com/login/)获取您的公钥（id）和私钥（key）, 并在代码中配置。配置文件的相对路径如下：
```
geetest_config.py
```

> 修改请求参数（可选）

名称|说明
----|------
user_id|user_id作为终端用户的唯一标识，确定用户的唯一性；作用于提供进阶数据分析服务，可在api1 或 api2 接口传入，不传入也不影响验证服务的使用；若担心用户信息风险，可作预处理(如哈希处理)再提供到极验
client_type|客户端类型，**web**（pc浏览器），**h5**（手机浏览器，包括webview），**native**（原生app），**unknown**（未知）
ip_address|客户端请求您服务器的ip地址，**unknow**表示未知

### 关键文件说明
名称|说明|相对路径
----|----|----
app.py|项目启动入口和接口请求控制器，主要处理一次验证和二次验证请求|
geetest_config.py|配置id和key|
geetest_lib.py|核心sdk，处理各种业务|sdk/
geetest_lib_result.rb|核心sdk返回数据的包装对象|sdk/
index.html|demo示例首页|templates/

### 运行demo
```
cd gt3-server-python-flask-sdk
sudo pip install -r requirements.txt
sudo python3 app.py
```
在浏览器中访问`http://localhost:5000`即可看到demo界面。

## 发布日志

### tag：20200601
- 统一各语言sdk标准
- 版本：python-flask:3.1.0

