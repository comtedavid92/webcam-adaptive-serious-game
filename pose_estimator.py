import mediapipe as mp


class PoseLandmark:
    
    RIGHT_SHOULDER   = 11
    LEFT_SHOULDER    = 12
    RIGHT_ELBOW      = 13
    LEFT_ELBOW       = 14
    RIGHT_WRIST      = 15
    LEFT_WRIST       = 16
    RIGHT_PINKY      = 17 # For proxies computation only
    LEFT_PINKY       = 18 # For proxies computation only
    RIGHT_INDEX      = 19 # For proxies computation only
    LEFT_INDEX       = 20 # For proxies computation only
    RIGHT_HIP        = 23
    LEFT_HIP         = 24
    PROXY_MIDDLE_HIP = 25
    PROXY_RIGHT_HAND = 26
    PROXY_LEFT_HAND  = 27
    PROXY_NECK       = 28

    _LANDMARKS = [
        RIGHT_SHOULDER,
        LEFT_SHOULDER,
        RIGHT_ELBOW,
        LEFT_ELBOW,
        RIGHT_WRIST,
        LEFT_WRIST,
        RIGHT_HIP,
        LEFT_HIP,
        PROXY_MIDDLE_HIP,
        PROXY_RIGHT_HAND,
        PROXY_LEFT_HAND,
        PROXY_NECK,
    ]

    _CONNECTIONS = [
        [LEFT_HIP, LEFT_SHOULDER       ],
        [LEFT_SHOULDER, LEFT_ELBOW     ],
        [LEFT_ELBOW, LEFT_WRIST        ],
        [LEFT_WRIST, PROXY_LEFT_HAND   ],
        [LEFT_SHOULDER, PROXY_NECK     ],
        [PROXY_NECK, RIGHT_SHOULDER    ],
        [RIGHT_SHOULDER, RIGHT_ELBOW   ],
        [RIGHT_ELBOW, RIGHT_WRIST      ],
        [RIGHT_WRIST, PROXY_RIGHT_HAND ],
        [RIGHT_SHOULDER, RIGHT_HIP     ],
        [RIGHT_HIP, PROXY_MIDDLE_HIP   ],
        [PROXY_MIDDLE_HIP, LEFT_HIP    ],
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
        self._min_visibility = 0
    
        # Check the model complexity
        if model_complexity not in PoseEstimator._MODEL_COMPLEXITIES:
            raise RuntimeError("The model complexity does not exist")
        
        # Set the model
        self._model = mp.solutions.pose.Pose(
            static_image_mode = False, # Video stream
            model_complexity = model_complexity
        )

        # Set the min visibility
        self._min_visibility = min_visibility

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

        # PROXY_MIDDLE_HIP
        if landmark == PoseLandmark.PROXY_MIDDLE_HIP:
            result = self._get_landmarks_mean([
                self._landmarks[PoseLandmark.RIGHT_HIP],
                self._landmarks[PoseLandmark.LEFT_HIP],
            ])

        # PROXY RIGHT HAND
        elif landmark == PoseLandmark.PROXY_RIGHT_HAND:
            result = self._get_landmarks_mean([
                self._landmarks[PoseLandmark.RIGHT_WRIST],
                self._landmarks[PoseLandmark.RIGHT_PINKY],
                self._landmarks[PoseLandmark.RIGHT_INDEX],
            ])

        # PROXY LEFT HAND
        elif landmark == PoseLandmark.PROXY_LEFT_HAND:
            result = self._get_landmarks_mean([
                self._landmarks[PoseLandmark.LEFT_WRIST],
                self._landmarks[PoseLandmark.LEFT_PINKY],
                self._landmarks[PoseLandmark.LEFT_INDEX],
            ])

        # PROXY NECK
        elif landmark == PoseLandmark.PROXY_NECK:
            result = self._get_landmarks_mean([
                self._landmarks[PoseLandmark.LEFT_SHOULDER],
                self._landmarks[PoseLandmark.RIGHT_SHOULDER],
            ])

        # LANDMARK
        else:
            output = self._landmarks[landmark]

            # Check the reliability
            if output.visibility < self._min_visibility:
                return None
            
            result = [output.x, output.y, output.z,]

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
        result = [0, 0, 0]
        for landmark in landmarks:
            result[0] = result[0] + landmark.x
            result[1] = result[1] + landmark.y
            result[2] = result[2] + landmark.z

        size = len(landmarks)
        result[0] = result[0] / size
        result[1] = result[1] / size
        result[2] = result[2] / size

        return result