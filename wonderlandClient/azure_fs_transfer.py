from azure.storage.file import FileService, ContentSettings
import time

file_service = FileService(account_name='mylake', account_key='nTYA+KhHEIuy2DVyG8uGuNev3qKGJ8Qm975hCkMgm+hGc7AW17RhnygFTKSNho5Iu8s3zwYcqxgrmte0tROBog==')

def log(current, total):
    print(str(current * 100.0 / total) + '/100' )
    start_time = time.time()

start_time = time.time()
file_service.create_file_from_path(
    'myshare',
    None, # We want to create this blob in the root directory, so we specify None for the directory_name
    'file.iso',
    '/home/igor/file.iso', max_connections=8, progress_callback=log)
print(time.time()-start_time)