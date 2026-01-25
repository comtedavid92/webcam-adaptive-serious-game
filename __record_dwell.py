import math
import time
from camera_reader import CameraReader
from pose_estimator import PoseEstimator, PoseLandmark
from game_controller import GameController
from data_manager import DataManager


GAME_RECORDING        = False
GAME_RUNNING          = True
GAME_FPS              = 60

NORM_CENTER           = None
NORM_DISTANCE         = None

CAMERA_TYPE           = CameraReader.CAMERA_EXTERNAL
CAMERA_WIDTH          = 640 #px
CAMERA_HEIGHT         = 480 #px

POSE_MODEL_COMPLEXITY = PoseEstimator.MODEL_COMPLEXITY_FAST
POSE_MIN_VISIBILITY   = 0.2

CANVAS_WIDTH          = 1920 #px
CANVAS_HEIGHT         = 1080 #px

LANDMARK_RADIUS       = 8 #px
CONNECTION_WIDTH      = 2 #px
TARGET_RADIUS         = 20 #px

TARGET_START_ID       = 100
TEXT_ID               = 101

TARGET_START_EVENT_ID = 1
TARGET_END_EVENT_ID   = 2

TARGET_START_X        = CANVAS_WIDTH / 2 #px
TARGET_START_Y        = 200 #px

TEXT_X                = 50 #px
TEXT_Y                = 50 #px
TEXT_RECORDING        = "RECORDING"
TEXT_NOT_RECORDING    = "NOT RECORDING"
TEXT_SIZE             = 20 #px

RESULTS_FOLDER        = "./experiments/"


camera_reader   = CameraReader(CAMERA_TYPE, CAMERA_WIDTH, CAMERA_HEIGHT)
pose_estimator  = PoseEstimator(POSE_MODEL_COMPLEXITY, POSE_MIN_VISIBILITY)
game_controller = GameController(GAME_FPS, CANVAS_WIDTH, CANVAS_HEIGHT)
data_manager    = DataManager(RESULTS_FOLDER)


def create_objects():
    # Create the text
    game_controller.create_object_text(TEXT_ID, TEXT_X, TEXT_Y, GameController.COLOR_WHITE, TEXT_NOT_RECORDING, TEXT_SIZE)

    # Create the targets
    game_controller.create_object_circle(TARGET_START_ID, TARGET_START_X, TARGET_START_Y, GameController.COLOR_GREEN, TARGET_RADIUS)

    # Create the landmarks
    for landmark_id in PoseLandmark.get_landmarks():
        game_controller.create_object_circle(landmark_id, 0, 0, GameController.COLOR_BLUE, LANDMARK_RADIUS)


def create_events():
    # Create the events
    game_controller.create_event_dwell(TARGET_START_EVENT_ID, TARGET_START_ID, PoseLandmark.RIGHT_HAND, 500)
    game_controller.create_event_dwell(TARGET_END_EVENT_ID, TARGET_START_ID, PoseLandmark.RIGHT_HAND, 2500)


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
        result[landmark][0] = int(output[0] * CANVAS_WIDTH)  # To pixels
        result[landmark][1] = int(output[1] * CANVAS_HEIGHT) # To pixels

    return result


def substract_landmark(landmark_1, landmark_2):
    # Substract the second landmark
    # (from the first one)
    result = [0, 0]
    result[0] = landmark_1[0] - landmark_2[0]
    result[1] = landmark_1[1] - landmark_2[1]
    return result


def get_normalized_landmarks_and_targets(landmarks_and_targets):
    global NORM_CENTER, NORM_DISTANCE

    # Get the center
    if NORM_CENTER is None:
        NORM_CENTER = landmarks_and_targets.get(PoseLandmark.MIDDLE_SHOULDER)
    
    # Check the center
    if NORM_CENTER is None: return {}

    # Get the distance
    if NORM_DISTANCE is None:
        shoulder1 = landmarks_and_targets.get(PoseLandmark.RIGHT_SHOULDER)
        shoulder2 = landmarks_and_targets.get(PoseLandmark.LEFT_SHOULDER)
        if shoulder1 is None or shoulder2 is None: return {}

        dist_vect = substract_landmark(shoulder1, shoulder2)
        dist_x = dist_vect[0]
        dist_y = dist_vect[1]
        
        NORM_DISTANCE = math.sqrt(dist_x * dist_x + dist_y * dist_y)

    # Check the distance
    if NORM_DISTANCE == 0: return {}
    
    # Center the landmarks
    # Normalize the landmarks
    result = {}
    for landmark in landmarks_and_targets:
        output = landmarks_and_targets.get(landmark)   
        output = substract_landmark(output, NORM_CENTER)
        result[landmark] = [0, 0]
        result[landmark][0] = output[0] / NORM_DISTANCE
        result[landmark][1] = output[1] / NORM_DISTANCE

    return result


def update_states():
    global GAME_RUNNING, GAME_RECORDING, NORM_CENTER, NORM_DISTANCE

    # Refresh the states
    game_controller.refresh_states()

    # Set the running state
    GAME_RUNNING = game_controller.get_running_state()

    # Set the recording state
    prev_game_recording = GAME_RECORDING
    if game_controller.get_event_state(TARGET_START_EVENT_ID):
        GAME_RECORDING = True
    if game_controller.get_event_state(TARGET_END_EVENT_ID):
        GAME_RECORDING = False
    
    # Start (or end) the iteration
    if not prev_game_recording and GAME_RECORDING:
        data_manager.start_iteration(DataManager.SIDE_RIGHT)
    elif prev_game_recording and not GAME_RECORDING:
        data_manager.end_iteration()
        NORM_CENTER = None
        NORM_DISTANCE = None


def update_objects(landmarks_as_px):
    # Update the text
    text_text = TEXT_NOT_RECORDING
    if GAME_RECORDING: text_text = TEXT_RECORDING
    game_controller.update_object_text(TEXT_ID, None, None, None, text_text, None)

    # Update the target
    target_color = GameController.COLOR_GREEN
    if GAME_RECORDING: target_color = GameController.COLOR_RED
    game_controller.update_object_circle(TARGET_START_ID, None, None, target_color, None)

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
        game_controller.create_object_line(None, px_landmark1[0], px_landmark1[1], px_landmark2[0], px_landmark2[1], GameController.COLOR_BLUE, CONNECTION_WIDTH)


def update_data(timestamp, normalized_landmarks_and_targets):
    # Get the data
    neck = normalized_landmarks_and_targets.get(PoseLandmark.MIDDLE_SHOULDER)
    hip = normalized_landmarks_and_targets.get(PoseLandmark.MIDDLE_HIP)
    shoulder = normalized_landmarks_and_targets.get(PoseLandmark.RIGHT_SHOULDER)
    elbow = normalized_landmarks_and_targets.get(PoseLandmark.RIGHT_ELBOW)
    wrist = normalized_landmarks_and_targets.get(PoseLandmark.RIGHT_WRIST)
    end_effector = normalized_landmarks_and_targets.get(PoseLandmark.RIGHT_HAND)
    target = normalized_landmarks_and_targets.get(TARGET_START_ID)

    # Check the data
    landmarks = [neck, hip, shoulder, elbow, wrist, end_effector, target]
    for landmark in landmarks:
        if landmark is None: return

    # Add the data
    data_manager.add_data(timestamp, neck[0], neck[1], hip[0], hip[1], shoulder[0], shoulder[1], elbow[0],
                          elbow[1], wrist[0], wrist[1], end_effector[0], end_effector[1], target[0], target[1])


def main():
    game_controller.set_background_color(GameController.COLOR_BLACK)
    create_objects()
    create_events()

    while GAME_RUNNING:
        update_states()

        image = get_image()
        if image is None: continue

        landmarks = get_landmarks(image)
        if landmarks is None: continue
        
        landmarks_as_px = get_landmarks_as_px(landmarks)
        update_objects(landmarks_as_px)

        if GAME_RECORDING:
            timestamp = time.time()
            landmarks_and_targets = landmarks_as_px.copy()
            landmarks_and_targets[TARGET_START_ID] = [TARGET_START_X, TARGET_START_Y]
            normalized_landmarks_and_targets = get_normalized_landmarks_and_targets(landmarks_and_targets)
            update_data(timestamp, normalized_landmarks_and_targets)

        game_controller.refresh_screen()
        game_controller.regulate_fps()


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        GAME_RUNNING = False
    finally:
        camera_reader.close()
        pose_estimator.close()
        game_controller.close()
        data_manager.close()