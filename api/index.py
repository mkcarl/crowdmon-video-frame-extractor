import base64
from io import BytesIO
from flask import Flask, request, make_response
import cv2
import boto3
import os 
from dotenv import load_dotenv
load_dotenv()

cloudflare_r2_url = os.getenv('CLOUDFLARE_R2_URL')
cloudflare_r2_key_id = os.getenv('CLOUDFLARE_R2_KEY_ID')
cloudflare_r2_secret = os.getenv('CLOUDFLARE_R2_SECRET')

app = Flask(__name__)

s3 = boto3.client('s3',
    endpoint_url=cloudflare_r2_url,
    aws_access_key_id=cloudflare_r2_key_id,
    aws_secret_access_key=cloudflare_r2_secret,
    region_name='weur'
    )


def upload(image_name: str, image):
    _, buffer = cv2.imencode(".jpg", image)
    img_data = BytesIO(buffer)
    key = f'extract/{image_name}'

    s3.put_object(Body=img_data, Bucket='crowdmon', Key=key)
    return f'https://images.crowdmon.mkcarl.com/{key}'

def uploadB64(key:str, image:str):
    image_data = base64.b64decode(image)
    key = f'v/{key}'
    s3.put_object(Body=image_data, Bucket='crowdmon', Key=key, ContentType='image/jpeg')
    return f'https://images.crowdmon.mkcarl.com/{key}'

@app.route('/')
def index():
    foobar = os.getenv('FOOBAR')
    return f'Crowdmon - Video Extractor {foobar}'

@app.route('/extract', methods=['POST'])
def extract(): 
    if request.method == 'POST': 
        data = request.get_json()
        video_url = data['url']
        timestamp = data['timestamp']
        
        cap = cv2.VideoCapture(video_url)
        cap.set(cv2.CAP_PROP_POS_MSEC, timestamp*1000)
        
        ret, frame = cap.read() 
        _, buffer = cv2.imencode('.jpg', frame)
        
        res = make_response(buffer.tobytes())
        res.mimetype = 'image/jpeg'
        
        return res

@app.route('/extract_and_upload', methods=['POST'])
def extract_and_upload():
    if request.method == 'POST': 
        data = request.get_json()
        video_url = data['url']
        timestamp = data['timestamp']
        image_name = data['image_name']
        
        cap = cv2.VideoCapture(video_url)
        cap.set(cv2.CAP_PROP_POS_MSEC, timestamp*1000)
        
        ret, frame = cap.read() 
        
        if not ret:
            return {'error': 'Could not extract frame from video'}, 500
        
        try: 
            image_url = upload(image_name, frame)
        except Exception as e:
            print(e)
            return {'error': 'Error uploading file'}, 500
        
        
        return {'data': image_url} 

@app.route('/upload', methods=['POST'])
def upload():
    if request.method != 'POST':
        return {'error': 'Method not allowed'}, 405
    
    data = request.get_json()
    key = data['key']
    image = data['image']
        
    if not key or not image:
        return {'error': 'Key and image are required'}, 400
    
    try: 
        image_url = uploadB64(key, image)
    except Exception as e:
        print(e)
        return {'error': 'Error uploading file'}, 500
    
    return {'data': image_url}

if __name__ == '__main__':
    app.run(debug=True)