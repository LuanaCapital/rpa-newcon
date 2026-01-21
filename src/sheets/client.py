from __future__ import annotations
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build

SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]

def get_sheets_service(token_path: str = "./token.json"):
    creds = Credentials.from_service_account_file(token_path, scopes=SCOPES)
    # cache_discovery=False evita warnings/latência em alguns ambientes
    return build("sheets", "v4", credentials=creds, cache_discovery=False)
