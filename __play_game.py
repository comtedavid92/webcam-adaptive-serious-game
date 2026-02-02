import sys
import math
import time
import random
from camera_reader import CameraReader
from pose_estimator import PoseEstimator, PoseLandmark
from game_controller import GameController
from data_manager import DataManager

# ===================================================================================================================================================

USER_ID                 = None
USER_TRAINED_SIDE       = None

GAME_CONTROLLER         = None
GAME_RUNNING            = True
GAME_FPS                = 60
GAME_WIDTH              = 1600 # px
GAME_HEIGHT             = 1200 # px

WINDOW_NAME               = "webcam-adaptive-serious-game"
WINDOW_ICON               = "./docs/icon.png"

CAMERA_READER           = None
CAMERA_TYPE             = CameraReader.CAMERA_EXTERNAL
CAMERA_WIDTH            = 640 # px
CAMERA_HEIGHT           = 480 # px

POSE_ESTIMATOR          = None
POSE_MODEL_COMPLEXITY   = PoseEstimator.MODEL_COMPLEXITY_FAST
POSE_MIN_VISIBILITY     = 0.2
POSE_EXCLUDED_LANDMARKS = [PoseLandmark.RIGHT_HAND, PoseLandmark.LEFT_HAND]
POSE_DUMMY_VARIABLE     = PoseLandmark.exclude_landmarks(POSE_EXCLUDED_LANDMARKS)

DATA_MANAGER            = None
DATA_FOLDER             = "./experiments/{user_id}/"
DATA_REACH_TYPE         = 0
DATA_DWELL_TYPE         = 1

OBJ_FIRST_TEXT_X        = 10   # px
OBJ_FIRST_TEXT_Y        = 10   # px
OBJ_SECOND_TEXT_X       = 10   # px
OBJ_SECOND_TEXT_Y       = 50   # px
OBJ_THIRD_TEXT_X        = 10   # px
OBJ_THIRD_TEXT_Y        = 90   # px
OBJ_TEXT_SIZE           = 40   # px
OBJ_TARGET_RADIUS       = 20   # px
OBJ_DWELL_TIME          = 1000 # ms

DIFF_MIN_ANGLE          = 90    # degrees
DIFF_MAX_ANGLE          = 210   # degrees
DIFF_MIN_DISTANCE       = 50    # px
DIFF_MAX_DISTANCE       = None  # px
DIFF_MIN_TIME           = 1000  # ms
DIFF_MAX_TIME           = 5000  # ms
DIFF_MIN_SIZE           = 10    # px
DIFF_MAX_SIZE           = 40    # px
DIFF_MIN_DWELL          = 1000  # ms
DIFF_MAX_DWELL          = 5000  # ms
DIFF_MIN_TRUNK          = 0     # degrees
DIFF_MAX_TRUNK          = 20    # degrees 

STEP_CURRENT            = 0
STEP_CALIBRATION        = 0
STEP_PLAY               = 1

STEP_CALIBRATION_MEMORY = {
    "substep"            : 0,
    # Object ids
    "text_instr_id"      : 100,
    "target_hand_id"     : 101,
    "text_hand_id"       : 102,
    "target_shoulder_id" : 103,
    "text_shoulder_id"   : 104,
    # Event ids
    "event_hand_id"      : 200,
    "event_shoulder_id"  : 201,
    # Other variables
    "max_distances"      : [],
}

STEP_PLAY_MEMORY = {
    "substep"              : 0,
    # Object ids
    "text_instr_id"        : 100,
    "text_score_id"        : 101,
    "text_option_id"       : 102,
    "target_start_id"      : 103,
    "text_start_id"        : 104,
    "target_end_id"        : 105,
    "text_end_id"          : 106,
    # Events ids
    "event_start_id"       : 200,
    "event_expired_end_id" : 201,
    "event_contact_end_id" : 202,
    "event_dwell_end_id"   : 203,
    # Other variables
    "norm_positions"       : [],
    "norm_position"        : None,
    "norm_distances"       : [],
    "norm_distance"        : None,
    "start_positions"      : [],
    "start_position"       : None,
    "end_position"         : None,
    "dda_diff_angle"       : 0,
    "diff_angle"           : 0,
    "dda_diff_distance"    : 0,
    "diff_distance"        : 0,
    "dda_diff_time"        : 0,
    "diff_time"            : 0,
    "dda_diff_size"        : 0,
    "diff_size"            : 0,
    "dda_diff_dwell"       : 0,
    "diff_dwell"           : 0,
    "dda_diff_trunk"       : 0,
    "diff_trunk"           : 0,
    "successes"            : [],
}

# STEP CALIBRATION ==================================================================================================================================

def update_step_calibration(landmarks_as_px):
    global STEP_CALIBRATION_MEMORY, DIFF_MAX_DISTANCE, STEP_CURRENT

    # ========
    # Ask the user to align his shoulder and his hand on the targets
    # ========
    if STEP_CALIBRATION_MEMORY["substep"] == 0:
        # Instruction text
        side = "right" if USER_TRAINED_SIDE == DataManager.SIDE_RIGHT else "left"
        text = "Calibration step : please extend your " + side + " arm and align your shoulder and your hand on the targets"
        GAME_CONTROLLER.create_object_text(STEP_CALIBRATION_MEMORY["text_instr_id"], OBJ_FIRST_TEXT_X, OBJ_FIRST_TEXT_Y, GameController.COLOR_WHITE, text, OBJ_TEXT_SIZE)

        # Hand target
        hand_x = GAME_WIDTH - 400 if USER_TRAINED_SIDE == DataManager.SIDE_RIGHT else 400
        hand_y = GAME_HEIGHT / 2
        GAME_CONTROLLER.create_object_circle(STEP_CALIBRATION_MEMORY["target_hand_id"], hand_x, hand_y, GameController.COLOR_GREEN, OBJ_TARGET_RADIUS)

        # Shoulder target
        shoulder_x = hand_x - 500 if USER_TRAINED_SIDE == DataManager.SIDE_RIGHT else hand_x + 500
        shoulder_y = GAME_HEIGHT / 2
        GAME_CONTROLLER.create_object_circle(STEP_CALIBRATION_MEMORY["target_shoulder_id"], shoulder_x, shoulder_y, GameController.COLOR_GREEN, OBJ_TARGET_RADIUS)

        # Hand text
        hand_x = hand_x + OBJ_TARGET_RADIUS + 10
        GAME_CONTROLLER.create_object_text(STEP_CALIBRATION_MEMORY["text_hand_id"], hand_x, hand_y, GameController.COLOR_WHITE, "hand", OBJ_TEXT_SIZE)

        # Shoulder text
        shoulder_x = shoulder_x + OBJ_TARGET_RADIUS + 10
        GAME_CONTROLLER.create_object_text(STEP_CALIBRATION_MEMORY["text_shoulder_id"], shoulder_x, shoulder_y, GameController.COLOR_WHITE, "shoulder", OBJ_TEXT_SIZE)

        # Hand event
        landmark_id = PoseLandmark.RIGHT_WRIST if USER_TRAINED_SIDE == DataManager.SIDE_RIGHT else PoseLandmark.LEFT_WRIST
        GAME_CONTROLLER.create_event_dwell(STEP_CALIBRATION_MEMORY["event_hand_id"], STEP_CALIBRATION_MEMORY["target_hand_id"], landmark_id, OBJ_DWELL_TIME)
        
        # Shoulder event
        landmark_id = PoseLandmark.RIGHT_SHOULDER if USER_TRAINED_SIDE == DataManager.SIDE_RIGHT else PoseLandmark.LEFT_SHOULDER
        GAME_CONTROLLER.create_event_dwell(STEP_CALIBRATION_MEMORY["event_shoulder_id"], STEP_CALIBRATION_MEMORY["target_shoulder_id"], landmark_id, OBJ_DWELL_TIME)

        STEP_CALIBRATION_MEMORY["substep"] = 10
    
    # ========
    # Wait for the user to align his shoulder and his hand on the targets
    # When aligned :
    # - Take 10 measurements of the "shoulder-to-hand" distance
    # - Set the max distance difficulty parameter to the mean
    # ========
    elif STEP_CALIBRATION_MEMORY["substep"] == 10:
        event_hand = GAME_CONTROLLER.get_event_continuous_state(STEP_CALIBRATION_MEMORY["event_hand_id"])
        event_shoulder = GAME_CONTROLLER.get_event_continuous_state(STEP_CALIBRATION_MEMORY["event_shoulder_id"])

        # Not aligned
        if not event_hand or not event_shoulder:
            STEP_CALIBRATION_MEMORY["max_distances"].clear()

        # Aligned
        else:
            landmark_id = PoseLandmark.RIGHT_WRIST if USER_TRAINED_SIDE == DataManager.SIDE_RIGHT else PoseLandmark.LEFT_WRIST
            landmark_hand = landmarks_as_px.get(landmark_id)
            
            landmark_id = PoseLandmark.RIGHT_SHOULDER if USER_TRAINED_SIDE == DataManager.SIDE_RIGHT else PoseLandmark.LEFT_SHOULDER
            landmark_shoulder = landmarks_as_px.get(landmark_id)
            
            if landmark_hand is None or landmark_shoulder is None: return
            
            distance = get_landmarks_distance(landmark_hand, landmark_shoulder)
            STEP_CALIBRATION_MEMORY["max_distances"].append(distance)

            if len(STEP_CALIBRATION_MEMORY["max_distances"]) >= 10:
                DIFF_MAX_DISTANCE = get_value_mean(STEP_CALIBRATION_MEMORY["max_distances"])
                GAME_CONTROLLER.delete_object(STEP_CALIBRATION_MEMORY["text_instr_id"])
                GAME_CONTROLLER.delete_object(STEP_CALIBRATION_MEMORY["target_hand_id"])
                GAME_CONTROLLER.delete_object(STEP_CALIBRATION_MEMORY["target_shoulder_id"])
                GAME_CONTROLLER.delete_object(STEP_CALIBRATION_MEMORY["text_hand_id"])
                GAME_CONTROLLER.delete_object(STEP_CALIBRATION_MEMORY["text_shoulder_id"])
                GAME_CONTROLLER.delete_event(STEP_CALIBRATION_MEMORY["event_hand_id"])
                GAME_CONTROLLER.delete_event(STEP_CALIBRATION_MEMORY["event_shoulder_id"])                
                STEP_CURRENT = STEP_PLAY

# STEP PLAY =========================================================================================================================================

def update_step_play(landmarks_as_px):
    global STEP_PLAY_MEMORY, STEP_CURRENT

    # ========
    # Ask the user to align his hand on the start target
    # ========
    if STEP_PLAY_MEMORY["substep"] == 0:
        # Instruction text
        side = "right" if USER_TRAINED_SIDE == DataManager.SIDE_RIGHT else "left"
        text = "Play step : please align your " + side + " hand on the start target"
        GAME_CONTROLLER.create_object_text(STEP_PLAY_MEMORY["text_instr_id"], OBJ_FIRST_TEXT_X, OBJ_FIRST_TEXT_Y, GameController.COLOR_WHITE, text, OBJ_TEXT_SIZE)

        # Score text
        successes = STEP_PLAY_MEMORY["successes"].count(True)
        total = len(STEP_PLAY_MEMORY["successes"])
        text = "Score : " + str(successes) + " / " + str(total)
        GAME_CONTROLLER.create_object_text(STEP_PLAY_MEMORY["text_score_id"], OBJ_SECOND_TEXT_X, OBJ_SECOND_TEXT_Y, GameController.COLOR_WHITE, text, OBJ_TEXT_SIZE)

        # Option text
        GAME_CONTROLLER.create_object_text(STEP_PLAY_MEMORY["text_option_id"], OBJ_THIRD_TEXT_X, OBJ_THIRD_TEXT_Y, GameController.COLOR_WHITE, "", OBJ_TEXT_SIZE)

        # Shoulder landmark
        landmark_id = PoseLandmark.RIGHT_SHOULDER if USER_TRAINED_SIDE == DataManager.SIDE_RIGHT else PoseLandmark.LEFT_SHOULDER
        shoulder_landmark = landmarks_as_px.get(landmark_id)
        if shoulder_landmark is None: return

        # Start target
        x = shoulder_landmark[0]
        y = shoulder_landmark[1]
        GAME_CONTROLLER.create_object_circle(STEP_PLAY_MEMORY["target_start_id"], x, y, GameController.COLOR_GREEN, OBJ_TARGET_RADIUS)

        # Start text
        x = x + OBJ_TARGET_RADIUS + 10
        GAME_CONTROLLER.create_object_text(STEP_PLAY_MEMORY["text_start_id"], x, y, GameController.COLOR_WHITE, "start", OBJ_TEXT_SIZE)

        # Start event
        landmark_id = PoseLandmark.RIGHT_WRIST if USER_TRAINED_SIDE == DataManager.SIDE_RIGHT else PoseLandmark.LEFT_WRIST
        GAME_CONTROLLER.create_event_dwell(STEP_PLAY_MEMORY["event_start_id"], STEP_PLAY_MEMORY["target_start_id"], landmark_id, OBJ_DWELL_TIME)

        STEP_PLAY_MEMORY["substep"] = 10

    # ========
    # Update the start target to the shoulder position
    # Wait for the user to align his hand on the start target
    # When aligned :
    # - Take 10 measurements of the position for normalization
    # - Take 10 measurements of the distance for normalization
    # - Take 10 measurements of the start position
    # - Set each value to the mean
    # ========
    elif STEP_PLAY_MEMORY["substep"] == 10:
        landmark_id = PoseLandmark.RIGHT_SHOULDER if USER_TRAINED_SIDE == DataManager.SIDE_RIGHT else PoseLandmark.LEFT_SHOULDER
        shoulder_landmark = landmarks_as_px.get(landmark_id)
        if shoulder_landmark is None: return

        x = shoulder_landmark[0]
        y = shoulder_landmark[1]
        GAME_CONTROLLER.update_object_circle(STEP_PLAY_MEMORY["target_start_id"], x, y, None, None)

        x = x + OBJ_TARGET_RADIUS + 10
        GAME_CONTROLLER.update_object_text(STEP_PLAY_MEMORY["text_start_id"], x, y, None, None, None)

        event = GAME_CONTROLLER.get_event_continuous_state(STEP_PLAY_MEMORY["event_start_id"])

        # Not aligned
        if not event:
            STEP_PLAY_MEMORY["norm_positions"].clear()
            STEP_PLAY_MEMORY["norm_distances"].clear()
            STEP_PLAY_MEMORY["start_positions"].clear()

        # Aligned
        else:
            middle_shoulder = landmarks_as_px.get(PoseLandmark.MIDDLE_SHOULDER)
            right_soulder_landmark = landmarks_as_px.get(PoseLandmark.RIGHT_SHOULDER)
            left_soulder_landmark = landmarks_as_px.get(PoseLandmark.LEFT_SHOULDER)
            if middle_shoulder is None or right_soulder_landmark is None or left_soulder_landmark is None: return

            norm_position = middle_shoulder
            norm_distance = get_landmarks_distance(right_soulder_landmark, left_soulder_landmark)
            STEP_PLAY_MEMORY["norm_positions"].append(norm_position)
            STEP_PLAY_MEMORY["norm_distances"].append(norm_distance)
            STEP_PLAY_MEMORY["start_positions"].append(shoulder_landmark)

            if len(STEP_PLAY_MEMORY["norm_positions"]) >= 10:
                STEP_PLAY_MEMORY["norm_position"] = get_landmarks_mean(STEP_PLAY_MEMORY["norm_positions"])
                STEP_PLAY_MEMORY["norm_distance"] = get_value_mean(STEP_PLAY_MEMORY["norm_distances"])
                STEP_PLAY_MEMORY["start_position"] = get_landmarks_mean(STEP_PLAY_MEMORY["start_positions"])            
                GAME_CONTROLLER.delete_object(STEP_PLAY_MEMORY["target_start_id"])
                GAME_CONTROLLER.delete_object(STEP_PLAY_MEMORY["text_start_id"])
                GAME_CONTROLLER.delete_event(STEP_PLAY_MEMORY["event_start_id"])
                STEP_PLAY_MEMORY["substep"] = 20

    # ========
    # Get the DDA difficulty parameters [0, 1]
    # Compute the difficulty parameters [min, max]
    # Compute the end position
    # ========
    elif STEP_PLAY_MEMORY["substep"] == 20:
        # DDA
        # TODO run the DDA
        # TODO use the trunk parameter

        STEP_PLAY_MEMORY["dda_diff_angle"] = random.random()
        STEP_PLAY_MEMORY["dda_diff_distance"] = random.random()
        STEP_PLAY_MEMORY["dda_diff_time"] = 0.5
        STEP_PLAY_MEMORY["dda_diff_size"] = 0.5
        STEP_PLAY_MEMORY["dda_diff_dwell"] = 0.25
        STEP_PLAY_MEMORY["dda_diff_trunk"] = 0.5

        STEP_PLAY_MEMORY["diff_angle"] = get_value_scaled(DIFF_MIN_ANGLE, DIFF_MAX_ANGLE, STEP_PLAY_MEMORY["dda_diff_angle"])
        STEP_PLAY_MEMORY["diff_distance"] = get_value_scaled(DIFF_MIN_DISTANCE, DIFF_MAX_DISTANCE, STEP_PLAY_MEMORY["dda_diff_distance"])
        STEP_PLAY_MEMORY["diff_time"] = get_value_scaled(DIFF_MIN_TIME, DIFF_MAX_TIME, STEP_PLAY_MEMORY["dda_diff_time"])
        STEP_PLAY_MEMORY["diff_size"] = get_value_scaled(DIFF_MIN_SIZE, DIFF_MAX_SIZE, STEP_PLAY_MEMORY["dda_diff_size"])
        STEP_PLAY_MEMORY["diff_dwell"] = get_value_scaled(DIFF_MIN_DWELL, DIFF_MAX_DWELL, STEP_PLAY_MEMORY["dda_diff_dwell"])
        STEP_PLAY_MEMORY["diff_trunk"] = get_value_scaled(DIFF_MIN_TRUNK, DIFF_MAX_TRUNK, STEP_PLAY_MEMORY["dda_diff_trunk"])

        STEP_PLAY_MEMORY["end_position"] = get_end_position(STEP_PLAY_MEMORY["start_position"], STEP_PLAY_MEMORY["diff_angle"], STEP_PLAY_MEMORY["diff_distance"])

        STEP_PLAY_MEMORY["substep"] = 30

    # ========
    # Ask the user to align his hand on the end target
    # Start the reach iteration
    # ========
    elif STEP_PLAY_MEMORY["substep"] == 30:
        # Instruction text
        side = "right" if USER_TRAINED_SIDE == DataManager.SIDE_RIGHT else "left"
        text = "Play step : please align your " + side + " hand on the end target"
        GAME_CONTROLLER.update_object_text(STEP_PLAY_MEMORY["text_instr_id"], None, None, None, text, None)

        # End target
        x = STEP_PLAY_MEMORY["end_position"][0]
        y = STEP_PLAY_MEMORY["end_position"][1]
        GAME_CONTROLLER.create_object_circle(STEP_PLAY_MEMORY["target_end_id"], x, y, GameController.COLOR_ORANGE, STEP_PLAY_MEMORY["diff_size"])

        # End text
        x = x + STEP_PLAY_MEMORY["diff_size"] + 10
        GAME_CONTROLLER.create_object_text(STEP_PLAY_MEMORY["text_end_id"], x, y, GameController.COLOR_WHITE, "", OBJ_TEXT_SIZE)

        # Expired event
        GAME_CONTROLLER.create_event_expired(STEP_PLAY_MEMORY["event_expired_end_id"], STEP_PLAY_MEMORY["target_end_id"], STEP_PLAY_MEMORY["diff_time"])

        # Contact event
        landmark_id = PoseLandmark.RIGHT_WRIST if USER_TRAINED_SIDE == DataManager.SIDE_RIGHT else PoseLandmark.LEFT_WRIST
        GAME_CONTROLLER.create_event_contact(STEP_PLAY_MEMORY["event_contact_end_id"], STEP_PLAY_MEMORY["target_end_id"], landmark_id)

        # Iteration
        DATA_MANAGER.start_iteration(USER_TRAINED_SIDE, DATA_REACH_TYPE)

        STEP_PLAY_MEMORY["substep"] = 40

    # ========
    # Update the data
    # Wait for the target to expire
    # Wait for the user to align his hand on the end target
    # When expired :
    # - Append a fail
    # - End the iteration
    # - Go to the first step
    # When aligned :
    # - End the iteration
    # - Go to the next step
    # ========
    elif STEP_PLAY_MEMORY["substep"] == 40:
        # End text
        time = GAME_CONTROLLER.get_event_expired_remaining_time_ms(STEP_PLAY_MEMORY["event_expired_end_id"])
        time = round(time / 1000, 1)
        text = "end | reach | " + str(time) + " s"
        GAME_CONTROLLER.update_object_text(STEP_PLAY_MEMORY["text_end_id"], None, None, None, text, None)

        # Data update
        enough_data = update_data(STEP_PLAY_MEMORY["target_end_id"], STEP_PLAY_MEMORY["end_position"], STEP_PLAY_MEMORY["norm_position"], STEP_PLAY_MEMORY["norm_distance"], landmarks_as_px)
        if not enough_data: return

        # Events
        event_expired = GAME_CONTROLLER.get_event_continuous_state(STEP_PLAY_MEMORY["event_expired_end_id"])
        event_contact = GAME_CONTROLLER.get_event_continuous_state(STEP_PLAY_MEMORY["event_contact_end_id"])

        # Target expired
        if event_expired:
            STEP_PLAY_MEMORY["successes"].append(False)
            GAME_CONTROLLER.delete_object(STEP_PLAY_MEMORY["text_instr_id"])
            GAME_CONTROLLER.delete_object(STEP_PLAY_MEMORY["text_score_id"])
            GAME_CONTROLLER.delete_object(STEP_PLAY_MEMORY["text_option_id"])
            GAME_CONTROLLER.delete_object(STEP_PLAY_MEMORY["target_end_id"])
            GAME_CONTROLLER.delete_object(STEP_PLAY_MEMORY["text_end_id"])
            GAME_CONTROLLER.delete_event(STEP_PLAY_MEMORY["event_expired_end_id"])
            GAME_CONTROLLER.delete_event(STEP_PLAY_MEMORY["event_contact_end_id"])
            DATA_MANAGER.end_iteration()
            STEP_PLAY_MEMORY["substep"] = 0

        # Aligned
        elif event_contact:
            GAME_CONTROLLER.delete_event(STEP_PLAY_MEMORY["event_expired_end_id"])
            DATA_MANAGER.end_iteration()
            STEP_PLAY_MEMORY["substep"] = 50
        
    # ========
    # Ask the user to dwell with his hand on the target
    # Start the dwell iteration
    # ========
    elif STEP_PLAY_MEMORY["substep"] == 50:
        # Instruction text
        side = "right" if USER_TRAINED_SIDE == DataManager.SIDE_RIGHT else "left"
        text = "Play step : please dwell with your " + side + " hand on the end target"
        GAME_CONTROLLER.update_object_text(STEP_PLAY_MEMORY["text_instr_id"], None, None, None, text, None)

        # End target
        GAME_CONTROLLER.update_object_circle(STEP_PLAY_MEMORY["target_end_id"], None, None, GameController.COLOR_RED, None)

        # Dwell event
        landmark_id = PoseLandmark.RIGHT_WRIST if USER_TRAINED_SIDE == DataManager.SIDE_RIGHT else PoseLandmark.LEFT_WRIST
        GAME_CONTROLLER.create_event_dwell(STEP_PLAY_MEMORY["event_dwell_end_id"], STEP_PLAY_MEMORY["target_end_id"], landmark_id, STEP_PLAY_MEMORY["diff_dwell"])

        # Iteration
        DATA_MANAGER.start_iteration(USER_TRAINED_SIDE, DATA_DWELL_TYPE)

        STEP_PLAY_MEMORY["substep"] = 60

    # ========
    # Update the data
    # Wait for the user to lose contact with the target
    # Wait for the user to dwell with his hand on the target
    # When contact lost :
    # - Append a fail
    # - End the iteration
    # - Go to the first step
    # When aligned :
    # - Append a success
    # - End the iteration
    # - Go to the first step
    # ========
    elif STEP_PLAY_MEMORY["substep"] == 60:
        # End text
        time = GAME_CONTROLLER.get_event_dwell_remaining_time_ms(STEP_PLAY_MEMORY["event_dwell_end_id"])
        time = round(time / 1000, 1)
        text = "end | dwell | " + str(time) + " ms"
        GAME_CONTROLLER.update_object_text(STEP_PLAY_MEMORY["text_end_id"], None, None, None, text, None)

        # Data update
        enough_data = update_data(STEP_PLAY_MEMORY["target_end_id"], STEP_PLAY_MEMORY["end_position"], STEP_PLAY_MEMORY["norm_position"], STEP_PLAY_MEMORY["norm_distance"], landmarks_as_px)
        if not enough_data: return

        # Events
        event_contact = GAME_CONTROLLER.get_event_continuous_state(STEP_PLAY_MEMORY["event_contact_end_id"])
        event_dwell = GAME_CONTROLLER.get_event_continuous_state(STEP_PLAY_MEMORY["event_dwell_end_id"])

        # Contact lost
        if not event_contact:
            STEP_PLAY_MEMORY["successes"].append(False)

        # Dwelled
        elif event_dwell:
            STEP_PLAY_MEMORY["successes"].append(True)

        if not event_contact or event_dwell:
            GAME_CONTROLLER.delete_object(STEP_PLAY_MEMORY["text_instr_id"])
            GAME_CONTROLLER.delete_object(STEP_PLAY_MEMORY["text_score_id"])
            GAME_CONTROLLER.delete_object(STEP_PLAY_MEMORY["text_option_id"])
            GAME_CONTROLLER.delete_object(STEP_PLAY_MEMORY["target_end_id"])
            GAME_CONTROLLER.delete_object(STEP_PLAY_MEMORY["text_end_id"])
            GAME_CONTROLLER.delete_event(STEP_PLAY_MEMORY["event_contact_end_id"])
            GAME_CONTROLLER.delete_event(STEP_PLAY_MEMORY["event_dwell_end_id"])
            DATA_MANAGER.end_iteration()
            STEP_PLAY_MEMORY["substep"] = 0

# STEP UTILS ========================================================================================================================================

def get_value_mean(list):
    sum = 0
    for item in list: sum += item
    mean = sum / len(list)
    return mean

def get_value_scaled(min_value, max_value, scale):
    distance = max_value - min_value
    parameter = min_value + scale * distance
    return parameter

def get_end_position(start_position, angle, distance):
    end_position = [0, 0]
    alpha = math.radians(angle)
    opp = math.sin(alpha) * distance
    adj = math.cos(alpha) * distance
    end_position[0] = start_position[0] + opp
    end_position[1] = start_position[1] + adj
    return end_position

def get_landmarks_subtraction(landmark_1, landmark_2):
    result = [0, 0]
    result[0] = landmark_1[0] - landmark_2[0]
    result[1] = landmark_1[1] - landmark_2[1]
    return result

def get_landmarks_distance(landmark_1, landmark_2):
    dist_vect = get_landmarks_subtraction(landmark_1, landmark_2)
    dist_x = dist_vect[0]
    dist_y = dist_vect[1]
    dist = math.sqrt(dist_x * dist_x + dist_y * dist_y)
    return dist

def get_landmarks_mean(landmarks):
    sum_x = 0
    sum_y = 0
    for item in landmarks:
        sum_x += item[0]
        sum_y += item[1]
    mean_x = sum_x / len(landmarks)
    mean_y = sum_y / len(landmarks)
    return [mean_x, mean_y]

def get_landmarks_normalized(norm_position, norm_distance, landmarks):    
    result = {}
    for landmark in landmarks:
        output = landmarks.get(landmark)   
        # Center the landmarks
        output = get_landmarks_subtraction(output, norm_position)
        # Normalize the landmarks
        result[landmark] = [0, 0]
        result[landmark][0] = output[0] / norm_distance
        result[landmark][1] = output[1] / norm_distance

    return result

def update_data(target_id, target_position, norm_position, norm_distance, landmarks):
    # Get the normalized landmarks
    landmarks[target_id] = target_position
    landmarks = get_landmarks_normalized(norm_position, norm_distance, landmarks)

    # Get the data
    neck = landmarks.get(PoseLandmark.MIDDLE_SHOULDER)
    hip = landmarks.get(PoseLandmark.MIDDLE_HIP)
    shoulder = landmarks.get(PoseLandmark.RIGHT_SHOULDER) if USER_TRAINED_SIDE == DataManager.SIDE_RIGHT else landmarks.get(PoseLandmark.LEFT_SHOULDER)
    elbow = landmarks.get(PoseLandmark.RIGHT_ELBOW) if USER_TRAINED_SIDE == DataManager.SIDE_RIGHT else landmarks.get(PoseLandmark.LEFT_ELBOW)
    wrist = landmarks.get(PoseLandmark.RIGHT_WRIST) if USER_TRAINED_SIDE == DataManager.SIDE_RIGHT else landmarks.get(PoseLandmark.LEFT_WRIST)
    end_effector = landmarks.get(PoseLandmark.RIGHT_WRIST) if USER_TRAINED_SIDE == DataManager.SIDE_RIGHT else landmarks.get(PoseLandmark.LEFT_WRIST)
    target = landmarks.get(target_id)

    # Check the data
    landmarks = [neck, hip, shoulder, elbow, wrist, end_effector, target]
    for landmark in landmarks:
        if landmark is None:return
    
    # Add the data
    timestamp = time.time()
    enough_data = DATA_MANAGER.add_data(timestamp, neck[0], neck[1], hip[0], hip[1], shoulder[0], shoulder[1], elbow[0],
                                        elbow[1], wrist[0], wrist[1], end_effector[0], end_effector[1], target[0], target[1])
    
    return enough_data

# MAIN ==============================================================================================================================================

def main(parameters):
    check_parameters(parameters)
    set_parameters(parameters)
    set_utils()

    set_background()
    create_landmarks()

    while GAME_RUNNING:
        update_game_states()

        image = get_image()
        if image is None: continue

        landmarks = get_landmarks(image)
        if landmarks is None: continue

        landmarks_as_px = get_landmarks_as_px(landmarks)

        update_steps(landmarks_as_px)
        update_landmarks(landmarks_as_px)

        draw_canvas()
        regulate_fps()

# MAIN UTILS ========================================================================================================================================

def check_parameters(parameters):
    # Check the parameters length
    if len(parameters) != 2:
        raise RuntimeError("Exactly two parameters are needed (user id, user trained side)")
    
    # Check the user trained side parameter
    if parameters[1] != "right" and parameters[1] != "left":
        raise RuntimeError("The user trained side parameter must be right or left")

def set_parameters(parameters):
    global USER_ID, USER_TRAINED_SIDE
    USER_ID = parameters[0]
    USER_TRAINED_SIDE = DataManager.SIDE_RIGHT if parameters[1] == "right" else DataManager.SIDE_LEFT

def set_utils():
    global GAME_CONTROLLER, CAMERA_READER, POSE_ESTIMATOR, DATA_MANAGER, DATA_FOLDER
    GAME_CONTROLLER = GameController(GAME_FPS, GAME_WIDTH, GAME_HEIGHT, WINDOW_NAME, WINDOW_ICON)
    CAMERA_READER = CameraReader(CAMERA_TYPE, CAMERA_WIDTH, CAMERA_HEIGHT)
    POSE_ESTIMATOR = PoseEstimator(POSE_MODEL_COMPLEXITY, POSE_MIN_VISIBILITY)
    DATA_FOLDER = DATA_FOLDER.format(user_id = USER_ID)
    DATA_MANAGER = DataManager(DATA_FOLDER)

def set_background():
    color = GameController.COLOR_BLACK
    GAME_CONTROLLER.set_background_color(color)

def create_landmarks():
    for landmark_id in PoseLandmark.get_landmarks():
        color = GameController.COLOR_BLUE
        radius = 10
        GAME_CONTROLLER.create_object_circle(landmark_id, 0, 0, color, radius)

def update_game_states():
    global GAME_RUNNING
    GAME_CONTROLLER.refresh_states()
    GAME_RUNNING = GAME_CONTROLLER.get_running_state() 

def get_image():
    # Read the camera
    result = CAMERA_READER.read()
    if not result: return None

    # Get the image
    result = CAMERA_READER.get_image()
    if result is None: return None
    image = result[0]
    
    return image

def get_landmarks(image):
    # Estimate the pose
    POSE_ESTIMATOR.set_image(image)
    result = POSE_ESTIMATOR.estimate()
    if not result: return None

    # Get the landmark coordinates
    landmarks = POSE_ESTIMATOR.get_landmarks()

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

def update_steps(landmarks_as_px):
    if STEP_CURRENT == STEP_CALIBRATION:
        update_step_calibration(landmarks_as_px)
    
    if STEP_CURRENT == STEP_PLAY:
        update_step_play(landmarks_as_px)

def update_landmarks(landmarks_as_px):
    # Update the landmarks
    for landmark_id in PoseLandmark.get_landmarks():
        px_landmark = landmarks_as_px.get(landmark_id)
        if px_landmark is None: continue
        GAME_CONTROLLER.update_object_circle(landmark_id, px_landmark[0], px_landmark[1], None, None)
    
    # Create the landmark connections
    for connection in PoseLandmark.get_connections():
        landmark_id1 = connection[0]
        landmark_id2 = connection[1]
        px_landmark1 = landmarks_as_px.get(landmark_id1)
        px_landmark2 = landmarks_as_px.get(landmark_id2)
        if px_landmark1 is None or px_landmark2 is None: continue
        
        color = GameController.COLOR_BLUE
        radius = 1
        GAME_CONTROLLER.create_object_line(None, px_landmark1[0], px_landmark1[1], px_landmark2[0], px_landmark2[1], color, radius)

def draw_canvas():
    GAME_CONTROLLER.refresh_screen()

def regulate_fps():
    GAME_CONTROLLER.regulate_fps()

# ===================================================================================================================================================

if __name__ == '__main__':
    try:
        parameters = sys.argv[1:] # The first parameter is the file name
        main(parameters)
    except KeyboardInterrupt:
        GAME_RUNNING = False
    finally:
        CAMERA_READER.close()
        POSE_ESTIMATOR.close()
        GAME_CONTROLLER.close()
        DATA_MANAGER.close()