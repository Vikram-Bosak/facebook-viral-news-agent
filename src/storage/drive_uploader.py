import os
import logging
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
import json

SCOPES = ['https://www.googleapis.com/auth/drive.file']

def get_drive_service():
    # Check if token json string is provided via environment variable (GitHub Secrets)
    token_json_str = os.getenv('GOOGLE_TOKEN_JSON')
    
    if token_json_str:
        try:
            token_data = json.loads(token_json_str)
            creds = Credentials.from_authorized_user_info(token_data, SCOPES)
            service = build('drive', 'v3', credentials=creds)
            return service
        except Exception as e:
            logging.error(f"Error creating Drive service from env: {e}")
            return None
            
    # Fallback to local token.json file
    token_path = os.getenv('GOOGLE_TOKEN_JSON_PATH', 'token.json')
    if not token_path or not os.path.exists(token_path):
        logging.warning("Google Drive token.json not found or invalid.")
        return None
        
    try:
        creds = Credentials.from_authorized_user_file(token_path, SCOPES)
        service = build('drive', 'v3', credentials=creds)
        return service
    except Exception as e:
        logging.error(f"Error creating Drive service: {e}")
        return None

def get_or_create_subfolder(service, parent_id, folder_name):
    query = f"'{parent_id}' in parents and name='{folder_name}' and mimeType='application/vnd.google-apps.folder' and trashed=false"
    results = service.files().list(q=query, spaces='drive', fields='files(id, name)').execute()
    items = results.get('files', [])
    
    if not items:
        file_metadata = {
            'name': folder_name,
            'parents': [parent_id],
            'mimeType': 'application/vnd.google-apps.folder'
        }
        folder = service.files().create(body=file_metadata, fields='id').execute()
        return folder.get('id')
    else:
        return items[0].get('id')

def upload_image_to_drive(file_path, base_folder_id):
    """
    Uploads a file to Generated-Images folder inside the base Google Drive folder.
    """
    service = get_drive_service()
    if not service:
        logging.warning("Skipping Drive upload since service is not initialized.")
        return None
        
    try:
        generated_folder_id = get_or_create_subfolder(service, base_folder_id, "Generated-Images")
        
        file_metadata = {
            'name': os.path.basename(file_path),
            'parents': [generated_folder_id]
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
