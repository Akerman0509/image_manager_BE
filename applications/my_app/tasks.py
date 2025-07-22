
from celery import shared_task
import requests
from django.core.files.base import ContentFile
from applications.my_app.models import Image, Folder, User

@shared_task
def sync_drive_folder_task (user_id, drive_folder_id, access_token):
    print (f"Starting sync for user_id: {user_id} with drive folder: {drive_folder_id}")
    print (f"Access token: {access_token}")

    try:
        
        user = User.objects.get(id=user_id)
        # get folder name on drive
        # Fetch folder metadata
        metadata_url = f"https://www.googleapis.com/drive/v3/files/{drive_folder_id}"
        metadata_params = {
            'fields': 'id, name'
        }
        headers = {
            'Authorization': f'Bearer {access_token}'
        }
        meta_response = requests.get(metadata_url, headers=headers, params=metadata_params)
        meta_response.raise_for_status()
        folder_metadata = meta_response.json()

        folder_name = folder_metadata.get('name', f"Drive-folder-{drive_folder_id}")

        

        #Get or create Folder
        folder, created = Folder.objects.get_or_create(
            drive_folder_id=drive_folder_id,
            owner=user,
            defaults={'name': folder_name},
        )
        # Clear existing images in this folder
        Image.objects.filter(folder__name=folder_name).delete()
        
        if created:
            print(f"Created new drive_folder: {folder.name} for user: {user.username}")
        else:
            print(f"Using existing drive_folder: {folder.name} for user: {user.username}")
        # Step 1: List files in folder
        url = 'https://www.googleapis.com/drive/v3/files'
        params = {
            'q': f"'{drive_folder_id}' in parents and trashed = false",
            'fields': 'files(id, name, mimeType)',
        }
        headers = {
            'Authorization': f'Bearer {access_token}'
        }

        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        files = response.json().get('files', [])

        # Step 2: Download each file
        success_count = 0
        for file in files:
            try:
                file_id = file['id']
                image_name = file['name']

                download_url = f'https://www.googleapis.com/drive/v3/files/{file_id}?alt=media'
                file_response = requests.get(download_url, headers=headers)
                file_response.raise_for_status()

                # Save image to Django model
                img_content = ContentFile(file_response.content)
                img_model = Image(
                    user=user,
                    image_name=image_name,
                    folder=folder,
                )
                img_model.image.save(image_name, img_content)
                img_model.save()
                success_count += 1
                
            except Exception as e:
                print(f"Failed to download or save file {file['name']}: {str(e)}")
                continue

        return {"message": f"Successfully synced {success_count} / {len(files)} files from folder {folder_name}"}
    
    except Exception as e:
        return {"error": str(e)}
