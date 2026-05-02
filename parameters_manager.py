import json
import os


class ParametersManager:
    
    def __init__(self, folder, date):
        self._parameters = None

        # Create the folder
        os.makedirs(folder, exist_ok=True) # Avoid already existing error

        # Set the file path
        if date is None:
            self._parameters_file = os.path.join(folder, "parameters.json")
        else:
            self._parameters_file = os.path.join(folder, date + "-parameters.json")

    def close(self):
        pass

    def save_parameters(
            self,
            user_id, user_trained_side,
            game_width, game_height, game_fps,
            camera_type, camera_width, camera_height, camera_fps,
            pose_model_complexity, pose_min_visibility, pose_excluded_landmarks,
            data_ref_vector, data_folder, data_date,
            diff_type, diff_pretrained_model, diff_goal_score, diff_margin_score, diff_start, diff_increment, diff_window_size_score, diff_window_size_metrics,
            diff_min_target_angle, diff_max_target_angle, diff_max_trunk_angle, diff_dwell_time,
            diff_min_target_distance, diff_max_target_distance, diff_min_target_size, diff_max_target_size, diff_min_reach_time, diff_max_reach_time
        ):
        # Set the parameters
        self._parameters = {
            "user_id": user_id,
            "user_trained_side": user_trained_side,
            "game_width": game_width,
            "game_height": game_height,
            "game_fps": game_fps,
            "camera_type": camera_type,
            "camera_width": camera_width,
            "camera_height": camera_height,
            "camera_fps": camera_fps,
            "pose_model_complexity": pose_model_complexity,
            "pose_min_visibility": pose_min_visibility,
            "pose_excluded_landmarks": pose_excluded_landmarks,
            "data_ref_vector": data_ref_vector,
            "data_folder": data_folder,
            "data_date": data_date,
            "diff_type": diff_type,
            "diff_pretrained_model": diff_pretrained_model,
            "diff_goal_score": diff_goal_score,
            "diff_margin_score": diff_margin_score,
            "diff_start": diff_start,
            "diff_increment": diff_increment,
            "diff_window_size_score": diff_window_size_score,
            "diff_window_size_metrics": diff_window_size_metrics,
            "diff_min_target_angle": diff_min_target_angle,
            "diff_max_target_angle": diff_max_target_angle,
            "diff_max_trunk_angle": diff_max_trunk_angle,
            "diff_dwell_time": diff_dwell_time,
            "diff_min_target_distance": diff_min_target_distance,
            "diff_max_target_distance": diff_max_target_distance,
            "diff_min_target_size": diff_min_target_size,
            "diff_max_target_size": diff_max_target_size,
            "diff_min_reach_time": diff_min_reach_time,
            "diff_max_reach_time": diff_max_reach_time,
        }

        # Save the parameters
        # Indent : add line breaks and indentation
        with open(self._parameters_file, "w") as file:
            json.dump(self._parameters, file, indent=4)

    def get_parameters(self):
        return self._parameters
    
    def get_parameters_from_file(self, path):
        parameters = {}
        with open(path, "r") as f:
            parameters = json.load(f)
        return parameters