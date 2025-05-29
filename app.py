from onvif import ONVIFCamera
import cv2
import yaml

def get_cameras_from_conf():
    # Read YAML file
    with open(".env.yaml", 'r') as env:
        return yaml.safe_load(env)['cameras']

# Step 2: Retrieve RTSP URL from Camera
def get_rtsp_url(camera_ip, camera_port, username, password):
    """
    Retrieve the RTSP URL from an ONVIF-compatible camera.
    """
    try:
        # Initialize the ONVIF camera object
        onvif_cam = ONVIFCamera(camera_ip, camera_port, username, password, './venv/lib/python3.4/site-packages/wsdl/')

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
        return rtsp_url.replace("rtsp://", f"rtsp://{username}:{password}@")
    except Exception as e:
        print(f"Failed to retrieve RTSP URL for {camera_ip}: {e}")
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
    cameras = get_cameras_from_conf()

    if not cameras:
        print("No cameras found on the network.")
        return

    print(f"Found {len(cameras)} camera(s): {cameras}")

    for camera in cameras:
        print(f"Retrieving RTSP URL for camera at {camera['ip']}:{camera['port']}...")
        rtsp_url = get_rtsp_url(camera['ip'], camera.port, username, password)

        if rtsp_url:
            print(f"RTSP URL for {camera['ip']}: {rtsp_url}")
            print("Verifying stream...")
            verify_stream(rtsp_url)
        else:
            print(f"Could not retrieve RTSP URL for camera at {camera['ip']}.")


if __name__ == "__main__":
    print("Please use the web interface to discover and manage cameras.")
    print("Run 'python web_app.py' to start the web interface.")
