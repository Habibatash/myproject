from django.test import TestCase
from django.core.exceptions import PermissionDenied
from django.test import RequestFactory
from .models import Department, Document, User
from .permissions import visible_documents, can_view_document, can_edit_document
from .views import _department_for_user

class DepartmentPermissionTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.a = Department.objects.create(slug='a', name='امریت الف')
        cls.b = Department.objects.create(slug='b', name='امریت ب')
        cls.gm = User.objects.create_user(username='gm@example.com', email='gm@example.com', password='StrongPass!123', role='gm', approved=True, is_active=True)
        cls.deputy = User.objects.create_user(username='deputy@example.com', email='deputy@example.com', password='StrongPass!123', role='deputy', department=cls.a, approved=True, is_active=True)
        cls.amir = User.objects.create_user(username='amir@example.com', email='amir@example.com', password='StrongPass!123', role='amir', department=cls.a, approved=True, is_active=True)
        cls.employee = User.objects.create_user(username='employee@example.com', email='employee@example.com', password='StrongPass!123', role='employee', department=cls.a, approved=True, is_active=True)
        cls.other_employee = User.objects.create_user(username='other@example.com', email='other@example.com', password='StrongPass!123', role='employee', department=cls.b, approved=True, is_active=True)
        cls.doc_a = Document.objects.create(title='A', department=cls.a, created_by=cls.employee)
        cls.doc_b = Document.objects.create(title='B', department=cls.b, created_by=cls.other_employee)

    def test_general_manager_sees_all_but_deputy_only_own(self):
        self.assertEqual(visible_documents(self.gm).count(), 2)
        self.assertEqual(visible_documents(self.deputy).count(), 0)
        own = Document.objects.create(title='Deputy own', department=self.a, created_by=self.deputy)
        self.assertEqual(list(visible_documents(self.deputy)), [own])

    def test_amir_sees_employee_docs_only_in_own_department(self):
        deputy_doc = Document.objects.create(title='Deputy A', department=self.a, created_by=self.deputy)
        amir_doc = Document.objects.create(title='Amir own', department=self.a, created_by=self.amir)
        visible = set(visible_documents(self.amir).values_list('pk', flat=True))
        self.assertEqual(visible, {self.doc_a.pk, deputy_doc.pk, amir_doc.pk})
        self.assertTrue(can_edit_document(self.amir, self.doc_a))
        self.assertFalse(can_view_document(self.amir, self.doc_b))

    def test_employee_sees_only_own_documents(self):
        self.assertEqual(list(visible_documents(self.employee)), [self.doc_a])
        self.assertTrue(can_edit_document(self.employee, self.doc_a))
        self.assertFalse(can_view_document(self.employee, self.doc_b))

    def test_non_manager_cannot_submit_for_another_department(self):
        request = RequestFactory().post('/documents/', {'department': self.b.pk})
        request.user = self.employee
        with self.assertRaises(PermissionDenied):
            _department_for_user(request, self.b.pk)



class AccessAndMentionTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        from .models import Post, Comment
        cls.a = Department.objects.create(slug='a2', name='الف')
        cls.b = Department.objects.create(slug='b2', name='ب')
        mk = lambda n, role, dept: User.objects.create_user(username=f'{n}@x.com', email=f'{n}@x.com', password='StrongPass!123', first_name=n, role=role, department=dept, approved=True, is_active=True, email_verified=True)
        cls.gm = mk('gm', 'gm', None)
        cls.amir_a = mk('amira', 'amir', cls.a)
        cls.amir_b = mk('amirb', 'amir', cls.b)
        cls.emp_a = mk('empa', 'employee', cls.a)
        cls.emp_b = mk('empb', 'employee', cls.b)
        cls.post_a = Post.objects.create(author=cls.emp_a, department=cls.a, text='x')
        cls.post_b = Post.objects.create(author=cls.emp_b, department=cls.b, text='y')

    def test_edit_delete_scope_for_posts(self):
        from .permissions import can_edit_post
        self.assertTrue(can_edit_post(self.gm, self.post_a) and can_edit_post(self.gm, self.post_b))
        self.assertTrue(can_edit_post(self.amir_a, self.post_a))
        self.assertFalse(can_edit_post(self.amir_a, self.post_b))
        self.assertTrue(can_edit_post(self.emp_a, self.post_a))
        self.assertFalse(can_edit_post(self.emp_a, self.post_b))

    def test_reports_are_not_visible_across_amirs_or_employees(self):
        d = Document.objects.create(title='d', department=self.b, created_by=self.amir_b)
        self.assertNotIn(d, visible_documents(self.amir_a))
        self.assertNotIn(d, visible_documents(self.emp_a))
        self.assertIn(d, visible_documents(self.gm))

    def test_employee_cannot_open_departments_page(self):
        self.client.force_login(self.emp_a)
        self.assertEqual(self.client.get('/departments/').status_code, 302)
        self.client.force_login(self.gm)
        self.assertEqual(self.client.get('/departments/').status_code, 200)

    def test_mention_list_contains_every_other_user_and_notifies(self):
        from .models import Notification
        from .services import notify_mentions
        self.client.force_login(self.emp_a)
        names = {u['name'] for u in self.client.get('/api/mention-users/').json()['users']}
        self.assertEqual(names, {'gm', 'amira', 'amirb', 'empb'})
        notify_mentions('hi', self.emp_a, '/news/', ids=[self.amir_b.pk])
        self.assertTrue(Notification.objects.filter(recipient=self.amir_b).exists())

    def test_login_requires_verified_email(self):
        u = User.objects.create_user(username='n@x.com', email='n@x.com', password='StrongPass!123', approved=True, is_active=True, email_verified=False)
        with self.settings(EMAIL_VERIFICATION_REQUIRED=True):
            r = self.client.post('/accounts/login/', {'username': 'n@x.com', 'password': 'StrongPass!123'})
        self.assertEqual(r.status_code, 200)
        self.assertNotIn('_auth_user_id', self.client.session)
