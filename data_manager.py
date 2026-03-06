import numpy
import ckatool
import datetime
import os
import random

from contextualbandits.online import BootstrappedUCB
from sklearn.linear_model import SGDClassifier, SGDRegressor


class _DataIteration:

    def __init__(self):
        self.side = []
        self.type = []
        self.id = []
        self.iteration = []
        self.timestamp = []
        self.neck_x = []
        self.neck_y = []
        self.neck_z = []
        self.hip_x = []
        self.hip_y = []
        self.hip_z = []
        self.shoulder_x = []
        self.shoulder_y = []
        self.shoulder_z = []
        self.elbow_x = []
        self.elbow_y = []
        self.elbow_z = []
        self.wrist_x = []
        self.wrist_y = []
        self.wrist_z = []
        self.end_effector_x = []
        self.end_effector_y = []
        self.end_effector_z = []
        self.target_x = []
        self.target_y = []
        self.target_z = []

        self.shoulder_number_of_velocity_peaks = 0
        self.elbow_number_of_velocity_peaks = 0
        self.wrist_number_of_velocity_peaks = 0

        self.shoulder_ratio_mean_peak_velocity = 0
        self.elbow_ratio_mean_peak_velocity = 0
        self.wrist_ratio_mean_peak_velocity = 0

        self.shoulder_mean_velocity = 0
        self.elbow_mean_velocity = 0
        self.wrist_mean_velocity = 0

        self.shoulder_peak_velocity = 0
        self.elbow_peak_velocity = 0
        self.wrist_peak_velocity = 0

        self.shoulder_sparc = 0
        self.elbow_sparc = 0
        self.wrist_sparc = 0

        self.shoulder_jerk = 0
        self.elbow_jerk = 0
        self.wrist_jerk = 0

        self.shoulder_movement_time = 0
        self.elbow_movement_time = 0
        self.wrist_movement_time = 0

        self.shoulder_percentage_time_to_peak_velocity = 0
        self.elbow_percentage_time_to_peak_velocity = 0
        self.wrist_percentage_time_to_peak_velocity = 0

        self.trunk_rom = 0
        self.shoulder_rom = 0
        self.elbow_rom = 0

        self.trunk_displacement = 0
        self.shoulder_displacement = 0
        self.elbow_displacement = 0

        self.target_error_distance = 0
        self.hand_path_ratio = 0


class DataManager:

    SIDE_RIGHT = 0
    SIDE_LEFT  = 1

    _SIDES = [
        SIDE_RIGHT,
        SIDE_LEFT,
    ]
    
    def __init__(self, folder, date = None):
        self._iteration_number = 0
        self._iteration_side = 0
        self._iteration_type = 0
        self._iteration_id = 0
        self._iteration = None
        self._last_iterations = {}

        # Create the folder
        os.makedirs(folder, exist_ok=True) # Avoid already existing error

        # Set the file paths
        if date is None: date = datetime.datetime.now().strftime("%Y-%m-%d-%H-%M-%S")
        self._coordinates_file = os.path.join(folder, date + "-coordinates.csv")
        self._kinematics_file = os.path.join(folder, date + "-kinematics.csv")

        # Set the reference vector, for the computation of the trunk compensation
        self._reference = [0, -1, 0]

        # Set the minimum data, for the computation of kinematics, as CKATool crashes when there is not enough data
        self._min_data = 16

    def close(self):
        pass

    def start_iteration(self, side, type = 0, id = 0):
        # Check the side
        if side not in DataManager._SIDES: raise RuntimeError("The side does not exist")

        # Check the iteration
        it = self._iteration
        if it is not None: raise RuntimeError("The iteration already exists")

        # Set the iteration
        self._iteration_number = self._iteration_number + 1
        self._iteration_side = side
        self._iteration_type = type
        self._iteration_id = id
        self._iteration = _DataIteration()

    def end_iteration(self):
        # Check the iteration
        it = self._iteration
        it_nbr = self._iteration_number
        if it is None: raise RuntimeError("The iteration does not exist")

        # Check the data
        if len(it.iteration) == 0: raise RuntimeError("The iteration contains no data")
        
        # Create the CKATool objects
        side = "right" if self._iteration_side == DataManager.SIDE_RIGHT else "left"
        neck = ckatool.Neck(it.timestamp, it.neck_x, it.neck_y, it.neck_z, it.iteration)
        hip = ckatool.Hip(it.timestamp, it.hip_x, it.hip_y, it.hip_z, it.iteration)
        shoulder = ckatool.Shoulder(it.timestamp, it.shoulder_x, it.shoulder_y, it.shoulder_z, it.iteration, side)
        elbow = ckatool.Elbow(it.timestamp, it.elbow_x, it.elbow_y, it.elbow_z, it.iteration, side)
        wrist = ckatool.Wrist(it.timestamp, it.wrist_x, it.wrist_y, it.wrist_z, it.iteration, side)
        end_effector = ckatool.EndEffector(it.timestamp, it.end_effector_x, it.end_effector_y, it.end_effector_z, it.iteration)
        target = ckatool.Target(it.timestamp, it.target_x, it.target_y, it.target_z, it.iteration)

        # Compute the kinematics
        self._compute_kinematics(neck, hip, shoulder, elbow, wrist, end_effector, target)
        self._save_kinematics(it, it_nbr, neck, hip, shoulder, elbow, wrist, end_effector, target)
        
        # Write the headers
        if self._iteration_number == 1:
            self._write_coordinates_header()
            self._write_kinematics_header()

        # Write the data
        self._write_coordinates_data(it)
        self._write_kinematics_data(it)

        self._last_iterations[self._iteration_type] = self._iteration # Save the iteration
        self._iteration = None # Unset the iteration

    def get_last_iteration(self, type = 0):
        last_iteration = self._last_iterations.get(type)
        return last_iteration

    def delete_last_iterations(self):
        self._last_iterations = {}

    def add_data(self, timestamp, neck_x, neck_y, hip_x, hip_y, shoulder_x, shoulder_y, elbow_x,
                 elbow_y, wrist_x, wrist_y, end_effector_x, end_effector_y, target_x, target_y):
        # Check the iteration
        it = self._iteration
        if it is None: raise RuntimeError("The iteration does not exist")

        # Add the data
        it.side.append(self._iteration_side)
        it.type.append(self._iteration_type)
        it.id.append(self._iteration_id)
        it.iteration.append(self._iteration_number)
        it.timestamp.append(timestamp)
        it.neck_x.append(neck_x)
        it.neck_y.append(neck_y)
        it.neck_z.append(0)
        it.hip_x.append(hip_x)
        it.hip_y.append(hip_y)
        it.hip_z.append(0)
        it.shoulder_x.append(shoulder_x)
        it.shoulder_y.append(shoulder_y)
        it.shoulder_z.append(0)
        it.elbow_x.append(elbow_x)
        it.elbow_y.append(elbow_y)
        it.elbow_z.append(0)
        it.wrist_x.append(wrist_x)
        it.wrist_y.append(wrist_y)
        it.wrist_z.append(0)
        it.end_effector_x.append(end_effector_x)
        it.end_effector_y.append(end_effector_y)
        it.end_effector_z.append(0)
        it.target_x.append(target_x)
        it.target_y.append(target_y)
        it.target_z.append(0)

        # Check the number of data
        number_of_data = len(self._iteration.side)
        enough_data = number_of_data >= self._min_data

        return enough_data

    def get_trunk_displacement(self):
        # Check the iteration
        it = self._iteration
        if it is None: raise RuntimeError("The iteration does not exist")

        # Check the data
        if len(it.iteration) <= 1: return 0
        
        # Get a subset of the data
        timestamp = [it.timestamp[0], it.timestamp[-1]]
        iteration = [it.iteration[0], it.iteration[-1]]
        neck_x = [it.neck_x[0], it.neck_x[-1]]
        neck_y = [it.neck_y[0], it.neck_y[-1]]
        neck_z = [it.neck_z[0], it.neck_z[-1]]
        hip_x = [it.hip_x[0], it.hip_x[-1]]
        hip_y = [it.hip_y[0], it.hip_y[-1]]
        hip_z = [it.hip_z[0], it.hip_z[-1]]

        # Create the CKATool objects
        neck = ckatool.Neck(timestamp, neck_x, neck_y, neck_z, iteration)
        hip = ckatool.Hip(timestamp, hip_x, hip_y, hip_z, iteration)

        # Compute the trunk displacement
        neck.calculate_trunk_angle(hip, self._reference)
        trunk_displacement = abs(neck.trunk_angle[-1] - neck.trunk_angle[0])

        return trunk_displacement

    def _compute_kinematics(self, neck, hip, shoulder, elbow, wrist, end_effector, target):
        neck.calculate_trunk_angle(hip, self._reference)

        shoulder.calculate_speed_profile(elbow, neck, hip)
        shoulder.calculate_acceleration_profile()
        shoulder.calculate_zero_crossings()
        shoulder.count_number_of_velocity_peaks()
        shoulder.calculate_ratio_mean_peak_velocity()
        shoulder.calculate_mean_velocity()
        shoulder.calculate_peak_velocity()
        shoulder.calculate_sparc()
        shoulder.calculate_jerk()
        shoulder.calculate_movement_time()
        shoulder.calculate_percentage_time_to_peak_velocity()

        elbow.calculate_speed_profile(wrist, shoulder)
        elbow.calculate_acceleration_profile()
        elbow.calculate_zero_crossings()
        elbow.count_number_of_velocity_peaks()
        elbow.calculate_ratio_mean_peak_velocity()
        elbow.calculate_mean_velocity()
        elbow.calculate_peak_velocity()
        elbow.calculate_sparc()
        elbow.calculate_jerk()
        elbow.calculate_movement_time()
        elbow.calculate_percentage_time_to_peak_velocity()

        wrist.calculate_speed_profile()
        wrist.calculate_acceleration_profile()
        wrist.calculate_zero_crossings()
        wrist.count_number_of_velocity_peaks()
        wrist.calculate_ratio_mean_peak_velocity()
        wrist.calculate_mean_velocity()
        wrist.calculate_peak_velocity()
        wrist.calculate_sparc()
        wrist.calculate_jerk()
        wrist.calculate_movement_time()
        wrist.calculate_percentage_time_to_peak_velocity()

        end_effector.calculate_target_error_distance(target)
        end_effector.calculate_hand_path_ratio(target)

    def _save_kinematics(self, it, it_nbr, neck, hip, shoulder, elbow, wrist, end_effector, target):
        it.shoulder_number_of_velocity_peaks = shoulder.number_of_velocity_peaks[it_nbr]
        it.elbow_number_of_velocity_peaks = elbow.number_of_velocity_peaks[it_nbr]
        it.wrist_number_of_velocity_peaks = wrist.number_of_velocity_peaks[it_nbr]

        it.shoulder_ratio_mean_peak_velocity = shoulder.ratio_mean_peak_velocity[it_nbr]
        it.elbow_ratio_mean_peak_velocity = elbow.ratio_mean_peak_velocity[it_nbr]
        it.wrist_ratio_mean_peak_velocity = wrist.ratio_mean_peak_velocity[it_nbr]

        it.shoulder_mean_velocity = shoulder.mean_velocity[it_nbr]
        it.elbow_mean_velocity = elbow.mean_velocity[it_nbr]
        it.wrist_mean_velocity = wrist.mean_velocity[it_nbr]

        it.shoulder_peak_velocity = shoulder.peak_velocity[it_nbr]
        it.elbow_peak_velocity = elbow.peak_velocity[it_nbr]
        it.wrist_peak_velocity = wrist.peak_velocity[it_nbr]

        it.shoulder_sparc = shoulder.sparc[it_nbr]
        it.elbow_sparc = elbow.sparc[it_nbr]
        it.wrist_sparc = wrist.sparc[it_nbr]

        it.shoulder_jerk = shoulder.jerk[it_nbr]
        it.elbow_jerk = elbow.jerk[it_nbr]
        it.wrist_jerk = wrist.jerk[it_nbr]

        it.shoulder_movement_time = shoulder.movement_time[it_nbr]
        it.elbow_movement_time = elbow.movement_time[it_nbr]
        it.wrist_movement_time = wrist.movement_time[it_nbr]

        it.shoulder_percentage_time_to_peak_velocity = shoulder.percentage_time_to_peak_velocity[it_nbr]
        it.elbow_percentage_time_to_peak_velocity = elbow.percentage_time_to_peak_velocity[it_nbr]
        it.wrist_percentage_time_to_peak_velocity = wrist.percentage_time_to_peak_velocity[it_nbr]

        it.trunk_rom = numpy.max(neck.trunk_angle) - numpy.min(neck.trunk_angle)
        it.shoulder_rom = numpy.max(shoulder.angle) - numpy.min(shoulder.angle)
        it.elbow_rom = numpy.max(elbow.angle) - numpy.min(elbow.angle)

        it.trunk_displacement = numpy.absolute(neck.trunk_angle[-1] - neck.trunk_angle[0])
        it.shoulder_displacement = numpy.absolute(shoulder.angle[-1] - shoulder.angle[0])
        it.elbow_displacement = numpy.absolute(elbow.angle[-1] - elbow.angle[0])

        it.target_error_distance = end_effector.target_error_distance[it_nbr]
        it.hand_path_ratio = end_effector.hand_path_ratio[it_nbr]

    def _write_coordinates_header(self):
        # Get the header
        header = [
            "side", "type", "id", "iteration", "timestamp",
            "neck_x", "neck_y", "neck_z",
            "hip_x", "hip_y", "hip_z",
            "shoulder_x", "shoulder_y", "shoulder_z",
            "elbow_x", "elbow_y", "elbow_z",
            "wrist_x", "wrist_y", "wrist_z",
            "end_effector_x", "end_effector_y", "end_effector_z",
            "target_x", "target_y", "target_z"
        ]
        header_str = ",".join(header)

        # Write the header
        with open(self._coordinates_file, "a") as file: file.write(header_str + "\n")

    def _write_coordinates_data(self, it):
        with open(self._coordinates_file, "a") as file:
            i = 0
            while i < len(it.iteration):
                # Get the line
                line = [
                    it.side[i], it.type[i], it.id[i], it.iteration[i], it.timestamp[i],
                    it.neck_x[i], it.neck_y[i], it.neck_z[i],
                    it.hip_x[i], it.hip_y[i], it.hip_z[i],
                    it.shoulder_x[i], it.shoulder_y[i], it.shoulder_z[i],
                    it.elbow_x[i], it.elbow_y[i], it.elbow_z[i],
                    it.wrist_x[i], it.wrist_y[i], it.wrist_z[i],
                    it.end_effector_x[i], it.end_effector_y[i], it.end_effector_z[i],
                    it.target_x[i], it.target_y[i], it.target_z[i]
                ]
                line_str = ",".join(str(data) for data in line)
                                
                # Write the line
                file.write(line_str + "\n")

                i = i + 1

    def _write_kinematics_header(self):
        # Get the header
        header = [
            "side", "type", "id", "iteration", "start_timestamp", "end_timestamp",
            "shoulder_number_of_velocity_peaks", "elbow_number_of_velocity_peaks", "wrist_number_of_velocity_peaks",
            "shoulder_ratio_mean_peak_velocity", "elbow_ratio_mean_peak_velocity", "wrist_ratio_mean_peak_velocity",
            "shoulder_mean_velocity", "elbow_mean_velocity", "wrist_mean_velocity",
            "shoulder_peak_velocity", "elbow_peak_velocity", "wrist_peak_velocity",
            "shoulder_sparc", "elbow_sparc", "wrist_sparc",
            "shoulder_jerk", "elbow_jerk", "wrist_jerk",
            "shoulder_movement_time", "elbow_movement_time", "wrist_movement_time",
            "shoulder_percentage_time_to_peak_velocity", "elbow_percentage_time_to_peak_velocity", "wrist_percentage_time_to_peak_velocity",
            "trunk_rom", "shoulder_rom", "elbow_rom",
            "trunk_displacement", "shoulder_displacement", "elbow_displacement",
            "target_error_distance", "hand_path_ratio"
        ]
        header_str = ",".join(header)

        # Write the header
        with open(self._kinematics_file, "a") as file: file.write(header_str + "\n")

    def _write_kinematics_data(self, it):
        # Get the line
        line = [
            it.side[0], it.type[0], it.id[0], it.iteration[0], it.timestamp[0], it.timestamp[-1],
            it.shoulder_number_of_velocity_peaks, it.elbow_number_of_velocity_peaks, it.wrist_number_of_velocity_peaks,
            it.shoulder_ratio_mean_peak_velocity, it.elbow_ratio_mean_peak_velocity, it.wrist_ratio_mean_peak_velocity,
            it.shoulder_mean_velocity, it.elbow_mean_velocity, it.wrist_mean_velocity,
            it.shoulder_peak_velocity, it.elbow_peak_velocity, it.wrist_peak_velocity,
            it.shoulder_sparc, it.elbow_sparc, it.wrist_sparc,
            it.shoulder_jerk, it.elbow_jerk, it.wrist_jerk,
            it.shoulder_movement_time, it.elbow_movement_time, it.wrist_movement_time,
            it.shoulder_percentage_time_to_peak_velocity, it.elbow_percentage_time_to_peak_velocity, it.wrist_percentage_time_to_peak_velocity,
            it.trunk_rom, it.shoulder_rom, it.elbow_rom,
            it.trunk_displacement, it.shoulder_displacement, it.elbow_displacement,
            it.target_error_distance, it.hand_path_ratio,
        ]
        line_str = ",".join(str(data) for data in line)
        
        # Write the line
        with open(self._kinematics_file, "a") as file: file.write(line_str + "\n")


class DifficulyAdapter:
    
    TYPE_RANDOM_BASED = 0
    TYPE_RULE_BASED = 1
    TYPE_DATA_BASED  = 2

    _TYPES = [
        TYPE_RANDOM_BASED,
        TYPE_RULE_BASED,
        TYPE_DATA_BASED,
    ]

    def __init__(self, type, goal_score, margin_score, folder, date = None):
        # Check the type
        if type not in DifficulyAdapter._TYPES: raise RuntimeError("The type does not exist")

        self._type = type
        self._goal_score = goal_score
        self._margin_score = margin_score
        self._diff_increment = 0.05
        self._window_size = 10
        self._start_diff = 0.5

        self._id = []
        self._diff_target_distance = []
        self._diff_target_size = []
        self._diff_reach_time = []
        self._reach_iteration = []
        self._dwell_iteration = []
        self._target_succeeded = []
        self._trunk_failed = []
        self._reach_failed = []
        self._dwell_failed = []

        # Data-based DDA
        self._last_score = None
        self._last_parameter = None
        self._last_context = None
        self._contextual_bandits = None
        
        if type == DifficulyAdapter.TYPE_DATA_BASED:
            model = SGDClassifier(
                loss = "log_loss",        # Binary prediction
                learning_rate = "optimal" # Adaptative learning rate
            )

            self._contextual_bandits = BootstrappedUCB(
                base_algorithm = model,
                nchoices = 3,        # Number of arms
                nsamples = 10,       # Number of boostrap models per arms
                batch_train = True   # How to update (here, after each new data)
            )

            # The initial fit seems to be necessary to create the model properly
            # The three arms are pulled once, without any reward, in order to avoid any bias
            # https://nbviewer.org/github/david-cortes/contextualbandits/blob/master/example/online_contextual_bandits.ipynb

            context_size = 11
            first_batch = numpy.zeros((3, context_size)) # Matrix of 3x11 values
            action_chosen = numpy.array([0, 1, 2])       # Vector of three values
            rewards_received = numpy.array([0, 0, 0])    # Vector of three values
            self._contextual_bandits.fit(first_batch, action_chosen, rewards_received)

        # Create the folder
        os.makedirs(folder, exist_ok=True) # Avoid already existing error

        # Set the file path
        if date is None: date = datetime.datetime.now().strftime("%Y-%m-%d-%H-%M-%S")
        self._scores_file = os.path.join(folder, date + "-scores.csv")

    def get_new_parameters(self, id):
        parameters = [0, 0, 0]
        self._id.append(id)

        if self._type == DifficulyAdapter.TYPE_RANDOM_BASED:
            parameters = self._get_random_based_parameters()
        elif self._type == DifficulyAdapter.TYPE_RULE_BASED:
            parameters = self._get_rule_based_parameters()
        elif self._type == DifficulyAdapter.TYPE_DATA_BASED:
            parameters = self._get_data_based_parameters()

        return parameters
        
    def set_previous_kinematics_and_scores(self, reach_iteration, dwell_iteration, target_succeeded, trunk_failed, reach_failed, dwell_failed):
        self._reach_iteration.append(reach_iteration)
        self._dwell_iteration.append(dwell_iteration)

        self._target_succeeded.append(target_succeeded)
        self._trunk_failed.append(trunk_failed)
        self._reach_failed.append(reach_failed)
        self._dwell_failed.append(dwell_failed)

        # Write header
        if len(self._id) == 1: self._write_header()

        # Write data
        self._write_data()

    def get_score(self):
        n_targets = len(self._target_succeeded)
        n_successes = self._target_succeeded.count(True)
        score = n_successes / n_targets if n_targets > 0 else 0
        return score

    def get_str_score(self):
        n_targets = len(self._target_succeeded)
        n_successes = self._target_succeeded.count(True)
        str_score = str(n_successes) + "/" + str(n_targets)
        return str_score
    
    def _get_window_score(self):
        window_size = self._window_size
        target_succeeded = self._target_succeeded[-window_size:]
        n_targets = len(target_succeeded)
        n_successes = target_succeeded.count(True)
        score = n_successes / n_targets if n_targets > 0 else 0
        return score

    def _get_random_based_parameters(self):
        diff_target_distance = random.random()
        diff_target_size = random.random()
        diff_reach_time = random.random()
        
        self._diff_target_distance.append(diff_target_distance)
        self._diff_target_size.append(diff_target_size)
        self._diff_reach_time.append(diff_reach_time)

        return [diff_target_distance, diff_target_size, diff_reach_time]

    def _get_rule_based_parameters(self):
        # Get the start parameters
        diff_target_distance = self._start_diff
        diff_target_size = self._start_diff
        diff_reach_time = self._start_diff
        
        # It is the first call
        # Return the start parameters
        if len(self._diff_target_distance) == 0:
            self._diff_target_distance.append(diff_target_distance)
            self._diff_target_size.append(diff_target_size)
            self._diff_reach_time.append(diff_reach_time)

            return [
                self._diff_target_distance[-1],
                self._diff_target_size[-1],
                self._diff_reach_time[-1],
            ]

        # Get the last parameters
        diff_target_distance = self._diff_target_distance[-1]
        diff_target_size = self._diff_target_size[-1]
        diff_reach_time = self._diff_reach_time[-1]

        # Compute the difficulty status (too hard, too easy, OK)
        score = self._get_window_score()
        too_hard = self._is_difficulty_too_high(score)
        too_easy = self._is_difficulty_too_low(score)
        
        # The difficulty is OK
        # Return the last parameters
        if not too_hard and not too_easy:
            self._diff_target_distance.append(diff_target_distance)
            self._diff_target_size.append(diff_target_size)
            self._diff_reach_time.append(diff_reach_time)

            return [
                self._diff_target_distance[-1],
                self._diff_target_size[-1],
                self._diff_reach_time[-1],
            ]

        # Compute the performance metrics (that are not kinematics)
        # Construct an errors dict for later use
        trunk_errors = self._trunk_failed[-self._window_size:].count(True)
        reach_errors = self._reach_failed[-self._window_size:].count(True)
        dwell_errors = self._dwell_failed[-self._window_size:].count(True)

        key_trunk = 0
        key_reach = 1
        key_dwell = 2

        errors = {
            key_trunk : trunk_errors,
            key_reach : reach_errors,
            key_dwell : dwell_errors,
        }

        # The difficulty is too hard
        # One of the parameter need to be decreased
        # Filter the adjustable parameters (those that are not already at the minimum)
        # Decrease the parameter attached to the worst performance metric
        # Choose randomly in case of a tie
        if too_hard:
            if diff_target_distance <= 0: del errors[key_trunk]
            if diff_reach_time <= 0: del errors[key_reach]
            if diff_target_size <= 0: del errors[key_dwell]
            
            if len(errors) >= 1:
                curr_key = self._get_largest(errors)
                curr_key = self._randomize_competitors(curr_key, errors)
                if curr_key == key_trunk:
                    diff_target_distance -= self._diff_increment
                elif curr_key == key_reach:
                    diff_reach_time -= self._diff_increment
                elif curr_key == key_dwell:
                    diff_target_size -= self._diff_increment
        
        # The difficulty is too easy
        # One of the parameter need to be increased
        # Filter the adjustable parameters (those that are not already at the maximum)
        # Increase the parameter attached to the best performance metric
        # Choose randomly in case of a tie
        elif too_easy:
            if diff_target_distance >= 1: del errors[key_trunk]
            if diff_reach_time >= 1: del errors[key_reach]
            if diff_target_size >= 1: del errors[key_dwell]

            if len(errors) >= 1:
                curr_key = self._get_smallest(errors)
                curr_key = self._randomize_competitors(curr_key, errors)
                if curr_key == key_trunk:
                    diff_target_distance += self._diff_increment
                elif curr_key == key_reach:
                    diff_reach_time += self._diff_increment
                elif curr_key == key_dwell:
                    diff_target_size += self._diff_increment

        # Limit the parameters between 0 and 1
        diff_target_distance = min(diff_target_distance, 1)
        diff_target_size = min(diff_target_size, 1)
        diff_reach_time = min(diff_reach_time, 1)

        diff_target_distance = max(diff_target_distance, 0)
        diff_target_size = max(diff_target_size, 0)
        diff_reach_time = max(diff_reach_time, 0)

        # Return the new parameters
        self._diff_target_distance.append(diff_target_distance)
        self._diff_target_size.append(diff_target_size)
        self._diff_reach_time.append(diff_reach_time)

        return [
            self._diff_target_distance[-1],
            self._diff_target_size[-1],
            self._diff_reach_time[-1],
        ]

    def _get_data_based_parameters(self):
        # Get the start parameters
        diff_target_distance = self._start_diff
        diff_target_size = self._start_diff
        diff_reach_time = self._start_diff
        
        # It is the first call
        # Return the start parameters
        if len(self._diff_target_distance) == 0:
            self._diff_target_distance.append(diff_target_distance)
            self._diff_target_size.append(diff_target_size)
            self._diff_reach_time.append(diff_reach_time)

            return [
                self._diff_target_distance[-1],
                self._diff_target_size[-1],
                self._diff_reach_time[-1],
            ]
        
        # The contextual bandits ran
        # Update it with the reward
        # Partial fit is used because the contextual bandits is updated after each new data (online learning)
        if self._last_parameter is not None:
            reward = abs(self._last_score - self._goal_score) - abs(self._get_window_score() - self._goal_score)
            reward = 1 if reward > 0 else 0
            self._contextual_bandits.partial_fit(self._last_context, numpy.array([self._last_parameter]), numpy.array([reward]))

        # Reset the contextual bandits variables
        self._last_score = None
        self._last_parameter = None
        self._last_context = None

        # Get the last parameters
        diff_target_distance = self._diff_target_distance[-1]
        diff_target_size = self._diff_target_size[-1]
        diff_reach_time = self._diff_reach_time[-1]

        # Compute the difficulty status (too hard, too easy, OK)
        score = self._get_window_score()
        too_hard = self._is_difficulty_too_high(score)
        too_easy = self._is_difficulty_too_low(score)
        
        # The difficulty is OK
        # Return the last parameters
        if not too_hard and not too_easy:
            self._diff_target_distance.append(diff_target_distance)
            self._diff_target_size.append(diff_target_size)
            self._diff_reach_time.append(diff_reach_time)

            return [
                self._diff_target_distance[-1],
                self._diff_target_size[-1],
                self._diff_reach_time[-1],
            ]

        # Get the context as :
        #   diff_target_distance, diff_target_size, diff_reach_time
        #   reach_wrist_number_of_velocity_peaks, reach_wrist_mean_velocity, reach_wrist_sparc, reach_wrist_jerk, reach_trunk_rom, reach_hand_path_ratio
        #   has_dwell, dwell_wrist_mean_velocity
        # !!!!!!!! Important, if the context changes, the context_size variable in the constructor has to be adapted !!!!!!!!

        self._last_score = self._get_window_score()
        self._last_context = numpy.array([
            self._diff_target_distance[-1],
            self._diff_target_size[-1],
            self._diff_reach_time[-1],
            self._reach_iteration[-1].wrist_number_of_velocity_peaks,
            self._reach_iteration[-1].wrist_mean_velocity,
            self._reach_iteration[-1].wrist_sparc,
            self._reach_iteration[-1].wrist_jerk,
            self._reach_iteration[-1].trunk_rom,
            self._reach_iteration[-1].hand_path_ratio,
            0 if self._dwell_iteration[-1] is None else 1,
            0 if self._dwell_iteration[-1] is None else self._dwell_iteration[-1].wrist_mean_velocity,
        ])

        # Reshape the context
        # Convert a vector (N,1) to (1,N)
        self._last_context = self._last_context.reshape(1, -1)

        # Choose the parameter to adjust
        self._last_parameter = self._contextual_bandits.predict(self._last_context)[0]

        # Adjust the chosen parameter
        if too_hard:
            if self._last_parameter == 0: diff_target_distance -= self._diff_increment
            elif self._last_parameter == 1: diff_reach_time -= self._diff_increment
            elif self._last_parameter == 2: diff_target_size -= self._diff_increment
        elif too_easy:
            if self._last_parameter == 0: diff_target_distance += self._diff_increment
            elif self._last_parameter == 1: diff_reach_time += self._diff_increment
            elif self._last_parameter == 2: diff_target_size += self._diff_increment

        # Limit the parameters between 0 and 1
        diff_target_distance = min(diff_target_distance, 1)
        diff_target_size = min(diff_target_size, 1)
        diff_reach_time = min(diff_reach_time, 1)

        diff_target_distance = max(diff_target_distance, 0)
        diff_target_size = max(diff_target_size, 0)
        diff_reach_time = max(diff_reach_time, 0)

        # Return the new parameters
        self._diff_target_distance.append(diff_target_distance)
        self._diff_target_size.append(diff_target_size)
        self._diff_reach_time.append(diff_reach_time)

        return [
            self._diff_target_distance[-1],
            self._diff_target_size[-1],
            self._diff_reach_time[-1],
        ]

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
            "dda_type", "goal_score", "margin_score", "start_diff", "diff_increment", "window_size",
            "diff_target_distance", "diff_target_size", "diff_reach_time",
            "diff_target_distance_updated", "diff_target_size_updated", "diff_reach_time_updated",
            "target_succeeded", "trunk_failed", "reach_failed", "dwell_failed",
            "score", "n_trunk_failed", "n_reach_failed", "n_dwell_failed",
            "window_score", "window_n_trunk_failed", "window_n_reach_failed", "window_n_dwell_failed",
            "reach_wrist_number_of_velocity_peaks", "reach_wrist_mean_velocity", "reach_wrist_sparc", "reach_wrist_jerk", "reach_trunk_rom", "reach_hand_path_ratio",
            "has_dwell", "dwell_wrist_mean_velocity",
        ]
        header_str = ",".join(header)

        # Write the header
        with open(self._scores_file, "a") as file: file.write(header_str + "\n")

    def _write_data(self):
        # Get the start timestamp
        start_timestamp = self._reach_iteration[-1].timestamp[0]

        # Get the end timestamp
        end_timestamp = self._reach_iteration[-1].timestamp[-1] if self._dwell_iteration[-1] is None else self._dwell_iteration[-1].timestamp[-1]

        # Get the updated difficulty parameters
        diff_target_distance_updated = 0
        diff_target_size_updated = 0
        diff_reach_time_updated = 0

        if len(self._diff_target_distance) >= 2:
            diff_target_distance_updated = 1 if self._diff_target_distance[-1] != self._diff_target_distance[-2] else 0
            diff_target_size_updated = 1 if self._diff_target_size[-1] != self._diff_target_size[-2] else 0
            diff_reach_time_updated = 1 if self._diff_reach_time[-1] != self._diff_reach_time[-2] else 0

        # Get the reach kinematics
        reach_wrist_number_of_velocity_peaks = self._reach_iteration[-1].wrist_number_of_velocity_peaks
        reach_wrist_mean_velocity = self._reach_iteration[-1].wrist_mean_velocity
        reach_wrist_sparc = self._reach_iteration[-1].wrist_sparc
        reach_wrist_jerk = self._reach_iteration[-1].wrist_jerk
        reach_trunk_rom = self._reach_iteration[-1].trunk_rom
        reach_hand_path_ratio = self._reach_iteration[-1].hand_path_ratio
        
        # Get the dwell kinematic
        has_dwell = 0 if self._dwell_iteration[-1] is None else 1
        dwell_wrist_mean_velocity = 0 if self._dwell_iteration[-1] is None else self._dwell_iteration[-1].wrist_mean_velocity

        # Get the line
        line = [
            self._id[-1], start_timestamp, end_timestamp,
            self._type, self._goal_score, self._margin_score, self._start_diff, self._diff_increment, self._window_size,
            self._diff_target_distance[-1], self._diff_target_size[-1], self._diff_reach_time[-1],
            diff_target_distance_updated, diff_target_size_updated, diff_reach_time_updated,
            int(self._target_succeeded[-1]), int(self._trunk_failed[-1]), int(self._reach_failed[-1]), int(self._dwell_failed[-1]),
            self.get_score(), self._trunk_failed.count(True), self._reach_failed.count(True), self._dwell_failed.count(True),
            self._get_window_score(), self._trunk_failed[-self._window_size:].count(True), self._reach_failed[-self._window_size:].count(True), self._dwell_failed[-self._window_size:].count(True),
            reach_wrist_number_of_velocity_peaks, reach_wrist_mean_velocity, reach_wrist_sparc, reach_wrist_jerk, reach_trunk_rom, reach_hand_path_ratio,
            has_dwell, dwell_wrist_mean_velocity,
        ]
        line_str = ",".join(str(data) for data in line)
        
        # Write the line
        with open(self._scores_file, "a") as file: file.write(line_str + "\n")