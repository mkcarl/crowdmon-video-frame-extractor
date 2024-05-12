from flask import Flask, request, make_response
import cv2

app = Flask(__name__)

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

if __name__ == '__main__':
    app.run(debug=True)