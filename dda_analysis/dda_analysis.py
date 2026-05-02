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

WINDOW_SIZE_CONVERGENCE = 10

N_LAST_TARGETS = 20

COLS = [
    "dda_type",
    "goal_score",
    "margin_score",
    "adjusted_parameter",
    "diff_target_distance",
    "diff_target_size",
    "diff_reach_time",
    "score",
    "score_improvement",
    "window_score",
    "window_score_improvement",
]

COLS_FOR_CORRELATION = [
    "mean_diff_target_distance_last_targets",
    "mean_diff_target_size_last_targets",
    "mean_diff_reach_time_last_targets",
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


def get_distance_to_goal_score_range(score, goal_score, margin_score):
    distance = abs(score - goal_score) - margin_score
    return distance


def get_in_goal_score_range(score, goal_score, margin_score):
    epsilon = 1e-9 # Avoid floating point rounding error
    distance = get_distance_to_goal_score_range(score, goal_score, margin_score)
    in_range = distance <= epsilon
    return in_range


def get_stats(scores_path, n_targets, window_size_convergence, n_last_targets, print_result = False):
    df_data = pandas.read_csv(scores_path)
    df_data = df_data[COLS]

    if len(df_data) < n_targets:
        print(scores_path + " : avoided, it does not contain enough targets")
        return None

    window_scores_convergence = deque(maxlen=window_size_convergence)

    dda_rewards = []
    n_targets_to_convergence = None

    from_convergence_in_goal_score_range = []
    from_convergence_window_scores = []
    from_convergence_distances_to_goal_score_range = []

    last_targets_window_scores = []
    last_targets_distances_to_goal_score_range = []

    last_targets_diff_target_distance = []
    last_targets_diff_target_size = []
    last_targets_diff_reach_time = []

    for i in range(n_targets):
        curr_row = df_data.iloc[i]

        window_scores_convergence.append(curr_row["window_score"])
        mean_window_score_convergence = statistics.mean(window_scores_convergence)
        in_goal_score_range_convergence = get_in_goal_score_range(mean_window_score_convergence, curr_row["goal_score"], curr_row["margin_score"]) if len(window_scores_convergence) == window_size_convergence else False
        
        distance_to_goal_score_range = get_distance_to_goal_score_range(curr_row["window_score"], curr_row["goal_score"], curr_row["margin_score"])
        in_goal_score_range = get_in_goal_score_range(curr_row["window_score"], curr_row["goal_score"], curr_row["margin_score"])

        # DDA adjustment
        if curr_row["adjusted_parameter"] != -1:
            dda_rewards.append(curr_row["window_score_improvement"])

        # To convergence
        if in_goal_score_range_convergence and n_targets_to_convergence is None:
            n_targets_to_convergence = i + 1

        # From convergence
        if n_targets_to_convergence is not None:
            if in_goal_score_range: from_convergence_in_goal_score_range.append(1)
            else: from_convergence_in_goal_score_range.append(0)
            from_convergence_window_scores.append(curr_row["window_score"])
            from_convergence_distances_to_goal_score_range.append(distance_to_goal_score_range)

        # Last targets
        if i >= n_targets - n_last_targets:
            last_targets_window_scores.append(curr_row["window_score"])
            last_targets_distances_to_goal_score_range.append(distance_to_goal_score_range)
            last_targets_diff_target_distance.append(curr_row["diff_target_distance"])
            last_targets_diff_target_size.append(curr_row["diff_target_size"])
            last_targets_diff_reach_time.append(curr_row["diff_reach_time"])
        
    if len(dda_rewards) == 0: raise RuntimeError("dda_rewards is empty, scores_path : " + scores_path)
    if n_targets_to_convergence is None: raise RuntimeError("target_to_convergence is None, scores_path : " + scores_path)

    result = {
        "Mean DDA reward" : statistics.mean(dda_rewards),
        "Number of targets to convergence" : n_targets_to_convergence,

        "Percentage of targets in goal score range (from convergence)" : statistics.mean(from_convergence_in_goal_score_range),
        "Mean window score (from convergence)" : statistics.mean(from_convergence_window_scores),
        "Mean distance to goal score range (from convergence)" : statistics.mean(from_convergence_distances_to_goal_score_range),

        "Mean window score (last targets)" : statistics.mean(last_targets_window_scores),
        "Stdev window score (last targets)" : statistics.stdev(last_targets_window_scores),
        "Mean distance to goal score range (last targets)": statistics.mean(last_targets_distances_to_goal_score_range),

        "mean_diff_target_distance_last_targets" : statistics.mean(last_targets_diff_target_distance),
        "mean_diff_target_size_last_targets" : statistics.mean(last_targets_diff_target_size),
        "mean_diff_reach_time_last_targets" : statistics.mean(last_targets_diff_reach_time),
    }

    for col in COLS_FOR_CORRELATION:
        if col not in result: raise RuntimeError("col " + col + " is missing from result")

    if print_result:
        print(result)

    return result


def get_correlation(df_experiments, dda_types, cols_for_correlation, print_result = False):
    result = []

    # Add a new columns for Spearman correlation
    # https://pandas.pydata.org/docs/getting_started/intro_tutorials/05_add_columns.html
    # https://pandas.pydata.org/docs/reference/api/pandas.Series.str.html
    # https://pandas.pydata.org/docs/reference/api/pandas.DataFrame.astype.html
    df_experiments["profile_level"] = df_experiments["profile"].str.replace("p", "").astype(int)

    # Loop over the DDA
    # Then, filter the experiments by DDA type
    # Finally, compute the Spearman correlation
    # https://www.geeksforgeeks.org/python/selecting-rows-in-pandas-dataframe-based-on-conditions/
    # https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.spearmanr.html
    for key in dda_types:
        dda_type = dda_types[key]
        df_filtered_experiments = df_experiments[df_experiments["dda_type"] == dda_type]

        for col in cols_for_correlation:
            res = scipy.stats.spearmanr(df_filtered_experiments["profile_level"], df_filtered_experiments[col])
            result.append({
                "dda_type" : dda_type,
                "diff_parameter" : col,
                "statistic" : res.statistic,
                "pvalue" : res.pvalue,
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
        stats = get_stats(scores_path, N_TARGETS, WINDOW_SIZE_CONVERGENCE, N_LAST_TARGETS, False) # Stats example : mean reward, number of targets to convergence, ...
        
        if stats is None: continue # Not enought targets
        
        for key in stats:
            val = stats[key]
            experiment[key] = val

        valid_experiments.append(experiment)

    os.makedirs(DATE, exist_ok=True) # Avoid already existing error

    # Save the parameters
    parameters = {
        "date" : DATE,
        "experiments_folder" : EXPERIMENTS_FOLDER,
        "n_targets" : N_TARGETS,
        "window_size_convergence" : WINDOW_SIZE_CONVERGENCE,
        "n_last_targets" : N_LAST_TARGETS,
    }
    path = os.path.join(DATE, "parameters.json")
    with open(path, "w") as file: json.dump(parameters, file, indent=4)

    # Save the experiments with stats
    df_experiments = pandas.DataFrame(valid_experiments)
    df_experiments.to_csv(DATE + "/experiments.csv", index=False)
    df_experiments.groupby("dda_type").mean(numeric_only=True).to_csv(DATE + "/experiments_grouped.csv")
    df_experiments.groupby(["dda_type", "profile"]).mean(numeric_only=True).to_csv(DATE + "/experiments_grouped_2.csv")

    # Save the correlation
    correlations = get_correlation(df_experiments, DDA_TYPES, COLS_FOR_CORRELATION)
    df_correlations = pandas.DataFrame(correlations)
    df_correlations.to_csv(DATE + "/correlation.csv", index=False)


if __name__ == "__main__":
    main()