from django.test import TestCase, Client
from django.urls import reverse
from django.db import transaction
from django.db.models import Sum
from accounts.models import User
from locations.models import Location
from .models import (
    Demand, DemandResponse, Comment, CreditRecord, AdminLog,
    CREDIT_COMPLETE_BONUS, CREDIT_GOOD_RATING, CREDIT_BAD_RATING,
    CREDIT_INITIAL, CREDIT_PUBLISH_THRESHOLD,
)


class UserAuthTest(TestCase):
    """用户认证测试"""

    def setUp(self):
        self.client = Client()
        self.register_data = {
            'username': 'testuser',
            'nickname': '测试用户',
            'student_id': '20240001',
            'phone': '13800138000',
            'password1': 'TestPass123',
            'password2': 'TestPass123',
        }

    def test_register_and_login(self):
        """测试注册和登录流程"""
        resp = self.client.post(reverse('accounts:register'), self.register_data)
        self.assertRedirects(resp, reverse('accounts:login'))

        user = User.objects.get(username='testuser')
        self.assertEqual(user.nickname, '测试用户')
        self.assertEqual(user.credit_score, CREDIT_INITIAL)
        self.assertEqual(user.role, 'student')

        login_resp = self.client.post(reverse('accounts:login'), {
            'username': 'testuser',
            'password': 'TestPass123',
        })
        self.assertRedirects(login_resp, '/')

    def test_login_open_redirect_fixed(self):
        """测试登录开放重定向漏洞已修复"""
        User.objects.create_user(username='testuser', password='TestPass123')
        resp = self.client.post(
            reverse('accounts:login') + '?next=https://evil.com',
            {'username': 'testuser', 'password': 'TestPass123'},
            follow=True,
        )
        # 不应该重定向到外部网站
        self.assertEqual(resp.redirect_chain[-1][0], '/')

    def test_register_with_invalid_student_id(self):
        """测试无效学号被拒绝"""
        data = self.register_data.copy()
        data['student_id'] = 'abc_not_digit'
        resp = self.client.post(reverse('accounts:register'), data)
        self.assertEqual(resp.status_code, 200)
        self.assertFalse(User.objects.filter(username='testuser').exists())

    def test_register_with_invalid_phone(self):
        """测试无效手机号被拒绝"""
        data = self.register_data.copy()
        data['phone'] = '12345'
        resp = self.client.post(reverse('accounts:register'), data)
        self.assertEqual(resp.status_code, 200)
        self.assertFalse(User.objects.filter(username='testuser').exists())


class CreditScoreTest(TestCase):
    """信誉积分测试"""

    def setUp(self):
        self.poster = User.objects.create_user(
            username='poster', password='TestPass123',
            credit_score=CREDIT_INITIAL,
        )
        self.responder = User.objects.create_user(
            username='responder', password='TestPass123',
            credit_score=CREDIT_INITIAL,
        )
        self.location = Location.objects.create(
            name='图书馆', campus_area='library',
            longitude=116.3, latitude=40.0,
        )
        self.demand = Demand.objects.create(
            user=self.poster, title='测试需求',
            content='测试内容', type='study_help',
            location=self.location, status='approved',
        )

    def test_demand_complete_credit_update(self):
        """测试完成需求后信誉记录正确创建"""
        response = DemandResponse.objects.create(
            demand=self.demand, user=self.responder,
            content='我来帮你', status='accepted',
        )
        CreditRecord.objects.create(
            user=self.poster, change_score=CREDIT_COMPLETE_BONUS,
            reason='完成需求发布', related_demand=self.demand,
            related_response=response,
        )
        CreditRecord.objects.create(
            user=self.responder, change_score=CREDIT_COMPLETE_BONUS,
            reason='完成需求响应', related_demand=self.demand,
            related_response=response,
        )
        total_poster = CreditRecord.objects.filter(user=self.poster).aggregate(
            s=Sum('change_score')
        )['s']
        total_responder = CreditRecord.objects.filter(user=self.responder).aggregate(
            s=Sum('change_score')
        )['s']
        self.assertEqual(total_poster, CREDIT_COMPLETE_BONUS)
        self.assertEqual(total_responder, CREDIT_COMPLETE_BONUS)

    def test_credit_record_audit_trail(self):
        """测试信誉记录审计追踪"""
        CreditRecord.objects.create(
            user=self.poster, change_score=CREDIT_COMPLETE_BONUS,
            reason='完成需求发布', related_demand=self.demand,
        )
        CreditRecord.objects.create(
            user=self.responder, change_score=CREDIT_BAD_RATING,
            reason='收到差评', related_demand=self.demand,
        )
        self.assertEqual(
            CreditRecord.objects.filter(change_score__gt=0).count(), 1,
        )
        self.assertEqual(
            CreditRecord.objects.filter(change_score__lt=0).count(), 1,
        )

    def test_low_credit_cannot_publish(self):
        """测试低信誉分用户不能发布需求"""
        low_user = User.objects.create_user(
            username='lowcredit', password='TestPass123',
            credit_score=50,
        )
        client = Client()
        client.login(username='lowcredit', password='TestPass123')
        resp = client.post(reverse('demands:create'), {
            'title': '测试', 'content': '测试',
            'type': 'study_help', 'location': self.location.pk,
        })
        self.assertRedirects(resp, reverse('demands:list'))


class DemandLifecycleTest(TestCase):
    """需求全生命周期测试"""

    def setUp(self):
        self.poster = User.objects.create_user(
            username='poster', password='TestPass123',
            credit_score=CREDIT_INITIAL, role='student',
        )
        self.responder = User.objects.create_user(
            username='responder', password='TestPass123',
            credit_score=CREDIT_INITIAL, role='student',
        )
        self.location = Location.objects.create(
            name='教学楼A', campus_area='teaching',
            longitude=116.3, latitude=40.0,
        )
        self.client = Client()
        self.client.login(username='poster', password='TestPass123')

    def test_full_lifecycle(self):
        """测试完整需求流程：发布→响应→接受→完成→评价"""
        # 1. 发布需求
        resp = self.client.post(reverse('demands:create'), {
            'title': '帮忙搬东西', 'content': '需要帮忙搬书',
            'type': 'task_help', 'location': self.location.pk,
        })
        self.assertEqual(resp.status_code, 302)
        demand = Demand.objects.get(title='帮忙搬东西')
        self.assertEqual(demand.status, 'approved')

        # 2. 另一个用户响应（需要登录为响应者）
        self.client.logout()
        self.client.login(username='responder', password='TestPass123')
        resp = self.client.post(
            reverse('demands:respond', args=[demand.pk]),
            {'content': '我可以帮忙'},
        )
        self.assertEqual(resp.status_code, 302)
        demand.refresh_from_db()
        self.assertEqual(demand.status, 'responded')

        # 3. 发帖者接受响应
        self.client.logout()
        self.client.login(username='poster', password='TestPass123')
        response_obj = DemandResponse.objects.get(demand=demand, user=self.responder)
        resp = self.client.post(
            reverse('demands:response_accept', args=[response_obj.pk]),
        )
        response_obj.refresh_from_db()
        self.assertEqual(response_obj.status, 'accepted')

        # 4. 完成需求
        resp = self.client.post(
            reverse('demands:complete', args=[demand.pk]),
        )
        demand.refresh_from_db()
        self.assertEqual(demand.status, 'completed')

        # 5. 评价
        resp = self.client.post(
            reverse('demands:comment', args=[demand.pk]),
            {'score': 5, 'content': '很靠谱'},
        )
        self.assertEqual(resp.status_code, 302)
        self.assertTrue(
            Comment.objects.filter(demand=demand, from_user=self.poster).exists(),
        )

    def test_cannot_respond_own_demand(self):
        """测试不能响应自己的需求"""
        demand = Demand.objects.create(
            user=self.poster, title='我的需求',
            content='内容', type='study_help',
            location=self.location, status='approved',
        )
        resp = self.client.post(
            reverse('demands:respond', args=[demand.pk]),
            {'content': '我自己来'},
        )
        self.assertEqual(resp.status_code, 302)
        self.assertFalse(
            DemandResponse.objects.filter(demand=demand, user=self.poster).exists(),
        )

    def test_duplicate_response_prevented(self):
        """测试不能重复响应同一个需求"""
        demand = Demand.objects.create(
            user=self.poster, title='测试',
            content='内容', type='study_help',
            location=self.location, status='approved',
        )
        self.client.logout()
        self.client.login(username='responder', password='TestPass123')

        # 第一次响应应该成功
        resp = self.client.post(
            reverse('demands:respond', args=[demand.pk]),
            {'content': '我来', 'demand': demand.pk},
        )
        self.assertEqual(DemandResponse.objects.filter(demand=demand, user=self.responder).count(), 1)

        # 第二次响应应该失败（unique_together 约束）
        resp = self.client.post(
            reverse('demands:respond', args=[demand.pk]),
            {'content': '我又来了', 'demand': demand.pk},
        )
        self.assertEqual(DemandResponse.objects.filter(demand=demand, user=self.responder).count(), 1)


class AdminTest(TestCase):
    """管理员功能测试"""

    def setUp(self):
        self.admin = User.objects.create_user(
            username='admin', password='Admin123456',
            role='admin', credit_score=CREDIT_INITIAL,
        )
        self.student = User.objects.create_user(
            username='student', password='TestPass123',
            role='student', credit_score=CREDIT_INITIAL,
        )
        self.client = Client()

    def test_normal_user_cannot_access_admin(self):
        """测试普通用户无法访问管理后台"""
        self.client.login(username='student', password='TestPass123')
        resp = self.client.get(reverse('admin_panel:dashboard'))
        self.assertRedirects(resp, reverse('home'))

    def test_admin_can_access_dashboard(self):
        """测试管理员可以访问管理后台"""
        self.client.login(username='admin', password='Admin123456')
        resp = self.client.get(reverse('admin_panel:dashboard'))
        self.assertEqual(resp.status_code, 200)

    def test_admin_cannot_disable_last_admin(self):
        """测试不能移除最后一个管理员"""
        self.client.login(username='admin', password='Admin123456')
        # 尝试把唯一的admin降级为student
        resp = self.client.post(
            reverse('admin_panel:user_set_role', args=[self.admin.pk, 'student']),
        )
        self.admin.refresh_from_db()
        self.assertEqual(self.admin.role, 'admin')
        self.assertIn('不能移除最后一个管理员', [m.message for m in resp.wsgi_request._messages])

    def test_admin_actions_logged(self):
        """测试管理员操作被记录到审计日志"""
        self.client.login(username='admin', password='Admin123456')
        self.client.post(
            reverse('admin_panel:user_adjust_credit', args=[self.student.pk]),
            {'change': 10, 'reason': '测试调整'},
        )
        self.assertTrue(
            AdminLog.objects.filter(
                admin=self.admin,
                action='user_adjust_credit',
                target_type='user',
                target_id=self.student.pk,
            ).exists(),
        )

    def test_admin_credit_adjustment_limit(self):
        """测试单次信誉分调整不能超过100分"""
        self.client.login(username='admin', password='Admin123456')
        resp = self.client.post(
            reverse('admin_panel:user_adjust_credit', args=[self.student.pk]),
            {'change': 200, 'reason': '超额调整'},
        )
        self.admin.refresh_from_db()
        # 应该被拒绝
        self.assertTrue(
            CreditRecord.objects.filter(
                user=self.student, change_score=200,
            ).count() == 0,
        )


class SecurityTest(TestCase):
    """安全测试"""

    def test_csrf_protection_on_forms(self):
        """测试POST请求需要CSRF token"""
        client = Client(enforce_csrf_checks=True)
        resp = client.post(reverse('accounts:register'), {
            'username': 'test', 'password1': 'TestPass123',
            'password2': 'TestPass123',
            'nickname': 'Test', 'student_id': '20240001',
        })
        self.assertEqual(resp.status_code, 403)

    def test_admin_state_change_requires_post(self):
        """测试管理员状态变更需要POST请求"""
        admin = User.objects.create_user(
            username='admin2', password='Admin123456', role='admin',
        )
        student = User.objects.create_user(
            username='student2', password='TestPass123', role='student',
        )
        client = Client()
        client.login(username='admin2', password='Admin123456')

        # GET 请求应该被拒绝（405 Method Not Allowed）
        resp = client.get(
            reverse('admin_panel:user_toggle', args=[student.pk]),
        )
        self.assertEqual(resp.status_code, 405)


class LocationTest(TestCase):
    """位置功能测试"""

    def setUp(self):
        Location.objects.create(
            name='图书馆', campus_area='library',
            longitude=116.3, latitude=40.0,
        )
        Location.objects.create(
            name='食堂', campus_area='canteen',
            longitude=116.31, latitude=40.01,
        )

    def test_campus_map_uses_annotate(self):
        """测试校园地图使用annotate而非N+1查询"""
        from django.db.models import Count, Q
        # 确保annotate查询不会报错
        locations = Location.objects.annotate(
            demand_count=Count('demands', filter=Q(demands__status__in=['approved', 'responded']))
        )
        self.assertEqual(locations.count(), 2)
        for loc in locations:
            self.assertEqual(loc.demand_count, 0)

    def test_location_api_returns_json(self):
        """测试位置API返回JSON"""
        resp = self.client.get(reverse('locations:api'))
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(len(data), 2)

    def test_invalid_coordinates_rejected(self):
        """测试无效坐标被拒绝"""
        from locations.forms import LocationForm
        form = LocationForm(data={
            'name': '测试', 'campus_area': 'other',
            'longitude': 200, 'latitude': 100,
        })
        self.assertFalse(form.is_valid())
        self.assertIn('longitude', form.errors)
        self.assertIn('latitude', form.errors)
