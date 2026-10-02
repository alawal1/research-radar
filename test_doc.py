from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/documents",
    "https://www.googleapis.com/auth/drive",
]

creds = Credentials.from_service_account_file("service_account.json", scopes=SCOPES)
print("Service account email:", creds.service_account_email)

# Try to list the service account's own Drive files.
drive = build("drive", "v3", credentials=creds)
try:
    result = drive.files().list(pageSize=5).execute()
    print("Drive access OK. Files:", result.get("files", []))
except Exception as e:
    print("Drive access failed:", e)

# Try to create a Doc.
docs = build("docs", "v1", credentials=creds)
try:
    doc = docs.documents().create(body={"title": "Test Doc"}).execute()
    print("Doc created:", doc["documentId"])
except Exception as e:
    print("Doc creation failed:", e)