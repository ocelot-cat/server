from datetime import timedelta
from celery import shared_task
from django.db.models import F, Q, Avg, Sum
from django.db.models.functions import Coalesce
from companies.models import Company
from products.models import Product, ProductImage, ProductRecord, ProductRecordSnapshot
from products.services import upload_image_to_cloudflare
import os
import logging
from django.utils import timezone
from django.core.cache import cache

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3)
def upload_image_to_cloudflare_task(
    self, temp_file_path, product_id, content_type=None
):
    logger.info(
        f"Task attempt {self.request.retries + 1}/{self.max_retries + 1} for product {product_id} with file {temp_file_path}, content_type: {content_type}"
    )
    try:
        product = Product.objects.get(id=product_id)
        with open(temp_file_path, "rb") as image_file:
            image_url = upload_image_to_cloudflare(
                image_file, content_type=content_type
            )
        ProductImage.objects.filter(product=product).delete()
        ProductImage.objects.create(product=product, image_url=image_url)
        product.image_upload_status = "completed"
        product.save()
        logger.info(f"Image uploaded for product {product_id}: {image_url}")
    except Product.DoesNotExist as exc:
        logger.error(f"Product {product_id} not found: {str(exc)}")
        if self.request.retries < self.max_retries:
            logger.info(f"Retrying image upload task for product {product_id}")
            self.retry(countdown=10, exc=exc)
        else:
            logger.error(
                f"Failed to upload image for product {product_id}: Product does not exist"
            )
    except Exception as exc:
        logger.error(f"Async image upload failed for product {product_id}: {str(exc)}")
        if self.request.retries >= self.max_retries:
            try:
                logger.info(
                    f"Switching to synchronous upload for product {product_id} at {timezone.now()}"
                )
                with open(temp_file_path, "rb") as image_file:
                    image_url = upload_image_to_cloudflare(
                        image_file, content_type=content_type
                    )
                product = Product.objects.get(id=product_id)
                ProductImage.objects.filter(product=product).delete()
                ProductImage.objects.create(product=product, image_url=image_url)
                product.image_upload_status = "completed"
                product.save()
                logger.info(
                    f"Synchronous upload succeeded for product {product_id}: {image_url}"
                )
            except Exception as sync_exc:
                logger.error(
                    f"Synchronous upload failed for product {product_id}: {str(sync_exc)}"
                )
                product = Product.objects.get(id=product_id)
                product.image_upload_status = "failed"
                ProductImage.objects.filter(product=product).delete()
                ProductImage.objects.create(
                    product=product, image_url="https://picsum.photos/1000"
                )
                product.save()
                logger.warning(f"Set default image for product {product_id}")
        else:
            logger.info(f"Retrying image upload task for product {product_id}")
            self.retry(countdown=60, exc=exc)
    finally:
        if self.request.retries >= self.max_retries and os.path.exists(temp_file_path):
            try:
                os.remove(temp_file_path)
                logger.info(f"Temporary file {temp_file_path} deleted")
            except Exception as e:
                logger.error(
                    f"Failed to delete temporary file {temp_file_path}: {str(e)}"
                )


@shared_task
def create_daily_product_snapshots():
    companies = Company.objects.all()
    snapshot_date = timezone.now().date()
    last_month = snapshot_date - timedelta(days=30)
    thirty_days_ago = last_month - timedelta(days=30)

    for company in companies:
        stock_data = (
            ProductRecord.objects.filter(product__company=company)
            .values("product")
            .annotate(
                total_pieces=Sum(
                    (F("box_quantity") * Coalesce(F("product__pieces_per_box"), 1))
                    + F("piece_quantity")
                    - F("consumed_quantity"),
                    filter=Q(record_type="in"),
                )
            )
        )

        for data in stock_data:
            product = Product.objects.get(id=data["product"])
            total_pieces = data["total_pieces"] or 0
            box_quantity = (
                total_pieces // product.pieces_per_box if product.pieces_per_box else 0
            )
            piece_quantity = (
                total_pieces % product.pieces_per_box
                if product.pieces_per_box
                else total_pieces
            )

            ProductRecordSnapshot.objects.update_or_create(
                company=company,
                product=product,
                snapshot_date=snapshot_date,
                defaults={
                    "box_quantity": box_quantity,
                    "piece_quantity": piece_quantity,
                    "total_pieces": total_pieces,
                },
            )

            avg_stock_data = ProductRecordSnapshot.objects.filter(
                product=product,
                snapshot_date__lte=last_month,
                snapshot_date__gte=thirty_days_ago,
            ).aggregate(avg_total_pieces=Avg("total_pieces"))
            avg_last_30_days_stock = avg_stock_data["avg_total_pieces"] or 0.0

            product.current_stock = total_pieces
            product.avg_last_30_days_stock = avg_last_30_days_stock
            product.variation = (
                (
                    (total_pieces - avg_last_30_days_stock)
                    / avg_last_30_days_stock
                    * 100.0
                )
                if avg_last_30_days_stock > 0
                else 0.0
            )
            product.save()

            cache.set(
                f"product:{product.id}:current_stock",
                total_pieces,
                timeout=86400,
            )
            cache.set(
                f"product:{product.id}:avg_last_30_days_stock",
                avg_last_30_days_stock,
                timeout=86400,
            )
            cache.set(
                f"product:{product.id}:variation",
                product.variation,
                timeout=86400,
            )

        cache.delete_pattern(f"products:company:{company.id}:*")
        cache.delete_pattern(f"product_flow:company:{company.id}:*")
        cache.delete_pattern(f"category_composition:company:{company.id}:*")


@shared_task
def delete_old_product_snapshots():
    """6개월(180일) 이상된 ProductRecordSnapshot 레코드 삭제"""
    cutoff_date = timezone.now().date() - timedelta(days=180)
    deleted_count, _ = ProductRecordSnapshot.objects.filter(
        snapshot_date__lt=cutoff_date
    ).delete()
    logger.info(
        f"Deleted {deleted_count} ProductRecordSnapshot records older than {cutoff_date}"
    )

    companies = Company.objects.all()
    for company in companies:
        cache.delete_pattern(f"products:company:{company.id}:*")
        cache.delete_pattern(f"product_flow:company:{company.id}:*")
