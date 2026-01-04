import numpy
import ckatool
import datetime
import os


class _DataIteration:

    def __init__(self):
        self.side = []
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

        self.target_error_distance = 0
        self.hand_path_ratio = 0


class DataManager:

    SIDE_RIGHT = 0
    SIDE_LEFT  = 1

    _SIDES = [
        SIDE_RIGHT,
        SIDE_LEFT,
    ]
    
    def __init__(self, folder):
        self._iteration_number = 0
        self._iteration_side = 0
        self._iteration = None

        # Create the folder
        os.makedirs(folder, exist_ok=True) # Avoid already existing error

        # Set the file paths
        date = datetime.datetime.now().strftime('%Y-%m-%d-%H-%M-%S')
        self._coordinates_file = os.path.join(folder, date + "-coordinates.csv")
        self._kinematics_file = os.path.join(folder, date + "-kinematics.csv")

    def close(self):
        pass

    def start_iteration(self, side):
        # Check the side
        if side not in DataManager._SIDES: raise RuntimeError("The side does not exist")

        # Check the iteration
        it = self._iteration
        if it is not None: raise RuntimeError("The iteration already exists")

        # Set the iteration
        self._iteration_number = self._iteration_number + 1
        self._iteration_side = side
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

        self._iteration = None # Unset the iteration

    def add_data(self, timestamp, neck_x, neck_y, hip_x, hip_y, shoulder_x, shoulder_y, elbow_x,
                 elbow_y, wrist_x, wrist_y, end_effector_x, end_effector_y, target_x, target_y):
        # Check the iteration
        it = self._iteration
        if it is None: raise RuntimeError("The iteration does not exist")

        # Add the data
        it.side.append(self._iteration_side)
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

    def _compute_kinematics(self, neck, hip, shoulder, elbow, wrist, end_effector, target):
        neck.calculate_trunk_angle(hip, [0, -1, 0])

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

        it.trunk_rom = numpy.nanmax(neck.trunk_angle) - numpy.nanmin(neck.trunk_angle)
        it.shoulder_rom = numpy.nanmax(shoulder.angle) - numpy.nanmin(shoulder.angle)
        it.elbow_rom = numpy.nanmax(elbow.angle) - numpy.nanmin(elbow.angle)

        it.target_error_distance = end_effector.target_error_distance[it_nbr]
        it.hand_path_ratio = end_effector.hand_path_ratio[it_nbr]

    def _write_coordinates_header(self):
        # Get the header
        header = [
            "side", "iteration", "timestamp",
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
                    it.side[i], it.iteration[i], it.timestamp[i],
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
            "side", "iteration",
            "shoulder_number_of_velocity_peaks", "elbow_number_of_velocity_peaks", "wrist_number_of_velocity_peaks",
            "shoulder_ratio_mean_peak_velocity", "elbow_ratio_mean_peak_velocity", "wrist_ratio_mean_peak_velocity",
            "shoulder_mean_velocity", "elbow_mean_velocity", "wrist_mean_velocity",
            "shoulder_peak_velocity", "elbow_peak_velocity", "wrist_peak_velocity",
            "shoulder_sparc", "elbow_sparc", "wrist_sparc",
            "shoulder_jerk", "elbow_jerk", "wrist_jerk",
            "shoulder_movement_time", "elbow_movement_time", "wrist_movement_time",
            "shoulder_percentage_time_to_peak_velocity", "elbow_percentage_time_to_peak_velocity", "wrist_percentage_time_to_peak_velocity",
            "trunk_rom", "shoulder_rom", "elbow_rom",
            "target_error_distance", "hand_path_ratio"
        ]
        header_str = ",".join(header)

        # Write the header
        with open(self._kinematics_file, "a") as file: file.write(header_str + "\n")

    def _write_kinematics_data(self, it):
        # Get the line
        line = [
            it.side[0], it.iteration[0],
            it.shoulder_number_of_velocity_peaks, it.elbow_number_of_velocity_peaks, it.wrist_number_of_velocity_peaks,
            it.shoulder_ratio_mean_peak_velocity, it.elbow_ratio_mean_peak_velocity, it.wrist_ratio_mean_peak_velocity,
            it.shoulder_mean_velocity, it.elbow_mean_velocity, it.wrist_mean_velocity,
            it.shoulder_peak_velocity, it.elbow_peak_velocity, it.wrist_peak_velocity,
            it.shoulder_sparc, it.elbow_sparc, it.wrist_sparc,
            it.shoulder_jerk, it.elbow_jerk, it.wrist_jerk,
            it.shoulder_movement_time, it.elbow_movement_time, it.wrist_movement_time,
            it.shoulder_percentage_time_to_peak_velocity, it.elbow_percentage_time_to_peak_velocity, it.wrist_percentage_time_to_peak_velocity,
            it.trunk_rom, it.shoulder_rom, it.elbow_rom,
            it.target_error_distance, it.hand_path_ratio,
        ]
        line_str = ",".join(str(data) for data in line)
        
        # Write the line
        with open(self._kinematics_file, "a") as file: file.write(line_str + "\n")