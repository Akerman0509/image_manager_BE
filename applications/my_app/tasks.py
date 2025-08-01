
from celery import shared_task
import requests
from django.core.files.base import ContentFile
from applications.my_app.models import Image, Folder, User,CloudAccount

def get_folder_diff(existing_files, drive_files):
    # Map existing images by drive_image_id
    existing_map = {img.drive_image_id: img for img in existing_files}
    seen_drive_ids = set()

    to_add = []
    to_delete = []
    to_rename = []

    for drive_file in drive_files:
        file_id = drive_file['id']
        file_name = drive_file['name']
        seen_drive_ids.add(file_id)

        if file_id not in existing_map:
            # New file to add
            to_add.append(drive_file)
        else:
            # File exists, check if name has changed
            existing_img = existing_map[file_id]
            if existing_img.image_name != file_name:
                to_rename.append((existing_img, file_name))

    # Images in DB but not in Drive = to delete
    to_delete = [img for img in existing_files if img.drive_image_id not in seen_drive_ids]

    return to_add, to_delete, to_rename


@shared_task
def sync_drive_folder_task (user_id,  drive_folder_id, parent_folder_id, access_token):
    print (f"Starting sync for user_id: {user_id} with drive folder: {drive_folder_id}")
    print (f"Access token: {access_token}")
    print (f"Parent folder ID: {parent_folder_id}")
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
        parent_folder = Folder.objects.filter(owner=user, id=parent_folder_id).first()
        #Get or create Folder
        folder, created = Folder.objects.get_or_create(
            drive_folder_id=drive_folder_id,
            owner=user,
            parent =parent_folder ,
            defaults={'name': folder_name},
        )
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

        # get list of drive_id of existing images in this folder
        existing_images = Image.objects.filter(folder=folder, user=user)
        to_add, to_delete, to_rename = get_folder_diff(existing_images, files)
        
        for img_obj, new_name in to_rename:
            img_obj.image_name = new_name
            img_obj.save()

        print (f"to_add: {to_add}")
        print (f"to_delete: {to_delete}")
        print (f"to_rename: {to_rename}")
        for file in to_add:
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
                    drive_image_id=file_id
                )
                img_model.image.save(image_name, img_content)
                img_model.save()
                
            except Exception as e:
                print(f"Failed to download or save file {file['name']}: {str(e)}")
                continue

        for img in to_delete:
            try:
                print(f"Deleting image {img.image_name} with drive ID {img.drive_image_id}")
                img.image.delete(save=False)  # delete the file
                img.delete()  # delete the DB entry
            except Exception as e:
                print(f"Failed to delete image {img.image_name}: {str(e)}")
                continue

        return {"message": f"Successfully synced files from folder {folder_name}"}
    
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

        print (f"image_id {img_id} downloaded successfully from Google Drive--------------------------------------------------------------------------")
        
        img_content = ContentFile(response.content)
        img_model = Image(
            user=user,
            image_name=img_name,
            folder=folder,
            drive_image_id=img_id
        )
        img_model.image.save(img_name, img_content)
        img_model.save()

        return {"message": "Image saved successfully", "image_id": img_model.id}

    except Exception as e:
        return {"error": f"Exception occurred: {str(e)}"}