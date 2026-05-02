import random


class RandomModel:

    def __init__(self, arms, seed):
        self.arms = arms
        self.random = random.Random(seed)

    def fit(self, decisions, rewards, contexts):
        pass

    def predict(self, contexts):
        return self.random.choice(self.arms)

    def partial_fit(self, decisions, rewards, contexts):
        pass