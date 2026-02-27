import sys
import math
import time
import random
import datetime
from camera_reader import CameraReader
from pose_estimator import PoseEstimator, PoseLandmark
from game_controller import GameController
from data_manager import DataManager, DifficulyAdapter

# ===================================================================================================================================================

USER_ID                  = None
USER_TRAINED_SIDE        = None

GAME_CONTROLLER          = None
GAME_RUNNING             = True
GAME_FPS                 = 60
GAME_WIDTH               = 1600 # px
GAME_HEIGHT              = 1200 # px

WINDOW_NAME              = "webcam-adaptive-serious-game"
WINDOW_ICON              = "./docs/icon.png"

CAMERA_READER            = None
CAMERA_TYPE              = CameraReader.CAMERA_EXTERNAL
CAMERA_WIDTH             = 640 # px
CAMERA_HEIGHT            = 480 # px

POSE_ESTIMATOR           = None
POSE_MODEL_COMPLEXITY    = PoseEstimator.MODEL_COMPLEXITY_FAST
POSE_MIN_VISIBILITY      = 0.2
POSE_EXCLUDED_LANDMARKS  = [PoseLandmark.RIGHT_HAND, PoseLandmark.LEFT_HAND]
POSE_DUMMY_VARIABLE      = PoseLandmark.exclude_landmarks(POSE_EXCLUDED_LANDMARKS)

DATA_MANAGER             = None
DATA_FOLDER              = "./experiments/{user_id}/"
DATA_DATE                = datetime.datetime.now().strftime("%Y-%m-%d-%H-%M-%S")
DATA_REACH_TYPE          = 0
DATA_DWELL_TYPE          = 1

OBJ_LAND_RADIUS          = 10   # px
OBJ_LAND_WIDTH           = 1    # px
OBJ_LAND_COLOR           = GameController.COLOR_BLUE

OBJ_FIRST_TEXT_X         = 10   # px
OBJ_FIRST_TEXT_Y         = 10   # px
OBJ_SECOND_TEXT_X        = 10   # px
OBJ_SECOND_TEXT_Y        = 50   # px
OBJ_THIRD_TEXT_X         = 10   # px
OBJ_THIRD_TEXT_Y         = 90   # px
OBJ_TEXT_SIZE            = 40   # px
OBJ_TARGET_RADIUS        = 20   # px
OBJ_DWELL_TIME           = 1000 # ms

DIFF_ADAPTER             = None
DIFF_TYPE                = DifficulyAdapter.TYPE_RULE_BASED
DIFF_GOAL_SCORE          = 0.75
DIFF_MARGIN_SCORE        = 0.05

DIFF_MIN_TARGET_ANGLE    = 90   # degrees
DIFF_MAX_TARGET_ANGLE    = 210  # degrees
DIFF_MIN_TRUNK_ANGLE     = 0    # degrees
DIFF_MAX_TRUNK_ANGLE     = 5    # degrees 
DIFF_DWELL_TIME          = 1000 # ms

DIFF_MIN_TARGET_DISTANCE = 50   # px
DIFF_MAX_TARGET_DISTANCE = None # px
DIFF_MIN_TARGET_SIZE     = 10   # px
DIFF_MAX_TARGET_SIZE     = 50   # px
DIFF_MIN_REACH_TIME      = 500  # ms
DIFF_MAX_REACH_TIME      = 5000 # ms

MS_CURRENT_STEP          = 0
MS_CALIBRATION_STEP      = 0
MS_PLAY_STEP             = 1

MEMORY_CALIBRATION = {
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

MEMORY_PLAY = {
    "substep"              : 0,
    # Object ids
    "text_instr_id"        : 100,
    "text_score_id"        : 101,
    "text_dda_param_id"    : 102,
    "text_trunk_id"        : 103,
    "target_start_id"      : 104,
    "text_start_id"        : 105,
    "target_end_id"        : 106,
    "text_end_id"          : 107,
    # Events ids
    "event_start_id"       : 200,
    "event_expired_end_id" : 201,
    "event_contact_end_id" : 202,
    "event_dwell_end_id"   : 203,
    # Positions
    "norm_positions"       : [],
    "norm_position"        : None,
    "norm_distances"       : [],
    "norm_distance"        : None,
    "start_positions"      : [],
    "start_position"       : None,
    "end_position"         : None,
    # DDA difficulty parameters
    "dda_target_distance"  : 0,
    "dda_target_size"      : 0,
    "dda_reach_time"       : 0,
    "dda_target_angle"     : 0,
    # Game difficulty parameters
    "diff_target_distance" : 0,
    "diff_target_size"     : 0,
    "diff_reach_time"      : 0,
    "diff_target_angle"    : 0,
    # Scores
    "current_target_id"    : 0,
    "trunk_failed"         : False,
    "reach_failed"         : False,
    "dwell_failed"         : False,
    "target_succeeded"     : False,
}

# STATE MACHINE : calibration step ==================================================================================================================

def update_step_calibration(landmarks_as_px):
    global MEMORY_CALIBRATION, DIFF_MAX_TARGET_DISTANCE, MS_CURRENT_STEP

    # ========
    # Ask the user to align his shoulder and his hand on the targets
    # ========
    if MEMORY_CALIBRATION["substep"] == 0:
        # Instruction text
        side = "right" if USER_TRAINED_SIDE == DataManager.SIDE_RIGHT else "left"
        text = "Calibration step : please extend your " + side + " arm and align your shoulder and your hand on the targets"
        GAME_CONTROLLER.create_object_text(MEMORY_CALIBRATION["text_instr_id"], OBJ_FIRST_TEXT_X, OBJ_FIRST_TEXT_Y, GameController.COLOR_WHITE, text, OBJ_TEXT_SIZE)

        # Hand target
        hand_x = GAME_WIDTH - 400 if USER_TRAINED_SIDE == DataManager.SIDE_RIGHT else 400
        hand_y = GAME_HEIGHT / 2
        GAME_CONTROLLER.create_object_circle(MEMORY_CALIBRATION["target_hand_id"], hand_x, hand_y, GameController.COLOR_GREEN, OBJ_TARGET_RADIUS)

        # Shoulder target
        shoulder_x = hand_x - 500 if USER_TRAINED_SIDE == DataManager.SIDE_RIGHT else hand_x + 500
        shoulder_y = GAME_HEIGHT / 2
        GAME_CONTROLLER.create_object_circle(MEMORY_CALIBRATION["target_shoulder_id"], shoulder_x, shoulder_y, GameController.COLOR_GREEN, OBJ_TARGET_RADIUS)

        # Hand text
        hand_x = hand_x + OBJ_TARGET_RADIUS + 10
        GAME_CONTROLLER.create_object_text(MEMORY_CALIBRATION["text_hand_id"], hand_x, hand_y, GameController.COLOR_WHITE, "hand", OBJ_TEXT_SIZE)

        # Shoulder text
        shoulder_x = shoulder_x + OBJ_TARGET_RADIUS + 10
        GAME_CONTROLLER.create_object_text(MEMORY_CALIBRATION["text_shoulder_id"], shoulder_x, shoulder_y, GameController.COLOR_WHITE, "shoulder", OBJ_TEXT_SIZE)

        # Hand event
        landmark_id = PoseLandmark.RIGHT_WRIST if USER_TRAINED_SIDE == DataManager.SIDE_RIGHT else PoseLandmark.LEFT_WRIST
        GAME_CONTROLLER.create_event_dwell(MEMORY_CALIBRATION["event_hand_id"], MEMORY_CALIBRATION["target_hand_id"], landmark_id, OBJ_DWELL_TIME)
        
        # Shoulder event
        landmark_id = PoseLandmark.RIGHT_SHOULDER if USER_TRAINED_SIDE == DataManager.SIDE_RIGHT else PoseLandmark.LEFT_SHOULDER
        GAME_CONTROLLER.create_event_dwell(MEMORY_CALIBRATION["event_shoulder_id"], MEMORY_CALIBRATION["target_shoulder_id"], landmark_id, OBJ_DWELL_TIME)

        MEMORY_CALIBRATION["substep"] = 10
    
    # ========
    # Wait for the user to align his shoulder and his hand on the targets
    # ========
    elif MEMORY_CALIBRATION["substep"] == 10:
        # Events
        event_hand = GAME_CONTROLLER.get_event_continuous_state(MEMORY_CALIBRATION["event_hand_id"])
        event_shoulder = GAME_CONTROLLER.get_event_continuous_state(MEMORY_CALIBRATION["event_shoulder_id"])

        # Not aligned
        if not event_hand or not event_shoulder:
            MEMORY_CALIBRATION["max_distances"].clear()

        # Aligned
        else:
            # Hand and shoulder landmarks
            landmark_id = PoseLandmark.RIGHT_WRIST if USER_TRAINED_SIDE == DataManager.SIDE_RIGHT else PoseLandmark.LEFT_WRIST
            landmark_hand = landmarks_as_px.get(landmark_id)
            landmark_id = PoseLandmark.RIGHT_SHOULDER if USER_TRAINED_SIDE == DataManager.SIDE_RIGHT else PoseLandmark.LEFT_SHOULDER
            landmark_shoulder = landmarks_as_px.get(landmark_id)
            if landmark_hand is None or landmark_shoulder is None: return
            
            # Distance computation
            distance = get_landmarks_distance(landmark_hand, landmark_shoulder)
            MEMORY_CALIBRATION["max_distances"].append(distance)

            # Mean computation
            if len(MEMORY_CALIBRATION["max_distances"]) >= 10:
                DIFF_MAX_TARGET_DISTANCE = get_value_mean(MEMORY_CALIBRATION["max_distances"])
                GAME_CONTROLLER.delete_object(MEMORY_CALIBRATION["text_instr_id"])
                GAME_CONTROLLER.delete_object(MEMORY_CALIBRATION["target_hand_id"])
                GAME_CONTROLLER.delete_object(MEMORY_CALIBRATION["target_shoulder_id"])
                GAME_CONTROLLER.delete_object(MEMORY_CALIBRATION["text_hand_id"])
                GAME_CONTROLLER.delete_object(MEMORY_CALIBRATION["text_shoulder_id"])
                GAME_CONTROLLER.delete_event(MEMORY_CALIBRATION["event_hand_id"])
                GAME_CONTROLLER.delete_event(MEMORY_CALIBRATION["event_shoulder_id"])                
                MS_CURRENT_STEP = MS_PLAY_STEP

# STATE MACHINE : play step =========================================================================================================================

def update_step_play(landmarks_as_px):
    global MEMORY_PLAY, MS_CURRENT_STEP

    # ========
    # Run the DDA
    # ========
    if MEMORY_PLAY["substep"] == 0:
        # Target id
        MEMORY_PLAY["current_target_id"] = MEMORY_PLAY["current_target_id"] + 1

        # DDA parameters
        parameters = DIFF_ADAPTER.get_new_parameters(MEMORY_PLAY["current_target_id"])
        MEMORY_PLAY["dda_target_distance"] = parameters[0]
        MEMORY_PLAY["dda_target_size"] = parameters[1]
        MEMORY_PLAY["dda_reach_time"] = parameters[2]
        MEMORY_PLAY["dda_target_angle"] = random.random()

        # Game paremeters
        MEMORY_PLAY["diff_target_distance"] = get_value_scaled(DIFF_MIN_TARGET_DISTANCE, DIFF_MAX_TARGET_DISTANCE, MEMORY_PLAY["dda_target_distance"])
        MEMORY_PLAY["diff_target_size"] = get_value_scaled(DIFF_MIN_TARGET_SIZE, DIFF_MAX_TARGET_SIZE, 1 - MEMORY_PLAY["dda_target_size"])
        MEMORY_PLAY["diff_reach_time"] = get_value_scaled(DIFF_MIN_REACH_TIME, DIFF_MAX_REACH_TIME, 1 - MEMORY_PLAY["dda_reach_time"])
        
        angle = get_value_scaled(DIFF_MIN_TARGET_ANGLE, DIFF_MAX_TARGET_ANGLE, MEMORY_PLAY["dda_target_angle"])
        MEMORY_PLAY["diff_target_angle"] = angle if USER_TRAINED_SIDE == DataManager.SIDE_RIGHT else -angle

        # Flags
        MEMORY_PLAY["trunk_failed"] = False
        MEMORY_PLAY["reach_failed"] = False
        MEMORY_PLAY["dwell_failed"] = False
        MEMORY_PLAY["target_succeeded"] = False

        MEMORY_PLAY["substep"] = 10

    # ========
    # Ask the user to align his hand on the start target
    # ========
    elif MEMORY_PLAY["substep"] == 10:
        # Instruction text
        side = "right" if USER_TRAINED_SIDE == DataManager.SIDE_RIGHT else "left"
        text = "Play step : please align your " + side + " hand on the start target"
        GAME_CONTROLLER.create_object_text(MEMORY_PLAY["text_instr_id"], OBJ_FIRST_TEXT_X, OBJ_FIRST_TEXT_Y, GameController.COLOR_WHITE, text, OBJ_TEXT_SIZE)

        # Score text
        str_score = DIFF_ADAPTER.get_str_score()
        score = round(DIFF_ADAPTER.get_score() * 100, 1)
        text = "Score : " + str_score + " (" + str(score) + "%) "
        GAME_CONTROLLER.create_object_text(MEMORY_PLAY["text_score_id"], OBJ_THIRD_TEXT_X, OBJ_THIRD_TEXT_Y, GameController.COLOR_WHITE, text, OBJ_TEXT_SIZE)

        # Difficulty paramters text
        text = "Parameters : target distance {distance:.2f}, target size {size:.2f}, reach time {reach:.2f}"
        text = text.format(
            distance = MEMORY_PLAY["dda_target_distance"],
            size = MEMORY_PLAY["dda_target_size"],
            reach = MEMORY_PLAY["dda_reach_time"],
        )
        GAME_CONTROLLER.create_object_text(MEMORY_PLAY["text_dda_param_id"], OBJ_SECOND_TEXT_X, OBJ_SECOND_TEXT_Y, GameController.COLOR_WHITE, text, OBJ_TEXT_SIZE)

        # Trunk text
        GAME_CONTROLLER.create_object_text(MEMORY_PLAY["text_trunk_id"], 0, 0, GameController.COLOR_WHITE, "", OBJ_TEXT_SIZE)

        # Shoulder landmark
        landmark_id = PoseLandmark.RIGHT_SHOULDER if USER_TRAINED_SIDE == DataManager.SIDE_RIGHT else PoseLandmark.LEFT_SHOULDER
        shoulder_landmark = landmarks_as_px.get(landmark_id)
        if shoulder_landmark is None: return

        # Start target
        x = shoulder_landmark[0]
        y = shoulder_landmark[1]
        GAME_CONTROLLER.create_object_circle(MEMORY_PLAY["target_start_id"], x, y, GameController.COLOR_GREEN, OBJ_TARGET_RADIUS)

        # Start text
        x = x + OBJ_TARGET_RADIUS + 10
        GAME_CONTROLLER.create_object_text(MEMORY_PLAY["text_start_id"], x, y, GameController.COLOR_WHITE, "start", OBJ_TEXT_SIZE)

        # Start event
        landmark_id = PoseLandmark.RIGHT_WRIST if USER_TRAINED_SIDE == DataManager.SIDE_RIGHT else PoseLandmark.LEFT_WRIST
        GAME_CONTROLLER.create_event_dwell(MEMORY_PLAY["event_start_id"], MEMORY_PLAY["target_start_id"], landmark_id, OBJ_DWELL_TIME)

        MEMORY_PLAY["substep"] = 20

    # ========
    # Wait for the user to align his hand on the start target
    # ========
    elif MEMORY_PLAY["substep"] == 20:
        # Shoulder landmark
        landmark_id = PoseLandmark.RIGHT_SHOULDER if USER_TRAINED_SIDE == DataManager.SIDE_RIGHT else PoseLandmark.LEFT_SHOULDER
        shoulder_landmark = landmarks_as_px.get(landmark_id)
        if shoulder_landmark is None: return

        # Start target update
        x = shoulder_landmark[0]
        y = shoulder_landmark[1]
        GAME_CONTROLLER.update_object_circle(MEMORY_PLAY["target_start_id"], x, y, None, None)

        # Start text update
        x = x + OBJ_TARGET_RADIUS + 10
        GAME_CONTROLLER.update_object_text(MEMORY_PLAY["text_start_id"], x, y, None, None, None)

        # Event
        event = GAME_CONTROLLER.get_event_continuous_state(MEMORY_PLAY["event_start_id"])

        # Not aligned
        if not event:
            MEMORY_PLAY["norm_positions"].clear()
            MEMORY_PLAY["norm_distances"].clear()
            MEMORY_PLAY["start_positions"].clear()

        # Aligned
        else:
            # Neck and shoulders landmarks
            neck = landmarks_as_px.get(PoseLandmark.MIDDLE_SHOULDER)
            right_soulder_landmark = landmarks_as_px.get(PoseLandmark.RIGHT_SHOULDER)
            left_soulder_landmark = landmarks_as_px.get(PoseLandmark.LEFT_SHOULDER)
            if neck is None or right_soulder_landmark is None or left_soulder_landmark is None: return

            # Normalization position and distance
            norm_position = neck
            norm_distance = get_landmarks_distance(right_soulder_landmark, left_soulder_landmark)
            MEMORY_PLAY["norm_positions"].append(norm_position)
            MEMORY_PLAY["norm_distances"].append(norm_distance)
            MEMORY_PLAY["start_positions"].append(shoulder_landmark)

            # Mean computations
            if len(MEMORY_PLAY["norm_positions"]) >= 10:
                MEMORY_PLAY["norm_position"] = get_landmarks_mean(MEMORY_PLAY["norm_positions"])
                MEMORY_PLAY["norm_distance"] = get_value_mean(MEMORY_PLAY["norm_distances"])
                MEMORY_PLAY["start_position"] = get_landmarks_mean(MEMORY_PLAY["start_positions"])            
                GAME_CONTROLLER.delete_object(MEMORY_PLAY["target_start_id"])
                GAME_CONTROLLER.delete_object(MEMORY_PLAY["text_start_id"])
                GAME_CONTROLLER.delete_event(MEMORY_PLAY["event_start_id"])
                MEMORY_PLAY["substep"] = 30

    # ========
    # Ask the user to align his hand on the end target
    # ========
    elif MEMORY_PLAY["substep"] == 30:
        # Instruction text
        side = "right" if USER_TRAINED_SIDE == DataManager.SIDE_RIGHT else "left"
        text = "Play step : please align your " + side + " hand on the end target"
        GAME_CONTROLLER.update_object_text(MEMORY_PLAY["text_instr_id"], None, None, None, text, None)
        
        # End position
        MEMORY_PLAY["end_position"] = get_end_position(MEMORY_PLAY["start_position"], MEMORY_PLAY["diff_target_angle"], MEMORY_PLAY["diff_target_distance"])

        # End target
        x = MEMORY_PLAY["end_position"][0]
        y = MEMORY_PLAY["end_position"][1]
        GAME_CONTROLLER.create_object_circle(MEMORY_PLAY["target_end_id"], x, y, GameController.COLOR_GREEN, MEMORY_PLAY["diff_target_size"])

        # End text
        x = x + MEMORY_PLAY["diff_target_size"] + 10
        GAME_CONTROLLER.create_object_text(MEMORY_PLAY["text_end_id"], x, y, GameController.COLOR_WHITE, "", OBJ_TEXT_SIZE)

        # Expired event
        GAME_CONTROLLER.create_event_expired(MEMORY_PLAY["event_expired_end_id"], MEMORY_PLAY["target_end_id"], MEMORY_PLAY["diff_reach_time"])

        # Contact event
        landmark_id = PoseLandmark.RIGHT_WRIST if USER_TRAINED_SIDE == DataManager.SIDE_RIGHT else PoseLandmark.LEFT_WRIST
        GAME_CONTROLLER.create_event_contact(MEMORY_PLAY["event_contact_end_id"], MEMORY_PLAY["target_end_id"], landmark_id)

        # Iteration
        DATA_MANAGER.delete_last_iterations()
        DATA_MANAGER.start_iteration(USER_TRAINED_SIDE, DATA_REACH_TYPE, MEMORY_PLAY["current_target_id"])

        MEMORY_PLAY["substep"] = 40

    # ========
    # Wait for the user to align his hand on the end target
    # ========
    elif MEMORY_PLAY["substep"] == 40:
        # Data update
        enough_data = update_data(MEMORY_PLAY["target_end_id"], MEMORY_PLAY["end_position"], MEMORY_PLAY["norm_position"], MEMORY_PLAY["norm_distance"], landmarks_as_px)
        
        # Trunk text
        neck_landmark = landmarks_as_px.get(PoseLandmark.MIDDLE_SHOULDER)
        trunk_respected = update_trunk_text(MEMORY_PLAY["text_trunk_id"], neck_landmark)

        # End text
        time = GAME_CONTROLLER.get_event_expired_remaining_time_ms(MEMORY_PLAY["event_expired_end_id"])
        time = round(time / 1000, 1)
        text = "end | reach | " + str(time) + " s"
        GAME_CONTROLLER.update_object_text(MEMORY_PLAY["text_end_id"], None, None, None, text, None)

        # Events
        event_expired = GAME_CONTROLLER.get_event_continuous_state(MEMORY_PLAY["event_expired_end_id"])
        event_contact = GAME_CONTROLLER.get_event_continuous_state(MEMORY_PLAY["event_contact_end_id"])

        # Data check
        if not enough_data: return

        # Trunk not respected
        if not trunk_respected:
            MEMORY_PLAY["trunk_failed"] = True
        # Target expired
        elif event_expired:
            MEMORY_PLAY["reach_failed"] = True
        # Aligned
        elif event_contact:
            GAME_CONTROLLER.delete_event(MEMORY_PLAY["event_expired_end_id"])
            DATA_MANAGER.end_iteration()
            MEMORY_PLAY["substep"] = 50

        # Clear objects
        if not trunk_respected or event_expired:
            GAME_CONTROLLER.delete_object(MEMORY_PLAY["text_instr_id"])
            GAME_CONTROLLER.delete_object(MEMORY_PLAY["text_score_id"])
            GAME_CONTROLLER.delete_object(MEMORY_PLAY["text_dda_param_id"])
            GAME_CONTROLLER.delete_object(MEMORY_PLAY["text_trunk_id"])
            GAME_CONTROLLER.delete_object(MEMORY_PLAY["target_end_id"])
            GAME_CONTROLLER.delete_object(MEMORY_PLAY["text_end_id"])
            GAME_CONTROLLER.delete_event(MEMORY_PLAY["event_expired_end_id"])
            GAME_CONTROLLER.delete_event(MEMORY_PLAY["event_contact_end_id"])
            DATA_MANAGER.end_iteration()
            MEMORY_PLAY["substep"] = 70
        
    # ========
    # Ask the user to dwell with his hand on the end target
    # ========
    elif MEMORY_PLAY["substep"] == 50:
        # Instruction text
        side = "right" if USER_TRAINED_SIDE == DataManager.SIDE_RIGHT else "left"
        text = "Play step : please dwell with your " + side + " hand on the end target"
        GAME_CONTROLLER.update_object_text(MEMORY_PLAY["text_instr_id"], None, None, None, text, None)

        # End target
        GAME_CONTROLLER.update_object_circle(MEMORY_PLAY["target_end_id"], None, None, GameController.COLOR_GREEN, None)

        # Dwell event
        landmark_id = PoseLandmark.RIGHT_WRIST if USER_TRAINED_SIDE == DataManager.SIDE_RIGHT else PoseLandmark.LEFT_WRIST
        GAME_CONTROLLER.create_event_dwell(MEMORY_PLAY["event_dwell_end_id"], MEMORY_PLAY["target_end_id"], landmark_id, DIFF_DWELL_TIME)

        # Iteration
        DATA_MANAGER.start_iteration(USER_TRAINED_SIDE, DATA_DWELL_TYPE, MEMORY_PLAY["current_target_id"])

        MEMORY_PLAY["substep"] = 60

    # ========
    # Wait for the user to dwell with his hand on the end target
    # ========
    elif MEMORY_PLAY["substep"] == 60:
        # Data update
        enough_data = update_data(MEMORY_PLAY["target_end_id"], MEMORY_PLAY["end_position"], MEMORY_PLAY["norm_position"], MEMORY_PLAY["norm_distance"], landmarks_as_px)
        
        # Trunk text
        neck_landmark = landmarks_as_px.get(PoseLandmark.MIDDLE_SHOULDER)
        trunk_respected = update_trunk_text(MEMORY_PLAY["text_trunk_id"], neck_landmark)

        # End text
        time = GAME_CONTROLLER.get_event_dwell_remaining_time_ms(MEMORY_PLAY["event_dwell_end_id"])
        time = round(time / 1000, 1)
        text = "end | dwell | " + str(time) + " s"
        GAME_CONTROLLER.update_object_text(MEMORY_PLAY["text_end_id"], None, None, None, text, None)

        # Events
        event_contact = GAME_CONTROLLER.get_event_continuous_state(MEMORY_PLAY["event_contact_end_id"])
        event_dwell = GAME_CONTROLLER.get_event_continuous_state(MEMORY_PLAY["event_dwell_end_id"])

        # Data check
        if not enough_data: return

        # Trunk not respected
        if not trunk_respected:
            MEMORY_PLAY["trunk_failed"] = True
        # Contact lost
        elif not event_contact:
            MEMORY_PLAY["dwell_failed"] = True
        # Dwelled
        elif event_dwell:
            MEMORY_PLAY["target_succeeded"] = True

        # Clear objects
        if not trunk_respected or not event_contact or event_dwell:
            GAME_CONTROLLER.delete_object(MEMORY_PLAY["text_instr_id"])
            GAME_CONTROLLER.delete_object(MEMORY_PLAY["text_score_id"])
            GAME_CONTROLLER.delete_object(MEMORY_PLAY["text_dda_param_id"])
            GAME_CONTROLLER.delete_object(MEMORY_PLAY["text_trunk_id"])
            GAME_CONTROLLER.delete_object(MEMORY_PLAY["target_end_id"])
            GAME_CONTROLLER.delete_object(MEMORY_PLAY["text_end_id"])
            GAME_CONTROLLER.delete_event(MEMORY_PLAY["event_contact_end_id"])
            GAME_CONTROLLER.delete_event(MEMORY_PLAY["event_dwell_end_id"])
            DATA_MANAGER.end_iteration()
            MEMORY_PLAY["substep"] = 70
    
    # ========
    # Update the DDA
    # ========
    elif MEMORY_PLAY["substep"] == 70:
        last_reach_iteration = DATA_MANAGER.get_last_iteration(DATA_REACH_TYPE)
        last_dwell_iteration = DATA_MANAGER.get_last_iteration(DATA_DWELL_TYPE)
        DIFF_ADAPTER.set_previous_kinematics_and_scores(
            last_reach_iteration, last_dwell_iteration, MEMORY_PLAY["target_succeeded"],
            MEMORY_PLAY["trunk_failed"], MEMORY_PLAY["reach_failed"], MEMORY_PLAY["dwell_failed"]
        )
            
        MEMORY_PLAY["substep"] = 0

# STATE MACHINES : utility functions ================================================================================================================

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
        if output is None: continue
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
        if landmark is None: return False
    
    # Add the data
    timestamp = time.time()
    enough_data = DATA_MANAGER.add_data(
        timestamp, neck[0], neck[1], hip[0], hip[1], shoulder[0], shoulder[1], elbow[0],
        elbow[1], wrist[0], wrist[1], end_effector[0], end_effector[1], target[0], target[1]
    )
    
    return enough_data

def update_trunk_text(text_trunk_id, neck_landmark):
    if neck_landmark is None: return True

    trunk_displacement = round(DATA_MANAGER.get_trunk_displacement(), 1)
    trunk_respected = trunk_displacement <= DIFF_MAX_TRUNK_ANGLE
    
    x = neck_landmark[0]
    y = neck_landmark[1] + OBJ_LAND_RADIUS + 10
    text = "trunk | " + str(trunk_displacement) + "° | max " + str(DIFF_MAX_TRUNK_ANGLE) + "°"
    GAME_CONTROLLER.update_object_text(text_trunk_id, x, y, None, text, None)

    return trunk_respected

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

# MAIN : utility functions ==========================================================================================================================

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
    global GAME_CONTROLLER, CAMERA_READER, POSE_ESTIMATOR, DATA_MANAGER, DATA_FOLDER, DIFF_ADAPTER
    GAME_CONTROLLER = GameController(GAME_FPS, GAME_WIDTH, GAME_HEIGHT, WINDOW_NAME, WINDOW_ICON)
    CAMERA_READER = CameraReader(CAMERA_TYPE, CAMERA_WIDTH, CAMERA_HEIGHT)
    POSE_ESTIMATOR = PoseEstimator(POSE_MODEL_COMPLEXITY, POSE_MIN_VISIBILITY)
    DATA_FOLDER = DATA_FOLDER.format(user_id = USER_ID)
    DATA_MANAGER = DataManager(DATA_FOLDER, DATA_DATE)
    DIFF_ADAPTER = DifficulyAdapter(DIFF_TYPE, DIFF_GOAL_SCORE, DIFF_MARGIN_SCORE, DATA_FOLDER, DATA_DATE)

def set_background():
    color = GameController.COLOR_BLACK
    GAME_CONTROLLER.set_background_color(color)

def create_landmarks():
    for landmark_id in PoseLandmark.get_landmarks():
        GAME_CONTROLLER.create_object_circle(landmark_id, 0, 0, OBJ_LAND_COLOR, OBJ_LAND_RADIUS)

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
    if MS_CURRENT_STEP == MS_CALIBRATION_STEP:
        update_step_calibration(landmarks_as_px)
    
    if MS_CURRENT_STEP == MS_PLAY_STEP:
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
        GAME_CONTROLLER.create_object_line(None, px_landmark1[0], px_landmark1[1], px_landmark2[0], px_landmark2[1], OBJ_LAND_COLOR, OBJ_LAND_WIDTH)

def draw_canvas():
    GAME_CONTROLLER.refresh_screen()

def regulate_fps():
    GAME_CONTROLLER.regulate_fps()

# ===================================================================================================================================================

if __name__ == "__main__":
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