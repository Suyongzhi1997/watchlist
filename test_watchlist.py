import unittest
from app import app, db, Movie, User


class WatchlistTestCase(unittest.TestCase):
    def setUp(self):
        #  更新配置
        app.config.update(
            TESTING=True,
            SQLALCHEMY_DATABASE='sqlite:///:memory'
        )
        db.create_all()
        user = User(name='Test', username='test')
        user.set_password('123')
        movie = Movie(title='Test Movie title', year=2020)
        db.session.add_all([user, movie])
        db.session.commit()

        self.client = app.test_client()
        self.runner = app.test_cli_runner()

    def tearDown(self):
        db.session.remove()
        db.drop_all()

    def test_app_exist(self):
        self.assertIsNotNone(app)

    def test_app_is_testing(self):
        self.assertTrue(app.config['TESTING'])

    def test_404_page(self):
        response = self.client.get('/nothing')  # 传入目标 URL
        data = response.get_data(as_text=True)
        self.assertIn('Page Not Found - 404', data)
        self.assertIn('Go Back', data)
        self.assertEqual(response.status_code, 404)  # 判断响应状 态码 # 测试主页

    def test_index_page(self):
        response = self.client.get('/')
        data = response.get_data(as_text=True)
        self.assertIn('Test\'s Watchlist', data)
        self.assertIn('Test Movie Title', data)
        self.assertEqual(response.status_code, 200)

    def login(self):
        self.client.post('/login', data=dict(username='test', password='123'), follow_redirects=True)

    def test_create_item(self):
        self.login()
        # 测试创建条目操作
        response = self.client.post('/', data=dict(title='New Movie', year='2019'), follow_redirects=True)
        data = response.get_data(as_text=True)
        self.assertIn('Item created.', data)
        self.assertIn('New Movie', data)
        # 测试创建条目操作，但电影标题为空
        response = self.client.post('/', data=dict(title='', year='2019'), follow_redirects=True)
        data = response.get_data(as_text=True)
        self.assertNotIn('Item created.', data)
        self.assertIn('Invalid input.', data)
        # 测试创建条目操作，但电影年份为空
        response = self.client.post('/', data=dict(title='New Movie', year=''), follow_redirects=True)
        data = response.get_data(as_text=True)
        self.assertIn('Item created.', data)
        self.assertIn('New Movie', data)
