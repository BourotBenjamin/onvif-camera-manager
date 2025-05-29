import datetime

from onvif import ONVIFCamera
import cv2
import yaml

cameras_config_file = "./config/cameras.yaml"


class Stream:
    active: bool
    cap: cv2.VideoCapture

    def __init__(self, active: bool, cap: cv2.VideoCapture):
        self.active = active
        self.cap = cap


class Camera:
    id: int
    name: str
    ip: str
    port: str
    username: str
    password: str
    status: str
    rtsp_url: str
    last_seen: datetime
    connected: bool
    stream: Stream

    def __init__(self, index: int, d: dict):
        self.index = index
        self.name = d.get('name')
        self.ip = d.get('ip')
        self.port = d.get('port')
        self.username = d.get('username')
        self.password = d.get('password')
        self.status = 'offline'
        self.connected = False
        self.stream = None

    def to_dict(self) -> dict:
        return {"index": self.index, "name": self.name, "connected": self.connected, "status": self.status}


def load_cameras() -> list[Camera]:
    return [Camera(index, camera_data) for index, camera_data in enumerate(yaml.safe_load(open(cameras_config_file, 'r'))['cameras'])]


# Step 2: Retrieve RTSP URL from Camera
def get_rtsp_url(camera_index: int):
    ip = 'unknown'
    try:
        camera = load_cameras()[camera_index]
        ip = camera.ip

        # Initialize the ONVIF camera object
        onvif_cam = ONVIFCamera(camera.ip, camera.port, camera.username, camera.password,
                                './venv/lib/python3.4/site-packages/wsdl/')

        # Get the media service
        media_service = onvif_cam.create_media_service()
        profiles = media_service.GetProfiles()
        token = profiles[0].token

        # Get the RTSP stream URI
        stream_uri = media_service.GetStreamUri({
            'StreamSetup': {'Stream': 'RTP-Unicast', 'Transport': 'RTSP'},
            'ProfileToken': token
        })

        rtsp_url = stream_uri.Uri
        return rtsp_url.replace("rtsp://", f"rtsp://{camera.username}:{camera.password}@")
    except Exception as e:
        print(f"Failed to retrieve RTSP URL for Camera {ip} (Index {camera_index}): {e}")
        return None


# Step 3: Verify and Display Stream
def verify_stream(rtsp_url):
    """
    Verify the RTSP stream by opening it with OpenCV.
    """
    cap = cv2.VideoCapture(rtsp_url)
    if not cap.isOpened():
        print(f"Failed to open stream: {rtsp_url}")
        return False

    print(f"Stream opened successfully: {rtsp_url}")
    while True:
        ret, frame = cap.read()
        if not ret:
            print("Stream ended.")
            break
        cv2.imshow("Camera Stream", frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()
    return True


# Main Function
def main(username, password):
    print("Discovering cameras on the network...")
    cameras = load_cameras()

    if not cameras:
        print("No cameras found on the network.")
        return

    print(f"Found {len(cameras)} camera(s): {cameras}")

    for key, camera in cameras:
        print(f"Retrieving RTSP URL for camera at {camera.ip}:{camera.port}...")
        rtsp_url = get_rtsp_url(key)

        if rtsp_url:
            print(f"RTSP URL for {camera.ip}: {rtsp_url}")
            print("Verifying stream...")
            verify_stream(rtsp_url)
        else:
            print(f"Could not retrieve RTSP URL for camera at {camera.ip}.")


if __name__ == "__main__":
    print("Please use the web interface to discover and manage cameras.")
    print("Run 'python web_app.py' to start the web interface.")
