from flask import Flask  # 从flask包导入Flask类
from flask import url_for

app = Flask(__name__)  # 实例化类，创建一个程序对象app


@app.route('/')
def index():
    return 'Hello Flask'


@app.route('/user/<name>')  # 注册路由，使用装饰器绑定URL
def user_page(name):  # 请求处理函数
    return u'<h1>Hello %s!</h1>' % name


@app.route('/test')
def test_url_for():
    # 下面是一些调用示例（请在命令行窗口查看输出的 URL）：
    print(url_for('index'))  # 输出：/
    # 注意下面两个调用是如何生成包含 URL 变量的 URL 的
    print(url_for('user_page', name='greyli'))  # 输出：/user/gre yli
    print(url_for('user_page', name='peter'))  # 输出：/user/peter
    print(url_for('test_url_for'))  # 输出：/test
    # 下面这个调用传入了多余的关键字参数，它们会被作为查询字符串附加到 URL 后面。
    print(url_for('test_url_for', num=2))  # 输出：/test?num=2
    return 'Test page'


if __name__ == '__main__':
    app.run(debug=True)
