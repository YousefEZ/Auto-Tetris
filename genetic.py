from visual import *
from random import random

class nature:
    def __init__(self, population_size:int=50):
        self.population = [[random() for x in range (6)] for _ in range(population_size)]

    def mutate(self):
        pass