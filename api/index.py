from flask import Flask, request
from yt_dlp import YoutubeDL
import cv2
import base64

app = Flask(__name__)

@app.route('/')
def home():
    return 'Hello, World!'

@app.route('/test', methods=['POST'])
def test(): 
    if request.method == 'POST': 
        data = request.get_json()
        video_url = data['url']
        timestamp = data['timestamp']
        
        videoInfo = getVideoInfo(video_url)
        cap = cv2.VideoCapture(videoInfo['url'])
        cap.set(cv2.CAP_PROP_POS_MSEC, timestamp*1000)
        
        ret, frame = cap.read() 
        _, buffer = cv2.imencode('.jpg', frame)
        img_str = base64.b64encode(buffer).decode()
        
        return f"data:image/jpeg;base64,{img_str}"
        # return f'POST {info_dict}'
        
def getVideoInfo(video_url, format='134'):
    ydl_opts={}
    ydl=YoutubeDL(ydl_opts)
    info_dict=ydl.extract_info(video_url, download=False)
    formats = info_dict.get('formats', [])
    vid = filter(lambda x: x.get('format_id') == '134', formats)
    return next(vid, None)



if __name__ == '__main__':
    app.run(debug=True)