import os
import random
import cloudpickle
import pandas
from collections import deque


class DifficulyAdapter:
    
    TYPE_RANDOM_BASED = 0
    TYPE_RULE_BASED = 1
    TYPE_DATA_BASED  = 2

    _TYPES = [
        TYPE_RANDOM_BASED,
        TYPE_RULE_BASED,
        TYPE_DATA_BASED,
    ]

    _PARAMETER_TYPE_NONE = -1
    _PARAMETER_TYPE_TARGET_DISTANCE = 0
    _PARAMETER_TYPE_TARGET_SIZE = 1
    _PARAMETER_TYPE_REACH_TIME = 2

    def __init__(self, type, pretrained_model_path, goal_score, margin_score, diff_start, diff_increment, window_size_score, window_size_metrics, folder, date):
        # Check the type
        if type not in DifficulyAdapter._TYPES: raise RuntimeError("The type does not exist")

        self._type = type
        self._pretrained_model_path = pretrained_model_path
        self._goal_score = goal_score
        self._margin_score = margin_score
        self._diff_start = diff_start
        self._diff_increment = diff_increment
        self._window_size_score = window_size_score
        self._window_size_metrics = window_size_metrics
        self._folder = folder
        self._date = date

        # Create the folder
        os.makedirs(folder, exist_ok=True) # Avoid already existing error

        # Set the file path
        if date is None:
            self._scores_file = os.path.join(folder, "scores.csv")
        else:
            self._scores_file = os.path.join(folder, date + "-scores.csv")

        # Generic DDA
        self._id = None

        self._n_targets = 0
        self._n_targets_succeeded = 0

        self._adjusted_parameter = None
        self._diff_target_distance = None
        self._diff_target_size = None
        self._diff_reach_time = None

        self._reach_iteration = None
        self._dwell_iteration = None
        
        self._target_succeeded = deque(maxlen=window_size_score)

        self._trunk_failed = deque(maxlen=window_size_metrics)
        self._reach_failed = deque(maxlen=window_size_metrics)
        self._dwell_failed = deque(maxlen=window_size_metrics)

        self._reach_wrist_number_of_velocity_peaks = deque(maxlen=window_size_metrics)
        self._reach_wrist_mean_velocity = deque(maxlen=window_size_metrics)
        self._reach_wrist_sparc = deque(maxlen=window_size_metrics)
        self._reach_wrist_jerk = deque(maxlen=window_size_metrics)
        self._reach_trunk_rom = deque(maxlen=window_size_metrics)
        self._reach_hand_path_ratio = deque(maxlen=window_size_metrics)
        self._has_dwell = deque(maxlen=window_size_metrics)
        self._dwell_wrist_mean_velocity = deque(maxlen=window_size_metrics)

        self._last_score = None
        self._last_window_score = None

        # Data-based DDA
        self._model = None
        self._scaler = None
        
        self._last_context = None
        self._last_context_scaled = None
        
        # Init DDA
        if type == DifficulyAdapter.TYPE_RANDOM_BASED:
            self._init_random_based()
        elif type == DifficulyAdapter.TYPE_RULE_BASED:
            self._init_rule_based()
        elif type == DifficulyAdapter.TYPE_DATA_BASED:
            self._init_data_based()

    def close(self):
        pass

    def _init_random_based(self):
        if self._pretrained_model_path is not None:
            raise RuntimeError("No pretrained model possible for random-based DDA")

    def _init_rule_based(self):
        if self._pretrained_model_path is not None:
            raise RuntimeError("No pretrained model possible for rule-based DDA")

    def _init_data_based(self):
        if self._pretrained_model_path is None:
            raise RuntimeError("A pretrained model is required for data-based DDA")
        
        with open(self._pretrained_model_path, "rb") as file:
            model = cloudpickle.load(file)
            self._model = model["model"]
            self._scaler = model["scaler"]

    def get_parameters(self, id):
        self._id = id

        # Get the start parameters
        diff_target_distance = self._diff_start
        diff_target_size = self._diff_start
        diff_reach_time = self._diff_start
        
        # It is the first call
        if self._n_targets == 0:
            self._adjusted_parameter = DifficulyAdapter._PARAMETER_TYPE_NONE
            self._diff_target_distance = diff_target_distance
            self._diff_target_size = diff_target_size
            self._diff_reach_time = diff_reach_time
            self._last_score = 0
            self._last_window_score = 0

            return [
                self._diff_target_distance,
                self._diff_target_size,
                self._diff_reach_time,
            ]

        # Compute the difficulty status (too hard, too easy, OK)
        score = self.get_score()
        window_score = self._get_window_score()
        too_hard = self._is_difficulty_too_high(window_score)
        too_easy = self._is_difficulty_too_low(window_score)

        # Get the parameter to adjust
        parameter = DifficulyAdapter._PARAMETER_TYPE_NONE
        if self._type == DifficulyAdapter.TYPE_RANDOM_BASED:
            parameter = self._get_random_based_parameter(too_hard, too_easy)
        elif self._type == DifficulyAdapter.TYPE_RULE_BASED:
            parameter = self._get_rule_based_parameter(too_hard, too_easy)
        elif self._type == DifficulyAdapter.TYPE_DATA_BASED:
            parameter = self._get_data_based_parameter(too_hard, too_easy)

        # Get the last parameters
        diff_target_distance = self._diff_target_distance
        diff_target_size = self._diff_target_size
        diff_reach_time = self._diff_reach_time

        # The difficulty is OK
        if not too_hard and not too_easy:
            if parameter != DifficulyAdapter._PARAMETER_TYPE_NONE: raise RuntimeError("The parameter to adjust must be none")
            
            self._adjusted_parameter = parameter
            self._diff_target_distance = diff_target_distance
            self._diff_target_size = diff_target_size
            self._diff_reach_time = diff_reach_time
            self._last_score = score
            self._last_window_score = window_score

            return [
                self._diff_target_distance,
                self._diff_target_size,
                self._diff_reach_time,
            ]

        # The difficulty is NOK
        diff_increment = -self._diff_increment if too_hard else self._diff_increment

        if parameter == DifficulyAdapter._PARAMETER_TYPE_TARGET_DISTANCE:
            diff_target_distance += diff_increment
            diff_target_distance = self._get_min_max_diff_value(diff_target_distance)
        elif parameter == DifficulyAdapter._PARAMETER_TYPE_TARGET_SIZE:
            diff_target_size += diff_increment
            diff_target_size = self._get_min_max_diff_value(diff_target_size)
        elif parameter == DifficulyAdapter._PARAMETER_TYPE_REACH_TIME:
            diff_reach_time += diff_increment
            diff_reach_time = self._get_min_max_diff_value(diff_reach_time)

        self._adjusted_parameter = parameter
        self._diff_target_distance = diff_target_distance
        self._diff_target_size = diff_target_size
        self._diff_reach_time = diff_reach_time
        self._last_score = score
        self._last_window_score = window_score

        return [
            self._diff_target_distance,
            self._diff_target_size,
            self._diff_reach_time,
        ]
    
    def set_results(self, reach_iteration, dwell_iteration, target_succeeded, trunk_failed, reach_failed, dwell_failed):
        self._reach_iteration = reach_iteration
        self._dwell_iteration = dwell_iteration

        self._target_succeeded.append(int(target_succeeded))
        self._trunk_failed.append(int(trunk_failed))
        self._reach_failed.append(int(reach_failed))
        self._dwell_failed.append(int(dwell_failed))

        self._reach_wrist_number_of_velocity_peaks.append(reach_iteration.wrist_number_of_velocity_peaks)
        self._reach_wrist_mean_velocity.append(reach_iteration.wrist_mean_velocity)
        self._reach_wrist_sparc.append(reach_iteration.wrist_sparc)
        self._reach_wrist_jerk.append(reach_iteration.wrist_jerk)
        self._reach_trunk_rom.append(reach_iteration.trunk_rom)
        self._reach_hand_path_ratio.append(reach_iteration.hand_path_ratio)

        has_dwell = 0 if dwell_iteration is None else 1
        dwell_wrist_mean_velocity = 0 if dwell_iteration is None else dwell_iteration.wrist_mean_velocity

        self._has_dwell.append(has_dwell)
        self._dwell_wrist_mean_velocity.append(dwell_wrist_mean_velocity)
        
        self._n_targets += 1
        if target_succeeded: self._n_targets_succeeded += 1

        # Write header
        if self._n_targets == 1: self._write_header()

        # Write data
        self._write_data()

    def _get_min_max_diff_value(self, value):
        value = min(value, 1.0)
        value = max(value, 0.0)
        
        # Avoid floating point rounding error
        epsilon = 1e-9
        if abs(value) < epsilon:
            value = 0.0
        elif abs(value - 1.0) < epsilon:
            value = 1.0

        return value
    
    def _get_random_based_parameter(self, too_hard, too_easy):
        # The difficulty is OK
        if not too_hard and not too_easy:
            return DifficulyAdapter._PARAMETER_TYPE_NONE

        # The difficulty is NOK
        parameters = [
            DifficulyAdapter._PARAMETER_TYPE_TARGET_DISTANCE,
            DifficulyAdapter._PARAMETER_TYPE_TARGET_SIZE,
            DifficulyAdapter._PARAMETER_TYPE_REACH_TIME,
        ]
        parameter = random.choice(parameters)

        return parameter

    def _get_rule_based_parameter(self, too_hard, too_easy):
        # The difficulty is OK
        if not too_hard and not too_easy:
            return DifficulyAdapter._PARAMETER_TYPE_NONE

        # The difficulty is NOK
        trunk_errors = self._get_window_metric_score(self._trunk_failed)
        dwell_errors = self._get_window_metric_score(self._dwell_failed)
        reach_errors = self._get_window_metric_score(self._reach_failed)

        key_distance = DifficulyAdapter._PARAMETER_TYPE_TARGET_DISTANCE
        key_size = DifficulyAdapter._PARAMETER_TYPE_TARGET_SIZE
        key_time = DifficulyAdapter._PARAMETER_TYPE_REACH_TIME

        errors = {
            key_distance : trunk_errors,
            key_size : dwell_errors,
            key_time : reach_errors,
        }

        parameter = DifficulyAdapter._PARAMETER_TYPE_NONE

        # The difficulty is too hard
        # One of the parameter need to be decreased
        # Filter the adjustable parameters (those that are not already at the minimum)
        # Choose the parameter attached to the worst performance metric
        # Choose randomly in case of a tie
        if too_hard:
            if self._diff_target_distance <= 0: del errors[key_distance]
            if self._diff_target_size <= 0: del errors[key_size]
            if self._diff_reach_time <= 0: del errors[key_time]
            
            if len(errors) >= 1:
                parameter = self._get_largest(errors)
                parameter = self._randomize_competitors(parameter, errors)
        
        # The difficulty is too easy
        # One of the parameter need to be increased
        # Filter the adjustable parameters (those that are not already at the maximum)
        # Choose the parameter attached to the best performance metric
        # Choose randomly in case of a tie
        elif too_easy:
            if self._diff_target_distance >= 1: del errors[key_distance]
            if self._diff_target_size >= 1: del errors[key_size]
            if self._diff_reach_time >= 1: del errors[key_time]

            if len(errors) >= 1:
                parameter = self._get_smallest(errors)
                parameter = self._randomize_competitors(parameter, errors)

        return parameter

    def _get_data_based_parameter(self, too_hard, too_easy):
        # The Contextual Bandits ran
        # Update the data scaler, the scaling parameters (mean and standard deviation per feature) change over time (as the data arrives one by one)
        # Update also the Contextual Bandits
        if self._adjusted_parameter != DifficulyAdapter._PARAMETER_TYPE_NONE:
            self._scaler.partial_fit(self._last_context)
            reward = self._get_window_score_improvement()
            self._model.partial_fit(decisions=[self._adjusted_parameter], rewards=[reward], contexts=self._last_context_scaled)

        # The difficulty is OK
        if not too_hard and not too_easy:
            return DifficulyAdapter._PARAMETER_TYPE_NONE

        # Get the context
        self._last_context = pandas.DataFrame([{
            "diff_target_distance" : self._diff_target_distance,
            "diff_target_size" : self._diff_target_size,
            "diff_reach_time" : self._diff_reach_time,
            "window_reach_wrist_number_of_velocity_peaks" : self._get_window_metric_score(self._reach_wrist_number_of_velocity_peaks),
            "window_reach_wrist_mean_velocity" : self._get_window_metric_score(self._reach_wrist_mean_velocity),
            "window_reach_wrist_sparc" : self._get_window_metric_score(self._reach_wrist_sparc),
            "window_reach_wrist_jerk" : self._get_window_metric_score(self._reach_wrist_jerk),
            "window_reach_trunk_rom" : self._get_window_metric_score(self._reach_trunk_rom),
            "window_reach_hand_path_ratio" : self._get_window_metric_score(self._reach_hand_path_ratio),
            "window_has_dwell" : self._get_window_metric_score(self._has_dwell),
            "window_dwell_wrist_mean_velocity" : self._get_window_metric_score(self._dwell_wrist_mean_velocity),
        }])

        # Normalize the context
        self._last_context_scaled = self._scaler.transform(self._last_context)

        # Choose the parameter to adjust (pull the arm)
        parameter = self._model.predict(self._last_context_scaled)

        return parameter

    def get_score(self):
        n_targets = self._n_targets
        n_successes = self._n_targets_succeeded
        score = n_successes / n_targets if n_targets > 0 else 0
        return score

    def get_str_score(self):
        n_targets = self._n_targets
        n_successes = self._n_targets_succeeded
        str_score = str(n_successes) + "/" + str(n_targets)
        return str_score

    def _get_window_score(self):
        score = self._get_window_metric_score(self._target_succeeded)
        return score
            
    def _get_window_metric_score(self, metric):
        total_metric = 0
        n_metric = 0
        for c_metric in metric:
            total_metric += c_metric
            n_metric += 1
        score = total_metric / n_metric if n_metric > 0 else 0
        return score

    def _get_window_score_improvement(self):
        improvement = abs(self._last_window_score - self._goal_score) - abs(self._get_window_score() - self._goal_score)
        return improvement
    
    def _get_score_improvement(self):
        improvement = abs(self._last_score - self._goal_score) - abs(self.get_score() - self._goal_score)
        return improvement

    def _is_difficulty_too_high(self, score):
        result = False
        if score < self._goal_score - self._margin_score: result = True
        return result
    
    def _is_difficulty_too_low(self, score):
        result = False
        if score > self._goal_score + self._margin_score: result = True
        return result
    
    def _get_largest(self, obj):
        largest_key = None
        largest_value = float("-inf")
        for key in obj:
            value = obj[key]
            if value > largest_value:
                largest_value = value
                largest_key = key
        return largest_key

    def _get_smallest(self, obj):
        smallest_key = None
        smallest_value = float("inf")
        for key in obj:
            value = obj[key]
            if value < smallest_value:
                smallest_value = value
                smallest_key = key
        return smallest_key

    def _randomize_competitors(self, key, obj):
        competitors = []
        ref_value = obj[key]
        for key in obj:
            value = obj[key]
            if value == ref_value:
                competitors.append(key)
        competitor = random.choice(competitors)
        return competitor

    def _write_header(self):
        # Get the header
        header = [
            "id", "start_timestamp", "end_timestamp",
            "dda_type", "goal_score", "margin_score", "diff_start", "diff_increment", "window_size_score", "window_size_metrics",
            "adjusted_parameter", "diff_target_distance", "diff_target_size", "diff_reach_time",
            "target_succeeded", "score", "score_improvement", "window_score", "window_score_improvement",
            "trunk_failed", "reach_failed", "dwell_failed",
            "window_trunk_failed", "window_reach_failed", "window_dwell_failed",
            "reach_wrist_number_of_velocity_peaks", "reach_wrist_mean_velocity", "reach_wrist_sparc", "reach_wrist_jerk", "reach_trunk_rom", "reach_hand_path_ratio", "has_dwell", "dwell_wrist_mean_velocity",
            "window_reach_wrist_number_of_velocity_peaks", "window_reach_wrist_mean_velocity", "window_reach_wrist_sparc", "window_reach_wrist_jerk", "window_reach_trunk_rom", "window_reach_hand_path_ratio", "window_has_dwell", "window_dwell_wrist_mean_velocity",
        ]
        header_str = ",".join(header)

        # Write the header
        with open(self._scores_file, "a") as file: file.write(header_str + "\n")

    def _write_data(self):
        # Get the start timestamp
        start_timestamp = self._reach_iteration.timestamp[0]

        # Get the end timestamp
        end_timestamp = self._reach_iteration.timestamp[-1] if self._dwell_iteration is None else self._dwell_iteration.timestamp[-1]

        # Get the reward
        score_improvement = self._get_score_improvement()
        window_score_improvement = self._get_window_score_improvement()

        # Get the line
        line = [
            self._id, start_timestamp, end_timestamp,
            self._type, self._goal_score, self._margin_score, self._diff_start, self._diff_increment, self._window_size_score, self._window_size_metrics,
            self._adjusted_parameter, self._diff_target_distance, self._diff_target_size, self._diff_reach_time,
            self._target_succeeded[-1], self.get_score(), score_improvement, self._get_window_score(), window_score_improvement,
            self._trunk_failed[-1], self._reach_failed[-1], self._dwell_failed[-1],
            self._get_window_metric_score(self._trunk_failed), self._get_window_metric_score(self._reach_failed), self._get_window_metric_score(self._dwell_failed),
            self._reach_wrist_number_of_velocity_peaks[-1], self._reach_wrist_mean_velocity[-1], self._reach_wrist_sparc[-1], self._reach_wrist_jerk[-1], self._reach_trunk_rom[-1], self._reach_hand_path_ratio[-1], self._has_dwell[-1], self._dwell_wrist_mean_velocity[-1],
            self._get_window_metric_score(self._reach_wrist_number_of_velocity_peaks), self._get_window_metric_score(self._reach_wrist_mean_velocity), self._get_window_metric_score(self._reach_wrist_sparc), self._get_window_metric_score(self._reach_wrist_jerk), self._get_window_metric_score(self._reach_trunk_rom), self._get_window_metric_score(self._reach_hand_path_ratio), self._get_window_metric_score(self._has_dwell), self._get_window_metric_score(self._dwell_wrist_mean_velocity),
        ]
        line_str = ",".join(str(data) for data in line)
        
        # Write the line
        with open(self._scores_file, "a") as file: file.write(line_str + "\n")