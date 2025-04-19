from celery import shared_task
from products.models import Product, ProductImage
from products.services import upload_image_to_cloudflare
import os
import logging
from django.utils import timezone

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3)
def upload_image_to_cloudflare_task(
    self, temp_file_path, product_id, content_type=None
):
    logger.info(
        f"Starting image upload task for product {product_id} with file {temp_file_path}, content_type: {content_type}"
    )
    try:
        product = Product.objects.get(id=product_id)
        with open(temp_file_path, "rb") as image_file:
            image_url = upload_image_to_cloudflare(
                image_file, content_type=content_type
            )
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
                ProductImage.objects.create(
                    product=product,
                    image_url="https://imagedelivery.net/BxK0jiFZvOFWaDu7QtKNcQ/default/public",
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
