import sys
import math
import time
from camera_reader import CameraReader
from pose_estimator import PoseEstimator, PoseLandmark
from game_controller import GameController
from data_manager import DataManager

# ========

PARTICIPANT_ID           = None
PARTICIPANT_TRAINED_SIDE = PoseLandmark.RIGHT_WRIST

# ========

GAME_RUNNING             = True
GAME_FPS                 = 60
GAME_WIDTH               = 1920 #px
GAME_HEIGHT              = 1080 #px
game_controller          = GameController(GAME_FPS, GAME_WIDTH, GAME_HEIGHT)

# ========

CAMERA_TYPE              = CameraReader.CAMERA_EXTERNAL
CAMERA_WIDTH             = 640 #px
CAMERA_HEIGHT            = 480 #px
camera_reader            = CameraReader(CAMERA_TYPE, CAMERA_WIDTH, CAMERA_HEIGHT)

# ========

POSE_MODEL_COMPLEXITY    = PoseEstimator.MODEL_COMPLEXITY_BALANCED
POSE_MIN_VISIBILITY      = 0.2
POSE_EXCLUDED_LANDMARKS  = [PoseLandmark.RIGHT_HAND, PoseLandmark.LEFT_HAND]
pose_estimator           = PoseEstimator(POSE_MODEL_COMPLEXITY, POSE_MIN_VISIBILITY)
pose_dummy               = PoseLandmark.exclude_landmarks(POSE_EXCLUDED_LANDMARKS)

# ========

DATA_FOLDER              = "./experiments/"
data_manager             = DataManager(DATA_FOLDER)

# ========

CANVAS_COLOR             = GameController.COLOR_BLACK

# ========

LANDMARK_COLOR           = GameController.COLOR_BLUE
LANDMARK_RADIUS          = 8 #px

LANDMARK_CONNECT_COLOR   = GameController.COLOR_WHITE
LANDMARK_CONNECT_WIDTH   = 2 #px

# ========

def main(parameters):
    # Get the paramaters
    check_parameters(parameters)
    set_parameters(parameters)

    # Set the background and create the landmarks
    game_controller.set_background_color(CANVAS_COLOR)
    create_landmarks()    

    while GAME_RUNNING:
        
        # Update the game state and events
        update_states()

        # Read the camera
        image = get_image()
        if image is None: continue

        # Estimate the pose
        landmarks = get_landmarks(image)
        if landmarks is None: continue
        
        # Convert the coordinates to px
        landmarks_as_px = get_landmarks_as_px(landmarks)

        # Update the landmarks
        update_landmarks(landmarks_as_px)

        # Draw the canvas and regulate the FPS
        game_controller.refresh_screen()
        game_controller.regulate_fps()


def check_parameters(parameters):
    # Check the parameters length
    if len(parameters) != 2:
        raise RuntimeError("Exactly two parameters are needed (participant id, participant trained side)")
    
    # Check the participant trained side parameter
    if parameters[1] != "right" and parameters[1] != "left":
        raise RuntimeError("The participant trained side parameter must be right or left")


def set_parameters(parameters):
    global PARTICIPANT_ID, PARTICIPANT_TRAINED_SIDE
    PARTICIPANT_ID = parameters[0]
    PARTICIPANT_TRAINED_SIDE = PoseLandmark.RIGHT_WRIST if parameters[1] == "right" else PoseLandmark.LEFT_WRIST


def create_landmarks():
    for landmark_id in PoseLandmark.get_landmarks():
        game_controller.create_object_circle(landmark_id, 0, 0, LANDMARK_COLOR, LANDMARK_RADIUS)


def update_states():
    global GAME_RUNNING
    game_controller.refresh_states()
    GAME_RUNNING = game_controller.get_running_state()


def get_image():
    # Read the camera
    result = camera_reader.read()
    if not result: return None

    # Get the image
    result = camera_reader.get_image()
    if result is None: return None
    image = result[0]
    
    return image


def get_landmarks(image):
    # Estimate the pose
    pose_estimator.set_image(image)
    result = pose_estimator.estimate()
    if not result: return None

    # Get the landmark coordinates
    landmarks = pose_estimator.get_landmarks()

    return landmarks


def get_landmarks_as_px(landmarks):
    # Convert the landmarks to px
    result = {}
    for landmark in landmarks:
        output = landmarks.get(landmark)
        result[landmark] = [0, 0]
        result[landmark][0] = int(output[0] * GAME_WIDTH)  # To pixels
        result[landmark][1] = int(output[1] * GAME_HEIGHT) # To pixels

    return result


def update_landmarks(landmarks_as_px):
    # Update the landmarks
    for landmark_id in PoseLandmark.get_landmarks():
        px_landmark = landmarks_as_px.get(landmark_id)
        if px_landmark is None: continue
        game_controller.update_object_circle(landmark_id, px_landmark[0], px_landmark[1], None, None)
    
    # Create the landmark connections
    for connection in PoseLandmark.get_connections():
        landmark_id1 = connection[0]
        landmark_id2 = connection[1]
        px_landmark1 = landmarks_as_px.get(landmark_id1)
        px_landmark2 = landmarks_as_px.get(landmark_id2)
        if px_landmark1 is None or px_landmark2 is None: continue
        game_controller.create_object_line(None, px_landmark1[0], px_landmark1[1], px_landmark2[0], px_landmark2[1], LANDMARK_CONNECT_COLOR, LANDMARK_CONNECT_WIDTH)


if __name__ == '__main__':
    try:
        parameters = sys.argv[1:] # The first parameter is the file name
        main(parameters)
    except KeyboardInterrupt:
        GAME_RUNNING = False
    finally:
        camera_reader.close()
        pose_estimator.close()
        game_controller.close()
        data_manager.close()