
from celery import shared_task
import requests
from django.core.files.base import ContentFile
from applications.my_app.models import Image, Folder, User,CloudAccount

from applications.commons.utils import get_miniIO_client  # Assuming you have a utility function to get MinIO client

def get_folder_diff_drive(existing_files, drive_files):
    # Map existing images by external_img_id
    existing_map = {img.external_img_id: img for img in existing_files}
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
    to_delete = [img for img in existing_files if img.external_img_id not in seen_drive_ids]

    return to_add, to_delete, to_rename

def get_folder_diff_minio(existing_files, minio_files):
    # Map existing images by external_img_id
    existing_map = {img.external_img_id: img for img in existing_files}
    seen_minio_ids = set()
    to_add = []
    to_delete = []
    
    for minio_file in minio_files:
        file_key = minio_file['Key']
        file_name = file_key.split('/')[-1]
        seen_minio_ids.add(file_key)

        if file_key not in existing_map:
            # New file to add
            to_add.append({'Key': file_key, 'name': file_name})

    # Images in DB but not in MinIO = to delete
    to_delete = [img for img in existing_files if img.external_img_id not in seen_minio_ids]

    return to_add, to_delete


@shared_task
def gg_drive_sync_folder_task (user_id,  drive_folder_id, parent_folder_id, access_token):
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
            external_folder_id=drive_folder_id,
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
        to_add, to_delete, to_rename = get_folder_diff_drive(existing_images, files)
        
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
                    external_img_id=file_id
                )
                img_model.image.save(image_name, img_content)
                img_model.save()
                
            except Exception as e:
                print(f"Failed to download or save file {file['name']}: {str(e)}")
                continue

        for img in to_delete:
            try:
                print(f"Deleting image {img.image_name} with drive ID {img.external_img_id}")
                img.image.delete(save=False)  # delete the file
                img.delete()  # delete the DB entry
            except Exception as e:
                print(f"Failed to delete image {img.image_name}: {str(e)}")
                continue

        return {"message": f"Successfully synced files from folder {folder_name}"}
    
    except Exception as e:
        return {"error": str(e)}

@shared_task
def minIO_sync_folder_task(user_id , parent_folder_id, folder_key, bucket_name = 'actiup-internship'):
    try:
        user = User.objects.get(id=user_id)
        parent_folder = Folder.objects.filter(owner=user, id=parent_folder_id).first()
        
        folder_name = folder_key.rstrip('/').split('/')[-1]
        folder, created = Folder.objects.get_or_create(
            external_folder_id=folder_key,
            owner=user,
            parent =parent_folder ,
            defaults={'name': folder_name},
        )
        if created:
            print(f"Created new minIO_folder: {folder.name} for user: {user.username}")
        else:
            print(f"Using existing minIO_folder: {folder.name} for user: {user.username}")
        
        minio_client = get_miniIO_client()  
            
        response = minio_client.list_objects_v2(
            Bucket=bucket_name,
            Prefix=folder_key
        )
        
        existing_images = Image.objects.filter(folder=folder, user=user)
        minio_files = [{'Key': obj['Key']} for obj in response.get('Contents', [])]
        
        
        to_add, to_delete = get_folder_diff_minio(existing_images,minio_files)
        
        for obj in to_add:
            # Tạo presigned URL
            presigned_url = minio_client.generate_presigned_url(
                'get_object',
                Params={'Bucket': bucket_name, 'Key': obj['Key']},
                ExpiresIn=86400  # 24 hours
            )
            print (f"Presigned URL for {obj['Key']}: {presigned_url}")
            # Download the file
            file_response = requests.get(presigned_url)
            if file_response.status_code != 200:
                print(f"Failed to download {obj['Key']} from MinIO")
                continue
            # Save the file to Django model
            file_name = obj['name']
            img_content = ContentFile(file_response.content)
            img_model = Image(
                user=user,
                image_name=file_name,
                folder=folder,
                external_img_id=obj['Key'] 
            )    
            img_model.image.save(obj['Key'], img_content)
            img_model.save()
        
        for img in to_delete:
            try:
                print(f"Deleting image {img.image_name} with external ID {img.external_img_id}")
                img.image.delete(save=False)  # delete the file
                img.delete()  # delete the DB entry
            except Exception as e:
                print(f"Failed to delete image {img.image_name}: {str(e)}")
                continue
                
        return {"message": f"Folder {folder_key} synced to MinIO successfully"}

    except Exception as e:
        return {"error": f"Exception occurred: {str(e)}"}

    

@shared_task
def gg_drive_sync_task(user_id, drive_email, img_name, img_id, img_folder_id):
    try:
        user = User.objects.get(id=user_id)
        folder = Folder.objects.filter(id=img_folder_id).first()
        drive_account = CloudAccount.objects.filter(user=user, drive_email=drive_email).first()

        if not drive_account:
            return {"error": "Drive account not found"}

        access_token = drive_account.credentials.get("access_token")
        # print ("-------------------- access_token--------------------")
        # print (access_token)

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
            external_img_id=img_id
        )
        img_model.image.save(img_name, img_content)
        img_model.save()

        return {"message": "Image saved successfully", "image_id": img_model.id}

    except Exception as e:
        return {"error": f"Exception occurred: {str(e)}"}
    


@shared_task
def minIO_sync_task(user_id,img_folder_id, img_key , bucket_name = 'actiup-internship'):
    try:
        user = User.objects.get(id=user_id)
        folder = Folder.objects.filter(id=img_folder_id).first()
        # Assuming you have a function to get the MinIO client
        minio_client = get_miniIO_client()  
        # Upload image to MinIO
        presigned_url = minio_client.generate_presigned_url(
            'get_object',
            Params={'Bucket': bucket_name, 'Key': img_key},
            ExpiresIn=86400  # 24 hours
        )
        
        response = requests.get(presigned_url)
        if response.status_code != 200:
            return {"error": "Failed to download image from MinIO"}
        
        image_name = img_key.split('/')[-1]  # Extract the image name from the key
        
        img_content = ContentFile(response.content)
        img_model = Image(
            user=user,
            image_name=image_name,
            folder=folder,
            external_img_id=img_key
        )
        img_model.image.save(image_name, img_content)
        img_model.save()

        return {"message": "Image synced to MinIO successfully"}

    except Exception as e:
        return {"error": f"Exception occurred: {str(e)}"}