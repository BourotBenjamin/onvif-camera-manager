from flask import Flask, render_template, jsonify, request, Response, redirect, url_for, make_response
from app import get_rtsp_url, load_cameras, Camera, Stream
import cv2
import threading
import secrets

from user import user_login, load_users, create_user, User, authenticate

app = Flask(__name__, static_folder='static', template_folder='templates')
app.secret_key = secrets.token_hex(16)  # Generate a random secret key for sessions

stream_lock = threading.Lock()  # Add thread lock for stream operations
cameras: list[Camera] = []


def remove_all_cameras_and_stop_streams():
    for camera in cameras:
        if camera.stream:
            if camera.stream.active:
                try:
                    camera.stream.cap.release()
                except:
                    pass
            camera.stream = None
        camera.connected = False
        del camera


def load_cameras_and_start_streams():
    remove_all_cameras_and_stop_streams()
    global cameras
    cameras = load_cameras()
    for camera in cameras:
        rtsp_url = get_rtsp_url(camera.index)
        if rtsp_url:
            camera.rtsp_url = rtsp_url
            camera.connected = True
            camera.status = 'connected'
            camera.error_message = None
        else:
            camera.status = 'error'
            camera.connected = False
            camera.error_message = "Failed to get RTSP URL from camera"


def get_camera_stream(camera_index: int):
    if len(cameras) <= camera_index:
        return
    camera = cameras[camera_index]
    rtsp_url = camera.rtsp_url
    if not rtsp_url:
        return

    with stream_lock:
        if not camera.stream or not camera.stream.active:
            cap = cv2.VideoCapture(rtsp_url)
            if not cap.isOpened():
                camera.connected = False
                camera.status = 'error'
                camera.error_message = 'Failed to open stream'
                return

            camera.stream = Stream(True, cap)

    try:
        while True:
            with stream_lock:
                if not camera.stream or not camera.stream.active:
                    break
                cap = camera.stream.cap
                ret, frame = cap.read()
                if not ret:
                    break

                # Convert frame to JPEG
                ret, buffer = cv2.imencode('.jpg', frame)
                if not ret:
                    break
                frame = buffer.tobytes()

            # Return frame in multipart response
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
    finally:
        with stream_lock:
            if camera.stream and camera.stream.active:
                try:
                    camera.stream.cap.release()
                except:
                    pass  # Ignore errors during release
                camera.stream = None
            camera.connected = False
            camera.status = 'discovered'


@app.route('/')
def index():
    user = authenticate(request.cookies.get('user'))
    if not user:
        return redirect(url_for('login'))
    return render_template('index.html', cameras=cameras, user=user)


@app.route('/camera/<int:camera_index>')
def show_camera(camera_index: int):
    user = authenticate(request.cookies.get('user'))
    if not user:
        return redirect(url_for('login'))
    if len(cameras) <= camera_index:
        return redirect(url_for('index'))
    return render_template('camera.html', camera=cameras[camera_index], user=user)


@app.route('/login', methods=['GET', 'POST'])
def login():
    if len(load_users()) == 0:
        return redirect(url_for('register'))
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = user_login(username, password)
        if user:
            resp = make_response(redirect(url_for('index')))
            resp.set_cookie('user', user.get_auth_token())
            return resp

    return render_template('login.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        role = request.form.get('role')
        user_cookie = request.cookies.get('user')
        user = create_user(username, password, role, user_cookie)
        if user:
            resp = make_response(redirect(url_for('index')))
            resp.set_cookie('user', user.get_auth_token())
            return resp

    return render_template('register.html')


@app.route('/logout')
def logout():
    remove_all_cameras_and_stop_streams()
    resp = make_response(redirect(url_for('login')))
    resp.set_cookie('user', '')
    return resp

@app.route('/api/discover', methods=['POST'])
def api_discover():
    global cameras
    cameras = load_cameras()
    return jsonify({"status": "success", "cameras": cameras})


@app.route('/api/cameras/list')
def api_cameras():
    """API endpoint to get camera information"""
    return jsonify(cameras)


@app.route('/api/cameras/<int:camera_index>/stream')
def api_stream(camera_index: int):
    """API endpoint to stream camera feed"""
    if len(cameras) <= camera_index:
        return jsonify({
            "status": "error",
            "message": "Camera not found"
        }), 404

    if not cameras[camera_index].connected:
        return jsonify({
            "status": "error",
            "message": "Camera not connected"
        }), 400

    try:
        return Response(
            get_camera_stream(camera_index),
            mimetype='multipart/x-mixed-replace; boundary=frame'
        )
    except Exception as e:
        print(f"Stream error for {camera_index}: {str(e)}")
        return jsonify({
            "status": "error",
            "message": f"Stream error: {str(e)}"
        }), 500


@app.route('/api/cameras/<int:camera_index>/stop', methods=['POST'])
def stop_stream(camera_index: int):
    """API endpoint to stop a camera stream"""
    try:
        with stream_lock:
            # Check if camera exists
            if len(cameras) <= camera_index:
                return jsonify({
                    "status": "error",
                    "message": "Camera not found"
                }), 404
            camera = cameras[camera_index]
            # Stop the stream if active
            if camera.stream and camera.stream.active:
                try:
                    camera.stream.active = False
                    camera.stream.cap.release()
                except Exception as e:
                    print(f"Error releasing stream for {camera.ip}: {str(e)}")
                finally:
                    camera.stream = None

            # Update camera status regardless of whether stream was active
            camera.connected = False
            camera.status = 'discovered'
            camera.error_message = None

            return jsonify({
                "status": "success",
                "message": "Stream stopped successfully"
            })
    except Exception as e:
        print(f"Error stopping stream for {camera_index}: {str(e)}")
        return jsonify({
            "status": "error",
            "message": f"Failed to stop stream: {str(e)}"
        }), 500


@app.route('/api/cameras/<int:camera_index>/restart')
def camera_restart(camera_index: int):
    if len(cameras) <= camera_index:
        return jsonify({
            "status": "error",
            "message": "Camera not found"
        }), 404
    cameras[camera_index].connected = True
    return jsonify({
        "status": "success",
        "message": "Stream stopped successfully"
    })

if __name__ == '__main__':
    load_cameras_and_start_streams()

    # Run the Flask app
    app.run(host='0.0.0.0', port=5000, debug=True, use_reloader=False)
