from celery import shared_task
from companies.models import Company, Notification, CompanyMembership
from products.models import Product


@shared_task
def create_notification_for_new_member(company_id, membership_id):
    company = Company.objects.get(id=company_id)
    membership = CompanyMembership.objects.get(id=membership_id)
    admins_and_owners = CompanyMembership.objects.filter(
        company=company, role__in=["admin", "owner"]
    ).select_related("user")

    message = (
        f"새로운 직원 {membership.user.username}님이 {company.name}에 가입했습니다."
    )
    target_url = f"/api/v1/companies/{company.id}/members/{membership.user.id}/"
    for membership in admins_and_owners:
        Notification.objects.create(
            recipient=membership.user,
            company=company,
            message=message,
            target_url=target_url,
        )


@shared_task
def create_notification_for_new_product(company_id, product_id):
    company = Company.objects.get(id=company_id)
    product = Product.objects.get(id=product_id)
    admins_and_owners = CompanyMembership.objects.filter(
        company=company, role__in=["admin", "owner"]
    ).select_related("user")

    message = f"새로운 물건 {product.name}이(가) {company.name}에 등록되었습니다."
    target_url = product.get_absolute_url()

    for membership in admins_and_owners:
        Notification.objects.create(
            recipient=membership.user,
            company=company,
            message=message,
            target_url=target_url,
        )
