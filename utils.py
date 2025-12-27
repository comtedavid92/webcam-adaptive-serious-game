

class Utils:

    @staticmethod
    def to_px_landmarks(landmarks, width, height) :
        # Convert the landmarks to px
        # Z coordinates : do nothing, no depth
        result = {}
        for landmark in landmarks:
            output = landmarks.get(landmark)
            result[landmark] = [0, 0, 0]
            result[landmark][0] = int(output[0] * width)  # To pixels
            result[landmark][1] = int(output[1] * height) # To pixels
            result[landmark][2] = output[2]

        return result
    
    @staticmethod
    def to_normalized_landmarks(landmarks, center, distance):
        # Check the distance
        if distance == 0: raise RuntimeError("The distance cannot be zero")
        
        # Center the landmarks
        # Normalize the landmarks
        # Z coordinates : do nothing, no depth
        result = {}
        for landmark in landmarks:
            output = landmarks.get(landmark)   
            output = Utils.substract_landmark(output, center)
            result[landmark] = [0, 0, 0]
            result[landmark][0] = output[0] / distance
            result[landmark][1] = output[1] / distance
            result[landmark][2] = output[2]

        return result
    
    @staticmethod
    def substract_landmark(landmark_1, landmark_2):
        # Substract the second landmark
        # (from the first one)
        result = [0, 0, 0]
        result[0] = landmark_1[0] - landmark_2[0]
        result[1] = landmark_1[1] - landmark_2[1]
        result[2] = landmark_1[2] - landmark_2[2]
        return result