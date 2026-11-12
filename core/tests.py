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
