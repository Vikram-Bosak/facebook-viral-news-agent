import os
import logging
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

SCOPES = ['https://www.googleapis.com/auth/drive.file']

def get_drive_service():
    creds_path = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
    if not creds_path or not os.path.exists(creds_path):
        logging.warning("Google Drive credentials not found or invalid.")
        return None
        
    try:
        creds = service_account.Credentials.from_service_account_file(
            creds_path, scopes=SCOPES)
        service = build('drive', 'v3', credentials=creds)
        return service
    except Exception as e:
        logging.error(f"Error creating Drive service: {e}")
        return None

def upload_image_to_drive(file_path, folder_id):
    """
    Uploads a file to a specific Google Drive folder.
    """
    service = get_drive_service()
    if not service:
        logging.warning("Skipping Drive upload since service is not initialized.")
        return None
        
    try:
        file_metadata = {
            'name': os.path.basename(file_path),
            'parents': [folder_id]
        }
        media = MediaFileUpload(file_path, mimetype='image/jpeg')
        file = service.files().create(body=file_metadata,
                                      media_body=media,
                                      fields='id, webViewLink').execute()
        
        file_id = file.get('id')
        
        # Make the file public
        permission = {
            'type': 'anyone',
            'role': 'reader'
        }
        service.permissions().create(
            fileId=file_id,
            body=permission,
            fields='id'
        ).execute()
        
        logging.info(f"Successfully uploaded {file_path} to Drive and made public.")
        return file.get('webViewLink')
    except Exception as e:
        logging.error(f"Failed to upload to Drive: {e}")
        return None
