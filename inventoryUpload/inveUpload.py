import pandas as pd
import requests
from authentication.tokening import getHeaders



def request_signed_url(account_id: str, callback_url: str):
    resp = requests.post(
        f"https://api.deliverect.io/catalog/accounts/{account_id}/inventoryUploadUrl",
        headers={
            **getHeaders(),
            "Content-Type": "application/json",
        },
        json={"callbackUrl": callback_url},
        timeout=60,
    )
    resp.raise_for_status()
    data = resp.json()
    return data["signedUrl"], data.get("headers", {"Content-Type": "text/csv"}), data.get("fileId")

def upload_csv(csv_text: str, signed_url: str, upload_headers: dict):
    put = requests.put(
        signed_url,
        data=csv_text.encode("utf-8"),
        headers=upload_headers,
        timeout=300,
    )
    put.raise_for_status()
