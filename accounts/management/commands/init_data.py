from django.core.management.base import BaseCommand
from accounts.models import User
from locations.models import Location
from notifications.models import Notice


class Command(BaseCommand):
    help = '初始化校园位置数据和管理员账号'

    def handle(self, *args, **options):
        # 创建管理员账号
        if not User.objects.filter(username='admin').exists():
            admin = User.objects.create_superuser(
                username='admin',
                password='admin123',
                email='admin@campus.com',
                nickname='系统管理员',
                role='admin',
                credit_score=100,
            )
            self.stdout.write(self.style.SUCCESS(f'管理员账号创建成功: admin / admin123'))
        else:
            self.stdout.write(self.style.WARNING('管理员账号已存在'))

        # 创建测试学生账号
        if not User.objects.filter(username='student1').exists():
            User.objects.create_user(
                username='student1', password='123456',
                nickname='张三', student_id='2024001', role='student', credit_score=100,
            )
            User.objects.create_user(
                username='student2', password='123456',
                nickname='李四', student_id='2024002', role='student', credit_score=95,
            )
            User.objects.create_user(
                username='student3', password='123456',
                nickname='王五', student_id='2024003', role='student', credit_score=88,
            )
            self.stdout.write(self.style.SUCCESS('测试学生账号创建成功: student1/student2/student3, 密码: 123456'))

        # 创建校园位置
        locations_data = [
            # 宿舍区
            {'name': '1号宿舍楼', 'campus_area': 'dormitory', 'longitude': 116.3250, 'latitude': 39.9850, 'description': '男生宿舍1号楼'},
            {'name': '2号宿舍楼', 'campus_area': 'dormitory', 'longitude': 116.3255, 'latitude': 39.9855, 'description': '男生宿舍2号楼'},
            {'name': '3号宿舍楼', 'campus_area': 'dormitory', 'longitude': 116.3260, 'latitude': 39.9848, 'description': '女生宿舍1号楼'},
            {'name': '4号宿舍楼', 'campus_area': 'dormitory', 'longitude': 116.3265, 'latitude': 39.9853, 'description': '女生宿舍2号楼'},
            # 教学楼
            {'name': '第一教学楼', 'campus_area': 'teaching', 'longitude': 116.3280, 'latitude': 39.9870, 'description': '主教学楼，A/B/C三栋'},
            {'name': '第二教学楼', 'campus_area': 'teaching', 'longitude': 116.3290, 'latitude': 39.9875, 'description': '理工科教学楼'},
            {'name': '实验楼', 'campus_area': 'teaching', 'longitude': 116.3295, 'latitude': 39.9868, 'description': '各类实验室'},
            # 食堂
            {'name': '第一食堂', 'campus_area': 'canteen', 'longitude': 116.3270, 'latitude': 39.9860, 'description': '一楼中餐，二楼面食'},
            {'name': '第二食堂', 'campus_area': 'canteen', 'longitude': 116.3275, 'latitude': 39.9865, 'description': '综合餐厅'},
            # 图书馆
            {'name': '中心图书馆', 'campus_area': 'library', 'longitude': 116.3285, 'latitude': 39.9880, 'description': '主图书馆，共6层'},
            # 体育馆
            {'name': '体育馆', 'campus_area': 'gymnasium', 'longitude': 116.3240, 'latitude': 39.9870, 'description': '室内篮球、羽毛球、乒乓球'},
            {'name': '田径场', 'campus_area': 'playground', 'longitude': 116.3235, 'latitude': 39.9875, 'description': '400米标准跑道'},
            # 超市
            {'name': '校内超市', 'campus_area': 'supermarket', 'longitude': 116.3268, 'latitude': 39.9858, 'description': '日用品、零食饮料'},
            # 校门
            {'name': '学校正门', 'campus_area': 'gate', 'longitude': 116.3300, 'latitude': 39.9840, 'description': '南门，校园主入口'},
            {'name': '学校北门', 'campus_area': 'gate', 'longitude': 116.3270, 'latitude': 39.9890, 'description': '北门'},
            # 办公区
            {'name': '行政楼', 'campus_area': 'office', 'longitude': 116.3290, 'latitude': 39.9885, 'description': '学校行政办公'},
        ]

        created = 0
        for loc_data in locations_data:
            _, was_created = Location.objects.get_or_create(
                name=loc_data['name'],
                defaults=loc_data,
            )
            if was_created:
                created += 1
        self.stdout.write(self.style.SUCCESS(f'位置数据初始化完成，新增 {created} 个位置'))

        # 创建欢迎公告
        admin_user = User.objects.filter(role='admin').first()
        if admin_user and not Notice.objects.exists():
            Notice.objects.create(
                title='欢迎使用校园互助服务平台',
                content='校园互助服务平台正式上线！在这里你可以发布各类互助需求，包括物品租借、学习互助、事务求助、兼职对接和失物招领。\n\n平台特色功能：\n1. 校园位置定位 - 发布需求时可选择校园位置\n2. 信誉积分系统 - 完成互助加分，激励良好行为\n3. 双向评价 - 互助完成后双方可互相评价\n4. 附近需求 - 按位置查看附近的互助需求\n\n快来体验吧！',
                admin=admin_user,
            )
            self.stdout.write(self.style.SUCCESS('欢迎公告创建成功'))

        self.stdout.write(self.style.SUCCESS('=== 初始化完成 ==='))
        self.stdout.write('管理员账号: admin / admin123')
        self.stdout.write('学生账号: student1 / 123456, student2 / 123456, student3 / 123456')
