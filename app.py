import sys, os
import click
from flask import Flask, render_template  # 从flask包导入Flask类
from flask import url_for, request, redirect, flash
from flask_sqlalchemy import SQLAlchemy
#  generate_password_hash 生成密码散列值，check_password_hash 检查散列值和密码是否对应
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import LoginManager, login_user, login_required, logout_user, current_user, UserMixin

WIN = sys.platform.startswith('win')
if WIN:  # 如果是 Windows 系统，使用三个斜线
    prefix = 'sqlite:///'
else:
    # 否则使用四个斜线
    prefix = 'sqlite:////'

app = Flask(__name__)  # 实例化类，创建一个程序对象app
app.secret_key = 'flask'
#  设置数据库URI
app.config['SQLALCHEMY_DATABASE_URI'] = prefix + os.path.join(app.root_path, 'data.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False  # 关闭对模型 修改的监控
db = SQLAlchemy(app)  # 初始化扩展，传入程序实例app
login_manager = LoginManager(app)
login_manager.login_view = 'login'


@login_manager.user_loader
def load_user(user_id):
    """
    创建用户加载回调函数，接收用户ID作为参数
    """
    user = User.query.get(int(user_id))  # 用ID作为User模型的主键查询对应的用户
    return user  # 返回用户对象


@app.cli.command()
@click.option('--username', prompt=True, help='The username used to login')
@click.option('--password', prompt=True, hide_input=True, confirmation_prompt=True, help='The password used to login')
def admin(username, password):
    """
    创建管理员
    """
    db.create_all()

    user = User.query.first()
    if user is not None:
        click.echo('更新用户...')
        user.username = username
        user.set_password(password)  # 设置密码
    else:
        click.echo('创建用户...')
        user = User(username=username, name='Admin')
        user.set_password(password)
        db.session.add(user)
    db.session.commit()  # 提交数据库会话
    click.echo('Done.')


@app.cli.command()
def forge():
    """
    命令函数，把虚拟数据添加到数据库中
    """
    db.create_all()
    name = 'Super'
    movies = [{'title': 'My Neighbor Totoro', 'year': '1988'}, {'title': 'Dead Poets Society', 'year': '1989'},
              {'title': 'A Perfect World', 'year': '1993'}, {'title': 'Leon', 'year': '1994'},
              {'title': 'Mahjong', 'year': '1996'}, {'title': 'Swallowtail Butterfly', 'year': '1996'},
              {'title': 'King of Comedy', 'year': '1999'}, {'title': 'Devils on the Doorstep', 'year': '1999'},
              {'title': 'WALL-E', 'year': '2008'}, {'title': 'The Pork of Music', 'year': '2012'}, ]
    user = User(name=name)
    db.session.add(user)
    for m in movies:
        movie = Movie(title=m['title'], year=m['year'])
        db.session.add(movie)
    db.session.commit()
    click.echo('Done.')


@app.cli.command()  # 注册为命令
@click.option('--drop', is_flag=True, help='Create after drop.')  # 设置选项
def initdb(drop):
    """
    自定义命令自动创建数据库表
    """
    """Initialize the database."""
    if drop:  # 判断是否输入了选项
        db.drop_all()
    db.create_all()
    click.echo('Initialized database.')  # 输出提示信息


#  创建数据库模型
class User(db.Model, UserMixin):  # 模型类要声明继承db.Model
    id = db.Column(db.Integer, primary_key=True)  # 主键
    name = db.Column(db.String(20))  # 名字
    username = db.Column(db.String(20))  # 用户名
    password_hash = db.Column(db.String(128))  # 密码散列值

    def set_password(self, password):
        """
        设置密码
        """
        self.password_hash = generate_password_hash(password)

    def validate_password(self, password):
        """
        验证密码
        """
        return check_password_hash(self.password_hash, password)


class Movie(db.Model):
    id = db.Column(db.Integer, primary_key=True)  # 主键
    title = db.Column(db.String(60))  # 电影标题
    year = db.Column(db.String(4))  # 年份


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        if not username or not password:
            flash('输入错误!')
            return redirect(url_for('login'))

        user = User.query.first()
        # 验证用户名和密码是否一致
        if username == user.username and user.validate_password(password):
            login_user(user)  # 登入用户
            flash('登录成功!')
            return redirect(url_for('index'))
        flash('用户名或者密码错误!')
        return redirect(url_for('login'))
    return render_template('login.html')


@app.route('/logout')
@login_required  # 用于视图保护
def logout():
    logout_user()  # 用户退出
    flash('欢迎再次光临!')
    return redirect(url_for('index'))


@app.route('/settings', methods=['GET', 'POST'])
@login_required
def settings():
    if request.method == 'POST':
        name = request.form['name']

        if not name or len(name) > 20:
            flash('输入错误!')
            return redirect(url_for('settings'))

        current_user.name = name
        db.session.commit()
        flash('更新成功!')
        return redirect(url_for('index'))
    return render_template('settings.html')


@app.context_processor
def inject_user():
    """
    模板上下文处理函数
    """
    user = User.query.first()
    return dict(user=user)


@app.route('/', methods=['GET', 'POST'])
def index():
    """
    主页视图函数
    """
    if request.method == 'POST':  # 判断是否POST请求
        if not current_user.is_authenticated:  # 如果当前用户未认证
            return redirect(url_for('index'))  # 重定向回主页
        # 获取表单数据
        title = request.form.get('title')  # 传入表单对应输入字段的值
        year = request.form.get('year')
        if not title or not year or len(year) < 4 or len(title) > 60:
            flash('输入错误!')  # 显示错误提示
            return redirect(url_for('index'))  # 重定向回主页面
        movie = Movie(title=title, year=year)  # 创建记录
        db.session.add(movie)  # 添加到数据库会话
        db.session.commit()  # 提交数据库会话
        flash('数据添加成功!')
        return redirect(url_for('index'))  # 数据添加成功重定向回主页面

    user = User.query.first()
    movies = Movie.query.all()
    # print(1 / 0)
    return render_template('index.html', movies=movies)


@app.route('/movie/edit/<int:movie_id>', methods=['GET', 'POST'])
@login_required
def edit(movie_id):
    """
    编辑页视图函数
    """
    movie = Movie.query.get_or_404(movie_id)  # 返回主键对应记录，若没有，则返回404错误响应
    if request.method == 'POST':
        title = request.form['title']
        year = request.form['year']
        if not title or not year or len(year) < 4 or len(title) > 60:
            flash('输入错误!')
            return redirect(url_for('edit', movie_id=movie_id))  # 重定向回编辑页面
        movie.title = title  # 更新标题
        movie.year = year  # 更新年份
        db.session.commit()  # 提交数据库会话
        flash('修改数据成功!')
        return redirect(url_for('index'))
    return render_template('edit.html', movie=movie)  # 传入被编辑的电影记录


@app.route('/movie/delete/<int:movie_id>', methods=['POST'])
@login_required
def delete(movie_id):
    """
    删除功能函数
    """
    movie = Movie.query.get_or_404(movie_id)
    db.session.delete(movie)
    db.session.commit()
    flash('删除成功!')
    return redirect(url_for('index'))


@app.errorhandler(404)
def page_not_found(e):  # 接收异常对象作为参数
    """
    404错误页面处理
    """
    user = User.query.first()
    return render_template('404.html'), 404


@app.errorhandler(500)
def page_500_error(e):
    """
    500服务器错误处理
    """
    return render_template('500.html'), 500
    # return "500 error"


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
