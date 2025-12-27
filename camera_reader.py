import cv2


class CameraReader:

    CAMERA_INTERNAL = 0
    CAMERA_EXTERNAL = 1

    _CAMERAS = [
        CAMERA_INTERNAL,
        CAMERA_EXTERNAL,
    ]
    
    def __init__(self, camera_type, camera_width, camera_height):
        self._camera = None
        self._image = None

        # Check the camera type
        if camera_type not in CameraReader._CAMERAS:
            raise RuntimeError("The camera type does not exist")
        
        # Set the camera
        if camera_type == CameraReader.CAMERA_INTERNAL:
            self._camera = cv2.VideoCapture(0, cv2.CAP_DSHOW) # Windows
        elif camera_type == CameraReader.CAMERA_EXTERNAL:
            self._camera = cv2.VideoCapture(1, cv2.CAP_DSHOW) # Windows

        # Set the camera dimensions
        self._camera.set(cv2.CAP_PROP_FRAME_WIDTH, camera_width)
        self._camera.set(cv2.CAP_PROP_FRAME_HEIGHT, camera_height)

        # Check the camera opening
        if not self._camera.isOpened():
            raise RuntimeError("The camera cannot be opened")

    def close(self):
        # Release the camera
        try: self._camera.release()
        except: pass

    def read(self):
        # Read the camera
        success, image = self._camera.read()
        if not success: return False
        
        # Flip the image horizontally
        image = cv2.flip(image, 1)

        # Convert from BGR to RGB
        image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

        # Set the image
        self._image = image
        return True
    
    def get_image(self):
        # Check the image
        if self._image is None: return None

        image = self._image        
        return [image, image.shape[1], image.shape[0]]