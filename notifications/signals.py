# notifications/signals.py
from django.db.models.signals import post_save
from django.dispatch import receiver
from products.models import Product
from companies.models import CompanyMembership
from .tasks import create_notifications


@receiver(post_save, sender=Product)
def notify_product_added(sender, instance, created, **kwargs):
    if created:
        company = instance.company
        admin_ids = CompanyMembership.objects.filter(
            company=company, role__in=["admin", "owner"]
        ).values_list("user__id", flat=True)
        if admin_ids:
            message = (
                f"회사 {company.name}에 새 제품 '{instance.name}'이(가) 추가되었습니다."
            )
            create_notifications.delay(
                list(admin_ids), "product_added", message, instance.id
            )


@receiver(post_save, sender=CompanyMembership)
def notify_member_added(sender, instance, created, **kwargs):
    if created:
        company = instance.company
        admin_ids = (
            CompanyMembership.objects.filter(
                company=company, role__in=["admin", "owner"]
            )
            .exclude(user=instance.user)
            .values_list("user__id", flat=True)
        )
        if admin_ids:
            message = f"회사 {company.name}에 새 멤버 '{instance.user.username}'이(가) 추가되었습니다."
            create_notifications.delay(
                list(admin_ids), "member_added", message, instance.id
            )
