
import functions_framework
import ffmpeg 
import boto3
import os 
import subprocess
import base64

cloudflare_r2_url = os.getenv('CLOUDFLARE_R2_URL')
cloudflare_r2_key_id = os.getenv('CLOUDFLARE_R2_KEY_ID')
cloudflare_r2_secret = os.getenv('CLOUDFLARE_R2_SECRET')

s3 = boto3.client('s3',
    endpoint_url=cloudflare_r2_url,
    aws_access_key_id=cloudflare_r2_key_id,
    aws_secret_access_key=cloudflare_r2_secret,
    region_name='weur'
    )

bucket_prefix = 'ffmpeg_extract'
image_url_prefix = f'https://images.crowdmon.mkcarl.com/{bucket_prefix}'

def upload(image_name: str, image_path:str) -> bool:
  key = f'{bucket_prefix}/{image_name}'
  
  try: 
    response = s3.upload_file(image_path, 'crowdmon', key)
  except Exception as e: 
    print("[Upload error]", e)
    return False
  return True

def extract_using_ffmpeg_subprocess(video_url: str, timestamp: str, image_name: str) -> bool:
  print(video_url, timestamp, image_name)
  try:
    print('start extract')
    command = ['ffmpeg', '-ss', str(timestamp), '-i', video_url, '-vframes', '1', image_name , '-y'] 
    subprocess.run(command)
    print('end extract')
    return True
  except Exception as e:
    print("[Extraction error]", e)
    return False
  
# @functions_framework.http
def extract_and_upload(request):
    if request.method != 'POST':
        return ('Method not allowed', 405)
    
    data = request.get_json()
    video_url = data['url'] if 'url' in data else None
    timestamp = data['timestamp'] if 'timestamp' in data else None
    image_name = data['image_name'] if 'image_name' in data else None
    
    if not video_url or not timestamp or not image_name: 
      return {'error':'Invalid argument in url or time or image_name'}, 400
   
    subprocess_res = extract_using_ffmpeg_subprocess(video_url, timestamp, image_name)
    if not subprocess_res: 
      return {'error':'FFMPEG error'}, 500
  
    res = upload(image_name, image_name)
    
    if not res: 
      return {'error':'Upload error'}, 500
    
    return {"msg":'ok', "data": f'{image_url_prefix}/{image_name}'}, 200
  
@functions_framework.http
def extract(request):
  if request.method != 'POST': 
    return ('Method not allowed', 405)
  
  data = request.get_json()
  video_url = data['url'] if 'url' in data else None
  timestamp = data['timestamp'] if 'timestamp' in data else None
  image_name = f'{timestamp}.jpg'
  
  if not video_url or not timestamp:
    return {'error':'Invalid argument in url or time'}, 400
  
  subprocess_res = extract_using_ffmpeg_subprocess(video_url, timestamp, image_name)
  
  if not subprocess_res:
    return {'error':'FFMPEG error'}, 500
  
  data = None
  
  try:
    with open(image_name, "rb") as image_file:
      image_data = image_file.read()
      
    data = base64.b64encode(image_data).decode("utf-8")
    
  except FileNotFoundError:
    print(f"Error: File '{image_name}' not found.")
    return {'error':'Internal server error'}, 500
  
  return {"msg":'ok', "data": data}, 200