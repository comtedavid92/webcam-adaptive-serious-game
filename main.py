from camera_reader import CameraReader
from pose_estimator import PoseEstimator, PoseLandmark
from game_controller import GameController
from utils import Utils


GAME_RECORDING        = False
GAME_RUNNING          = True
GAME_FPS              = 60

CAMERA_TYPE           = CameraReader.CAMERA_EXTERNAL
CAMERA_WIDTH          = 640
CAMERA_HEIGHT         = 480

POSE_MODEL_COMPLEXITY = PoseEstimator.MODEL_COMPLEXITY_FAST
POSE_MIN_VISIBILITY   = 0.2

CANVAS_WIDTH          = 1920
CANVAS_HEIGHT         = 1080

LANDMARK_RADIUS       = 8
CONNECTION_WIDTH      = 2
TARGET_RADIUS         = 20

TARGET_START_ID       = 200
TARGET_END_ID         = 201

TARGET_START_EVENT_ID = 1
TARGET_END_EVENT_ID   = 2

TARGET_START_X        = CANVAS_WIDTH - 400
TARGET_START_Y        = CANVAS_HEIGHT - 400

TARGET_END_X          = CANVAS_WIDTH / 2
TARGET_END_Y          = 200

TEXT_ID               = 202
TEXT_RECORDING        = "RECORDING"
TEXT_NOT_RECORDING    = "NOT RECORDING"
TEXT_SIZE             = 20

TEXT_X                = 50
TEXT_Y                = 50


camera_reader   = CameraReader(CAMERA_TYPE, CAMERA_WIDTH, CAMERA_HEIGHT)
pose_estimator  = PoseEstimator(POSE_MODEL_COMPLEXITY, POSE_MIN_VISIBILITY)
game_controller = GameController(GAME_FPS, CANVAS_WIDTH, CANVAS_HEIGHT)


def create_objects():
    # Create the text
    game_controller.create_object_text(TEXT_ID, TEXT_X, TEXT_Y, GameController.COLOR_WHITE, TEXT_NOT_RECORDING, TEXT_SIZE)

    # Create the targets
    game_controller.create_object_circle(TARGET_START_ID, TARGET_START_X, TARGET_START_Y, GameController.COLOR_GREEN, TARGET_RADIUS)
    game_controller.create_object_circle(TARGET_END_ID, TARGET_END_X, TARGET_END_Y, GameController.COLOR_RED, TARGET_RADIUS)

    # Create the landmarks
    for landmark_id in PoseLandmark.get_landmarks():
        game_controller.create_object_circle(landmark_id, 0, 0, GameController.COLOR_BLUE, LANDMARK_RADIUS)


def create_events():
    # Create the events
    game_controller.create_event_dwell(TARGET_START_EVENT_ID, TARGET_START_ID, PoseLandmark.PROXY_RIGHT_HAND, 2500)
    game_controller.create_event_contact(TARGET_END_EVENT_ID, TARGET_END_ID, PoseLandmark.PROXY_RIGHT_HAND)


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


def update_objects(px_landmarks):
    # Update the text
    text_text = TEXT_NOT_RECORDING
    if GAME_RECORDING: text_text = TEXT_RECORDING
    game_controller.update_object_text(TEXT_ID, None, None, None, text_text, None)

    # Update the start target
    target_color = GameController.COLOR_GREEN
    if GAME_RECORDING: target_color = GameController.COLOR_BLACK
    game_controller.update_object_circle(TARGET_START_ID, None, None, target_color, None)

    # Update the landmarks
    for landmark_id in PoseLandmark.get_landmarks():
        px_landmark = px_landmarks.get(landmark_id)
        if px_landmark is None: continue
        game_controller.update_object_circle(landmark_id, px_landmark[0], px_landmark[1], None, None)
    
    # Create the landmark connections
    for connection in PoseLandmark.get_connections():
        landmark_id1 = connection[0]
        landmark_id2 = connection[1]
        px_landmark1 = px_landmarks.get(landmark_id1)
        px_landmark2 = px_landmarks.get(landmark_id2)
        if px_landmark1 is None or px_landmark2 is None: continue
        game_controller.create_object_line(None, px_landmark1[0], px_landmark1[1], px_landmark2[0], px_landmark2[1], GameController.COLOR_BLUE, CONNECTION_WIDTH)


def update_states():
    global GAME_RUNNING, GAME_RECORDING

    # Refresh the states
    game_controller.refresh_states()

    # Set running state
    GAME_RUNNING = game_controller.get_running_state()

    # Set recording state
    if game_controller.get_event_state(TARGET_START_EVENT_ID):
        GAME_RECORDING = True
    if game_controller.get_event_state(TARGET_END_EVENT_ID):
        GAME_RECORDING = False


def main():    
    game_controller.set_background_color(GameController.COLOR_BLACK)
    create_objects()
    create_events()

    while GAME_RUNNING:
        image = get_image()
        if image is None: continue
        landmarks = get_landmarks(image)
        if landmarks is None: continue
        px_landmarks = Utils.to_px_landmarks(landmarks, CANVAS_WIDTH, CANVAS_HEIGHT)
        update_objects(px_landmarks)
        update_states()
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