
from celery import shared_task
import requests
from django.core.files.base import ContentFile
from applications.my_app.models import Image, Folder, User,CloudAccount

@shared_task
def sync_drive_folder_task (user_id,  drive_folder_id, access_token):
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

        parent_folder = Folder.objects.filter(owner=user, drive_folder_id=drive_folder_id).first()

        #Get or create Folder
        folder, created = Folder.objects.get_or_create(
            drive_folder_id=drive_folder_id,
            owner=user,
            parent =parent_folder ,
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


@shared_task
def sync_image_task(user_id, drive_email, img_name, img_id, img_folder_id):
    try:
        user = User.objects.get(id=user_id)
        folder = Folder.objects.filter(id=img_folder_id).first()
        drive_account = CloudAccount.objects.filter(user=user, drive_email=drive_email).first()

        if not drive_account:
            return {"error": "Drive account not found"}

        access_token = drive_account.credentials.get("access_token")

        drive_url = f"https://www.googleapis.com/drive/v3/files/{img_id}?alt=media"
        headers = {"Authorization": f"Bearer {access_token}"}
        response = requests.get(drive_url, headers=headers)

        if response.status_code != 200:
            return {"error": "Failed to download image from Google Drive"}

        img_content = ContentFile(response.content)
        img_model = Image(
            user=user,
            image_name=img_name,
            folder=folder
        )
        img_model.image.save(img_name, img_content)
        img_model.save()

        return {"message": "Image saved successfully", "image_id": img_model.id}

    except Exception as e:
        return {"error": f"Exception occurred: {str(e)}"}