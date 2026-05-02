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

    # Will hold the stats per DDA
    stats = {}
    
    for experiment in experiments:

        scores_path = experiment["scores_path"]
        df_data = pandas.read_csv(scores_path)

        if len(df_data) < N_TARGETS:
            print(scores_path + " : avoided, it does not contain enough targets")
            continue

        dda_type = experiment["dda_type"] # DDA type of the experiment

        if stats.get(dda_type) is None:   # Check for the presence of the DDA type in the stats
            stats[dda_type] = {
                "n_targets": 0,
                "n_adjustments": 0,
                "total_reward": 0,
                "n_effective_adjustments": 0,
                "n_ineffective_adjustments": 0,
            }

        for i in range(0, N_TARGETS): # Loop over the rows of the current experiment
    
            if i == 0: # Do not loop over the first row, as there is no previous row
                stats[dda_type]["n_targets"] += 1
                continue

            prev_row = df_data.iloc[i-1]
            curr_row = df_data.iloc[i]

            adjustment = True if curr_row["adjusted_parameter"] != -1 else False
            same_distance = True if prev_row["diff_target_distance"] == curr_row["diff_target_distance"] else False
            same_size = True if prev_row["diff_target_size"] == curr_row["diff_target_size"] else False
            same_time = True if prev_row["diff_reach_time"] == curr_row["diff_reach_time"] else False
            same_param = same_distance and same_size and same_time
            
            stats[dda_type]["n_targets"] += 1

            if adjustment:
                stats[dda_type]["n_adjustments"] += 1
                stats[dda_type]["total_reward"] += curr_row["window_score_improvement"]

            if adjustment and not same_param:
                stats[dda_type]["n_effective_adjustments"] += 1
            
            if adjustment and same_param:
                stats[dda_type]["n_ineffective_adjustments"] += 1
                        
    # Save the parameters
    parameters = {
        "date" : DATE,
        "experiments_folder" : EXPERIMENTS_FOLDER,
        "n_targets" : N_TARGETS,
    }

    os.makedirs(DATE, exist_ok=True) # Avoid already existing error
    path = os.path.join(DATE, "parameters.json")
    with open(path, "w") as file: json.dump(parameters, file, indent=4)

    # Save the stats
    df_stats = pandas.DataFrame(stats)
    df_stats.to_csv(DATE + "/total_reward.csv", index=True)


if __name__ == "__main__":
    main()