import json
import os
import pandas
import statistics
import datetime
import scipy
from collections import deque


# =================================================================================================
# PARAMETERS
# =================================================================================================

DATE = datetime.datetime.now().strftime("%Y-%m-%d-%H-%M-%S")

EXPERIMENTS_FOLDER = "../experiments/"

DDA_TYPES = {
    1 : "rule",
    2 : "data",
}

N_TARGETS = 100

COLS_FOR_CONCATENATION = [
    "window_score",
    "diff_target_distance",
    "diff_target_size",
    "diff_reach_time",
]


# =================================================================================================
# UTILS
# =================================================================================================

def get_experiments(folder_path, print_result = False):
    result = []

    for root, dirs, files in os.walk(folder_path): # https://www.geeksforgeeks.org/python/python-loop-through-folders-and-files-in-directory/
        if "scores.csv" not in files: continue
        
        scores_path = os.path.join(root, "scores.csv")
        parameters_path = os.path.join(root, "parameters.json")

        parameters = None
        with open(parameters_path, "r") as file:
            parameters = json.load(file)

        player_id = parameters["user_id"]
        player_id = player_id.split("-")[0]

        profile = parameters["user_id"]
        profile = profile.split("-")[1]

        dda_type = parameters["diff_type"]
        dda_type = DDA_TYPES.get(dda_type)

        if dda_type is None: continue

        result.append({
            "scores_path" : scores_path,
            "parameters_path" : parameters_path,
            "player_id" : player_id,
            "profile" : profile,
            "dda_type" : dda_type,
        })

    if print_result:
        for c_result in result:
            print(c_result)

    return result


# =================================================================================================
# Main
# =================================================================================================

def main():
    # Get all the experiments (with the CSV paths) recursively
    experiments = get_experiments(EXPERIMENTS_FOLDER, False)

    # Will hold the experiments that have at least N_TARGETS
    valid_experiments = []
    
    for experiment in experiments:
        scores_path = experiment["scores_path"]
        df_data = pandas.read_csv(scores_path)

        if len(df_data) < N_TARGETS:
            print(scores_path + " : avoided, it does not contain enough targets")
            continue

        for c_col in COLS_FOR_CONCATENATION: # Loop over the cols for concatenation
            for i in range(N_TARGETS):       # Loop over the rows of the current experiment
                curr_row = df_data.iloc[i]
                experiment[c_col + "_" + str(i + 1)] = curr_row[c_col]

        valid_experiments.append(experiment)

    # Save the parameters
    parameters = {
        "date" : DATE,
        "experiments_folder" : EXPERIMENTS_FOLDER,
        "n_targets" : N_TARGETS,
    }

    os.makedirs(DATE, exist_ok=True) # Avoid already existing error
    path = os.path.join(DATE, "parameters.json")
    with open(path, "w") as file: json.dump(parameters, file, indent=4)

    # Save the concatenated experiments
    experiments = valid_experiments
    df_experiments = pandas.DataFrame(experiments)
    df_experiments.to_csv(DATE + "/experiments_concatenated.csv", index=False)


if __name__ == "__main__":
    main()