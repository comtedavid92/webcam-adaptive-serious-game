import os
import copy
import json
import datetime
import pandas
from sklearn.preprocessing import StandardScaler
from mabwiser.mab import MAB, LearningPolicy, NeighborhoodPolicy
from custom_models import RandomModel


# =================================================================================================
# PARAMETERS
# =================================================================================================

DATE = datetime.datetime.now().strftime("%Y-%m-%d-%H-%M-%S")

N_RUNS = 100

REPLAY_TYPE_REPLAY_ONLY = 0
REPLAY_TYPE_REPLAY_AND_LEARN = 1
REPLAY_TYPE = REPLAY_TYPE_REPLAY_ONLY

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
]

TEST_CSV = [
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

    model_random = {
        "title" : "Random Policy (baseline)",
        "model" : RandomModel(arms=arms, seed=seed),
    }

    model_bonus = {
        "title" : "LinGreedy (epsilon = 0.00)",
        "model" : MAB(arms=arms, learning_policy=LearningPolicy.LinGreedy(epsilon=0.00), seed=seed),
    }

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
        model_random, # The first model is the baseline
        model_bonus,
        model_a,
        model_b,
        model_c,
        model_d,
        model_e,
        model_f,
        model_g,
        #model_h,
        #model_i,
        #model_j,
        #model_k,
    ]

    for model in models:
        model["scaler"] = StandardScaler()
        model["temp_model"] = None
        model["temp_scaler"] = None
        model["n_total"] = 0
        model["n_match"] = 0
        model["reward"] = 0
        model["mean_match"] = 0
        model["mean_reward"] = 0
        model["mean_reward_gain"] = 0

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


def replay(models, df_data, context_cols):
    for i in range(len(df_data)):
        curr_row = df_data.iloc[i]
        
        df_context = pandas.DataFrame([curr_row[context_cols]], columns=context_cols) # The row does not contain the cols, add them to avoid a warning
        logged_adjusted_parameter = curr_row["adjusted_parameter"]
        window_score_improvement = curr_row["window_score_improvement"]

        for model in models:
            model["n_total"] += 1
            
            scaled_context = model["scaler"].transform(df_context)
            predicted_adjusted_parameter = model["model"].predict(scaled_context)

            if predicted_adjusted_parameter == logged_adjusted_parameter:
                model["n_match"] += 1
                model["reward"] += window_score_improvement


def replay_and_learn(models, df_data, context_cols):
    prev_csv = None

    for i in range(len(df_data)):
        curr_row = df_data.iloc[i]
        curr_csv = curr_row["csv"]

        if curr_csv != prev_csv:
            prev_csv = curr_csv
            
            # The simulation is identical to that of the game
            # The participant uses a pretrained model that continues to learn online
            for model in models: 
                model["temp_model"] = copy.deepcopy(model["model"])
                model["temp_scaler"] = copy.deepcopy(model["scaler"])

        df_context = pandas.DataFrame([curr_row[context_cols]], columns=context_cols) # The row does not contain the cols, add them to avoid a warning
        logged_adjusted_parameter = curr_row["adjusted_parameter"]
        window_score_improvement = curr_row["window_score_improvement"]

        for model in models:
            model["n_total"] += 1
            
            scaled_context = model["temp_scaler"].transform(df_context)
            predicted_adjusted_parameter = model["temp_model"].predict(scaled_context)

            if predicted_adjusted_parameter == logged_adjusted_parameter:
                model["temp_scaler"].partial_fit(df_context)
                model["temp_model"].partial_fit(decisions=[predicted_adjusted_parameter], rewards=[window_score_improvement], contexts=scaled_context)
                model["n_match"] += 1
                model["reward"] += window_score_improvement


def compute_stats(models):
    baseline_mean_reward = None

    for model in models:
        model["mean_match"] = model["n_match"] / model["n_total"] if model["n_total"] > 0 else 0
        model["mean_reward"] = model["reward"] / model["n_match"] if model["n_match"] > 0 else 0
        
        if baseline_mean_reward is None: baseline_mean_reward = model["mean_reward"]
        model["mean_reward_gain"] = (model["mean_reward"] - baseline_mean_reward) / baseline_mean_reward if baseline_mean_reward > 0 else 0


def get_rows(models, run):
    rows = []

    for model in models:
        row = {
            "run" : run,
            "model" : model["title"],
            "n_total" : model["n_total"],
            "n_match" : model["n_match"],
            "reward" : model["reward"],
            "mean_match" : model["mean_match"],
            "mean_reward" : model["mean_reward"],
            "mean_reward_gain" : model["mean_reward_gain"],
        }
        rows.append(row)

    return rows


# =================================================================================================
# Main
# =================================================================================================

def main():
    # Prepare the data
    runs = []
    df_training_data = get_data(TRAINING_CSV, CONTEXT_COLS)
    df_test_data = get_data(TEST_CSV, CONTEXT_COLS)

    # Prepare the results folder
    results_path = DATE
    os.makedirs(results_path, exist_ok=True) # Avoid already existing error

    # Save the parameters
    parameters = {
        "date" : DATE,
        "n_runs" : N_RUNS,
        "replay_type" : REPLAY_TYPE,
        "context_cols" : CONTEXT_COLS,
        "training_csv" : TRAINING_CSV,
        "test_csv" : TEST_CSV,
    }
    path = os.path.join(results_path, "parameters.json")
    with open(path, "w") as file: json.dump(parameters, file, indent=4)

    # Execute the runs
    for i in range(N_RUNS):
        run = i
        seed = i

        models = get_models(seed)
        train_models(models, df_training_data, CONTEXT_COLS)
        
        if REPLAY_TYPE == REPLAY_TYPE_REPLAY_ONLY:
            replay(models, df_test_data, CONTEXT_COLS)
        elif REPLAY_TYPE == REPLAY_TYPE_REPLAY_AND_LEARN:
            replay_and_learn(models, df_test_data, CONTEXT_COLS)
        
        compute_stats(models)
        
        rows = get_rows(models, run)
        runs.extend(rows) # Rows contains a list and not a single item

    # Save the rows
    df_results = pandas.DataFrame(runs)
    path = os.path.join(results_path, "rows.csv")
    df_results.to_csv(path, index=False) # https://pandas.pydata.org/docs/reference/api/pandas.DataFrame.to_csv.html

    # Save the stats
    df_stats = (
        df_results
        .groupby("model")["mean_reward"]
        .agg(["mean", "std", "min", "max", "median"])
        .reset_index() # Else, the model col is missing from the CSV
    )
    path = os.path.join(results_path, "stats.csv")
    df_stats.to_csv(path, index=False)


if __name__ == "__main__":
    main()