import os
import cloudpickle
import json
import datetime
import pandas
from sklearn.preprocessing import StandardScaler
from mabwiser.mab import MAB, LearningPolicy, NeighborhoodPolicy


# =================================================================================================
# PARAMETERS
# =================================================================================================

DATE = datetime.datetime.now().strftime("%Y-%m-%d-%H-%M-%S")

CONTEXT_COLS = [
    "diff_target_distance",
    "diff_target_size",
    "diff_reach_time",
    "window_reach_wrist_number_of_velocity_peaks",
    "window_reach_wrist_mean_velocity",
    "window_reach_wrist_sparc",
    "window_reach_wrist_jerk",
    "window_reach_trunk_rom",
    "window_reach_hand_path_ratio",
    "window_has_dwell",
    "window_dwell_wrist_mean_velocity",
]

TRAINING_CSV = [
    # 0001-01
    "../experiments/0001-p1-right-random/2026-03-20-13-59-13/scores.csv",
    "../experiments/0001-p2-right-random/2026-03-21-21-29-22/scores.csv",
    "../experiments/0001-p3-right-random/2026-03-21-22-24-14/scores.csv",
    # 0002-01
    "../experiments/0002-p1-right-random/2026-03-21-17-29-10/scores.csv",
    "../experiments/0002-p2-right-random/2026-03-21-21-40-44/scores.csv",
    "../experiments/0002-p3-right-random/2026-03-21-22-33-06/scores.csv",
    # 0003
    "../experiments/0003-p1-right-random/2026-03-22-12-18-38/scores.csv",
    "../experiments/0003-p2-right-random/2026-03-22-14-41-57/scores.csv",
    "../experiments/0003-p3-right-random/2026-03-22-14-56-49/scores.csv",
    # 0004
    "../experiments/0004-p1-right-random/2026-03-22-12-01-41/scores.csv",
    "../experiments/0004-p2-right-random/2026-03-22-15-09-06/scores.csv",
    "../experiments/0004-p3-right-random/2026-03-22-15-24-33/scores.csv",
    # 0001-02
    "../experiments/0001-p1-right-random/2026-03-21-17-10-42/scores.csv",
    "../experiments/0001-p2-right-random/2026-03-21-21-57-18/scores.csv",
    "../experiments/0001-p3-right-random/2026-03-21-22-48-27/scores.csv",
    # 0002-02
    "../experiments/0002-p1-right-random/2026-03-21-21-13-08/scores.csv",
    "../experiments/0002-p2-right-random/2026-03-21-22-09-17/scores.csv",
    "../experiments/0002-p3-right-random/2026-03-21-22-56-10/scores.csv",
    # 0005
    "../experiments/0005-p1-right-random/2026-03-22-11-41-26/scores.csv",
    "../experiments/0005-p2-right-random/2026-03-22-13-55-33/scores.csv",
    "../experiments/0005-p3-right-random/2026-03-22-14-25-53/scores.csv",
    # 0006
    "../experiments/0006-p1-right-random/2026-03-22-11-51-39/scores.csv",
    "../experiments/0006-p2-right-random/2026-03-22-13-41-40/scores.csv",
    "../experiments/0006-p3-right-random/2026-03-22-14-13-36/scores.csv",
]


# =================================================================================================
# UTILS
# =================================================================================================

def get_models(seed):
    # Contextual MAB : https://github.com/fidelity/mabwiser/blob/master/examples/contextual_mab.py
    # Parametric MAB : https://github.com/fidelity/mabwiser/blob/master/examples/parametric_mab.py

    arms = [0, 1, 2] # 0 : diff_target_distance, 1 : diff_target_size, 2 : diff_reach_time

    model_a = {
        "title" : "LinGreedy (epsilon = 0.05)",
        "model" : MAB(arms=arms, learning_policy=LearningPolicy.LinGreedy(epsilon=0.05), seed=seed),
    }

    model_b = {
        "title" : "LinGreedy (epsilon = 0.1)",
        "model" : MAB(arms=arms, learning_policy=LearningPolicy.LinGreedy(epsilon=0.1), seed=seed),
    }

    model_c = {
        "title" : "LinGreedy (epsilon = 0.15)",
        "model" : MAB(arms=arms, learning_policy=LearningPolicy.LinGreedy(epsilon=0.15), seed=seed),
    }
    
    model_d = {
        "title" : "LinGreedy (epsilon = 0.2)",
        "model" : MAB(arms=arms, learning_policy=LearningPolicy.LinGreedy(epsilon=0.2), seed=seed),
    }

    model_e = {
        "title" : "LinGreedy (epsilon = 0.3)",
        "model" : MAB(arms=arms, learning_policy=LearningPolicy.LinGreedy(epsilon=0.3), seed=seed),
    }

    model_f = {
        "title" : "LinUCB",
        "model" : MAB(arms=arms, learning_policy=LearningPolicy.LinUCB(), seed=seed),
    }

    model_g = {
        "title" : "LinTS",
        "model" : MAB(arms=arms, learning_policy=LearningPolicy.LinTS(), seed=seed),
    }

    model_h = {
        "title" : "Greedy + KNearest (k=2)",
        "model" : MAB(arms=arms, learning_policy=LearningPolicy.EpsilonGreedy(), neighborhood_policy=NeighborhoodPolicy.KNearest(k=2), seed=seed),
    }

    model_i = {
        "title" : "Greedy + KNearest (k=5)",
        "model" : MAB(arms=arms, learning_policy=LearningPolicy.EpsilonGreedy(), neighborhood_policy=NeighborhoodPolicy.KNearest(k=5), seed=seed),
    }

    model_j = {
        "title" : "Greedy + KNearest (k=8)",
        "model" : MAB(arms=arms, learning_policy=LearningPolicy.EpsilonGreedy(), neighborhood_policy=NeighborhoodPolicy.KNearest(k=8), seed=seed),
    }

    model_k = {
        "title" : "Greedy + TreeBandit",
        "model" : MAB(arms=arms, learning_policy=LearningPolicy.EpsilonGreedy(), neighborhood_policy=NeighborhoodPolicy.TreeBandit(), seed=seed),
    }

    models = [
        model_a,
        model_b,
        model_c,
        model_d,
        model_e,
        model_f,
        model_g,
        model_h,
        model_i,
        model_j,
        model_k,
    ]

    for model in models:
        model["scaler"] = StandardScaler()

    return models


def get_data(data_csv, context_cols):
    std_data = []

    for csv in data_csv:
        df_data = pandas.read_csv(csv)

        for i in range(1, len(df_data)):
            prev_row = df_data.iloc[i-1] # https://pandas.pydata.org/docs/reference/api/pandas.DataFrame.iloc.html
            curr_row = df_data.iloc[i]

            if curr_row["adjusted_parameter"] == -1: continue # No parameter is adjusted, the score is within the target range.

            # Action at time t, context at time t-1, reward at time t
            to_add = {}
            to_add["csv"] = csv
            to_add["adjusted_parameter"] = curr_row["adjusted_parameter"]
            to_add["window_score_improvement"] = curr_row["window_score_improvement"]
            for col in context_cols: to_add[col] = prev_row[col]

            std_data.append(to_add)

    df_data = pandas.DataFrame(std_data)

    return df_data


def train_models(models, df_data, context_cols):
    for model in models:
        model["scaler"].fit(df_data[context_cols])
        scaled_context = model["scaler"].transform(df_data[context_cols])
        model["model"].fit(decisions=df_data["adjusted_parameter"], rewards=df_data["window_score_improvement"], contexts=scaled_context)


# =================================================================================================
# Main
# =================================================================================================

def main():
    # Prepare the data
    seed = 0
    df_training_data = get_data(TRAINING_CSV, CONTEXT_COLS)

    # Prepare the results folder
    results_path = DATE
    os.makedirs(results_path, exist_ok=True) # Avoid already existing error

    # Save the parameters
    parameters = {
        "date" : DATE,
        "context_cols" : CONTEXT_COLS,
        "training_csv" : TRAINING_CSV,
    }
    path = os.path.join(results_path, "parameters.json")
    with open(path, "w") as file: json.dump(parameters, file, indent=4)

    # Train the models
    models = get_models(seed)
    train_models(models, df_training_data, CONTEXT_COLS)

    # Save the models
    for model in models:
        path = os.path.join(results_path, model["title"] + ".pkl")
        with open(path, "wb") as file:
            cloudpickle.dump({
                "model": model["model"],
                "scaler": model["scaler"],
            }, file)


if __name__ == "__main__":
    main()