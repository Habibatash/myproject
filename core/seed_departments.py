from django.core.management.base import BaseCommand
from core.models import Department

DEPARTMENTS = [
    ('discovery', 'د معلوماتو مدیریت امریت', 'د اداري معلوماتو او اسنادو منظم ثبت', '🗂️', 1),
    ('technical', 'د تخنیکي ملاتړ او پېښو ثبت امریت', 'د تخنیکي ستونزو او پېښو اداري ثبت', '🛠️', 2),
    ('analytics', 'د راپورونو د تحلیل امریت', 'د راپورونو ارزونه او لنډیز', '📊', 3),
    ('websites', 'د وېب‌پاڼو او خبرونو آرشیف امریت', 'د عامه وېب‌پاڼو او خبرونو آرشیف', '🌐', 4),
    ('social', 'د عامه خپرونو آرشیف امریت', 'د عامه خپرونو او اعلانونو آرشیف', '📣', 5),
]

class Command(BaseCommand):
    help = 'د اصلي نمونې پنځه امریتونه جوړوي؛ موجود امریتونه نه تکراروي.'
    def handle(self, *args, **options):
        for slug, name, description, icon, order in DEPARTMENTS:
            Department.objects.update_or_create(slug=slug, defaults={'name':name,'description':description,'icon':icon,'sort_order':order,'is_active':True})
        self.stdout.write(self.style.SUCCESS('پنځه امریتونه چمتو شول.'))
