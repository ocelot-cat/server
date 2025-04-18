import requests
from django.conf import settings
from rest_framework.exceptions import APIException


def upload_image_to_cloudflare(image_file):
    url = settings.CLOUDFLARE_IMAGES_URL
    headers = {
        "Authorization": f"Bearer {settings.CLOUDFLARE_API_TOKEN}",
    }
    files = {"file": (image_file.name, image_file, image_file.content_type)}
    response = requests.post(url, headers=headers, files=files)

    if response.status_code != 200:
        raise APIException(
            f"Cloudflare upload failed: {response.json().get('errors', 'Unknown error')}"
        )

    result = response.json()
    if not result.get("success"):
        raise APIException("Cloudflare upload failed")

    image_id = result["result"]["id"]
    account_hash = settings.CLOUDFLARE_ACCOUNT_HASH
    base_url = f"https://imagedelivery.net/{account_hash}/{image_id}"
    return base_url
