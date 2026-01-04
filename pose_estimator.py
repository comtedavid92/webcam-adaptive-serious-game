import mediapipe


class PoseLandmark:
    
    _MP_RIGHT_SHOULDER = 11
    _MP_LEFT_SHOULDER  = 12
    _MP_RIGHT_ELBOW    = 13
    _MP_LEFT_ELBOW     = 14
    _MP_RIGHT_WRIST    = 15
    _MP_LEFT_WRIST     = 16
    _MP_RIGHT_PINKY    = 17
    _MP_LEFT_PINKY     = 18
    _MP_RIGHT_INDEX    = 19
    _MP_LEFT_INDEX     = 20
    _MP_RIGHT_HIP      = 23
    _MP_LEFT_HIP       = 24

    RIGHT_SHOULDER     = 0
    LEFT_SHOULDER      = 1
    RIGHT_ELBOW        = 2
    LEFT_ELBOW         = 3
    RIGHT_WRIST        = 4
    LEFT_WRIST         = 5
    MIDDLE_HIP         = 6
    RIGHT_HAND         = 7
    LEFT_HAND          = 8
    MIDDLE_SHOULDER    = 9

    _LANDMARKS = [
        RIGHT_SHOULDER,
        LEFT_SHOULDER,
        RIGHT_ELBOW,
        LEFT_ELBOW,
        RIGHT_WRIST,
        LEFT_WRIST,
        MIDDLE_HIP,
        RIGHT_HAND,
        LEFT_HAND,
        MIDDLE_SHOULDER,
    ]

    _CONNECTIONS = [
        [MIDDLE_HIP, LEFT_SHOULDER],
        [LEFT_SHOULDER, LEFT_ELBOW],
        [LEFT_ELBOW, LEFT_WRIST],
        [LEFT_WRIST, LEFT_HAND],
        [LEFT_SHOULDER, MIDDLE_SHOULDER],
        [MIDDLE_SHOULDER, RIGHT_SHOULDER],
        [RIGHT_SHOULDER, RIGHT_ELBOW],
        [RIGHT_ELBOW, RIGHT_WRIST],
        [RIGHT_WRIST, RIGHT_HAND],
        [RIGHT_SHOULDER, MIDDLE_HIP],
    ]

    @staticmethod
    def is_valid(landmark):
        return landmark in PoseLandmark._LANDMARKS
    
    @staticmethod
    def get_landmarks():
        return PoseLandmark._LANDMARKS
    
    @staticmethod
    def get_connections():
        return PoseLandmark._CONNECTIONS


class PoseEstimator:

    MODEL_COMPLEXITY_FAST = 0
    MODEL_COMPLEXITY_BALANCED = 1
    MODEL_COMPLEXITY_ACCURATE = 2
    
    _MODEL_COMPLEXITIES = [
        MODEL_COMPLEXITY_FAST,
        MODEL_COMPLEXITY_BALANCED,
        MODEL_COMPLEXITY_ACCURATE,
    ]
    
    def __init__(self, model_complexity, min_visibility):
        self._model = None
        self._landmarks = None
        self._image = None
        self._min_visibility = min_visibility
    
        # Check the model complexity
        if model_complexity not in PoseEstimator._MODEL_COMPLEXITIES:
            raise RuntimeError("The model complexity does not exist")
        
        # Set the model
        self._model = mediapipe.solutions.pose.Pose(
            static_image_mode = False, # Video stream
            model_complexity = model_complexity
        )

    def close(self):
        # Release the model
        try: self._model.close()
        except: pass

    def set_image(self, image):
        # Set the image
        self._image = image

    def estimate(self):
        # Check the image
        if self._image is None: return False

        # Process the image
        result = self._model.process(self._image)
        if not result.pose_landmarks: return False

        # Set the landmarks
        self._landmarks = result.pose_landmarks.landmark
        return True

    def get_landmark(self, landmark):
        # Check the landmark type
        if not PoseLandmark.is_valid(landmark): raise RuntimeError("The landmark type does not exist")

        # Check the landmarks
        if self._landmarks is None: return None
        
        # Get the coordinates of the landmark
        result = None

        if landmark == PoseLandmark.RIGHT_SHOULDER:
            result = self._get_landmarks_mean([
                self._landmarks[PoseLandmark._MP_RIGHT_SHOULDER],
            ])
        elif landmark == PoseLandmark.LEFT_SHOULDER:
            result = self._get_landmarks_mean([
                self._landmarks[PoseLandmark._MP_LEFT_SHOULDER],
            ])
        elif landmark == PoseLandmark.RIGHT_ELBOW:
            result = self._get_landmarks_mean([
                self._landmarks[PoseLandmark._MP_RIGHT_ELBOW],
            ])
        elif landmark == PoseLandmark.LEFT_ELBOW:
            result = self._get_landmarks_mean([
                self._landmarks[PoseLandmark._MP_LEFT_ELBOW],
            ])
        elif landmark == PoseLandmark.RIGHT_WRIST:
            result = self._get_landmarks_mean([
                self._landmarks[PoseLandmark._MP_RIGHT_WRIST],
            ])
        elif landmark == PoseLandmark.LEFT_WRIST:
            result = self._get_landmarks_mean([
                self._landmarks[PoseLandmark._MP_LEFT_WRIST],
            ])
        elif landmark == PoseLandmark.MIDDLE_HIP:
            result = self._get_landmarks_mean([
                self._landmarks[PoseLandmark._MP_RIGHT_HIP],
                self._landmarks[PoseLandmark._MP_LEFT_HIP],
            ])
        elif landmark == PoseLandmark.RIGHT_HAND:
            result = self._get_landmarks_mean([
                self._landmarks[PoseLandmark._MP_RIGHT_WRIST],
                self._landmarks[PoseLandmark._MP_RIGHT_PINKY],
                self._landmarks[PoseLandmark._MP_RIGHT_INDEX],
            ])
        elif landmark == PoseLandmark.LEFT_HAND:
            result = self._get_landmarks_mean([
                self._landmarks[PoseLandmark._MP_LEFT_WRIST],
                self._landmarks[PoseLandmark._MP_LEFT_PINKY],
                self._landmarks[PoseLandmark._MP_LEFT_INDEX],
            ])
        elif landmark == PoseLandmark.MIDDLE_SHOULDER:
            result = self._get_landmarks_mean([
                self._landmarks[PoseLandmark._MP_LEFT_SHOULDER],
                self._landmarks[PoseLandmark._MP_RIGHT_SHOULDER],
            ])

        return result
    
    def get_landmarks(self):
        result = {}

        # Add the landmarks
        for landmark in PoseLandmark.get_landmarks():
            output = self.get_landmark(landmark)
            if output is None: continue
            result[landmark] = output

        return result

    def _get_landmarks_mean(self, landmarks):
        # Check the reliability
        for landmark in landmarks:
            if landmark.visibility < self._min_visibility:
                return None

        # Compute the mean
        result = [0, 0]
        for landmark in landmarks:
            result[0] = result[0] + landmark.x
            result[1] = result[1] + landmark.y

        size = len(landmarks)
        result[0] = result[0] / size
        result[1] = result[1] / size

        return result