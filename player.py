from board import Direction, Rotation, Shape
from math import log


class Player:
    def choose_action(self, board):
        raise NotImplementedError


class Yousef(Player):
    def __init__(self):
        self.queue = []

        self.w1 = 0.2127  # Post_height_weight
        self.w2 = 0.85  # Bumpiness_weight
        self.w3 = 5.5  # Bubbles_weight
        self.w4 = 0.205  # Average_Height_weight
        self.w5 = 1  # Lines_completed_weight
        self.w6 = 1  # Next_block_score_weight
        self.w7 = 0.5 # Difference between post and avg

        self.lines_clearing_limiter = 4
        self.block_counter = 0
        self.shape_rotations = {
            Shape.I: 2,
            Shape.J: 4,
            Shape.L: 4,
            Shape.O: 1,
            Shape.S: 2,
            Shape.T: 4,
            Shape.Z: 2}

        self.block_clearing_threshold = 390

    @staticmethod
    def create_queue(index, shape, warning: bool = False):

        queue = []

        if shape != Shape.T and 10 <= index < 30 and not warning:
            queue.append(Rotation.Clockwise)
            index = index - 10

        for y in range(abs((index % 10) - 5)):
            if (index % 10) - 5 > 0:
                queue.append(Direction.Right)
            elif (index % 10) - 5 < 0:
                queue.append(Direction.Left)

        if index//10 == 3:
            queue.append(Rotation.Anticlockwise)
        else:
            for y in range(index // 10):
                queue.append(Rotation.Clockwise)

        return queue

    def pop_queue(self):
        if len(self.queue) > 0:
            move = self.queue[0]
            del self.queue[0]
            return move

        return Direction.Drop

    @staticmethod
    def proof_action(board, move):
        if board.falling is not None:
            if move == Rotation.Clockwise or move == Rotation.Anticlockwise:
                return board.rotate(move)
            else:
                return board.move(move)
        return

    # The following methods gather the values for each heuristic.

    # gets the highest point on the board.
    @staticmethod
    def get_highest_point(board) -> int:
        post_height = 23
        for y in board.cells:
            if y[1] < post_height:
                post_height = y[1]
        return post_height

    # gets the heights of all the columns on the board.
    @staticmethod
    def get_heights(board) -> list:
        heights = [23 for _ in range(10)]

        for x, y in board.cells:
            if y < heights[x]:
                heights[x] = y

        return heights

    # gets the value between the heights of each column and the next column.
    @staticmethod
    def get_bumpiness(heights: list) -> int:
        bump = 0
        for i in range(9):
            bump += abs(heights[i] - heights[i + 1])
        return bump

    # counts the number of squares that have been covered by a square on top.
    @staticmethod
    def get_bubbles(board, heights: list, post_height: int) -> int:
        bubble = 0
        for column in range(10):
            for row in range(23, post_height - 1, -1):
                if (column, row) not in board.cells and row >= heights[column] < 23:
                    bubble = bubble + 1
        return bubble

    def convert_score(self, score: int) -> float:
        score = score//100  # 100, 400, 800, 1600 -> 1,4,8,16
        if score != 0:
            score = log(score, 2)  # 1, 4, 8, 16 -> 0,2,3,4
            if score == 0:  # since the 100 points converts to 0, we need to increment it to fit the sequence 1,2,3,4
                score += 1

            # we want to discourage smaller combos up until it the end where we need to clear the board.
            if score < self.lines_clearing_limiter:
                score = ((-1.25) / (score + 1.8))*10.85
            else:
                score = 2**score
                score *= 100

        return score

    @staticmethod
    def get_height(heights, height):
        for i in range(len(heights)):
            if height == heights[i]:
                return i

    def get_actions(self, board, recurse: bool = True):
        self.queue = []
        if recurse:
            self.block_counter += 1

        pre_height = self.get_highest_point(board)

        try:
            num_rotations = self.shape_rotations[board.falling.shape]
        except AttributeError:
            num_rotations = 4

        aggregate_score = [0 for _ in range(num_rotations * 10)]

        warning = False
        if pre_height < 6:
            warning = True

        if recurse and pre_height < 14:
            self.lines_clearing_limiter = 3

        if self.block_counter >= self.block_clearing_threshold:
            self.lines_clearing_limiter = 1
            self.w5 = 15

        queues = [[] for i in range(num_rotations*10)]
        for rotations in range(num_rotations):
            for position in range(10):
                clone = board.clone()
                index = (rotations * 10) + position

                #15313
                queue = self.create_queue(index, clone.falling, warning)

                for move in queue:
                    self.proof_action(clone, move)

                self.proof_action(clone, Direction.Drop)

                raw_score = clone.score - board.score

                score = self.convert_score(raw_score)
                heights = self.get_heights(clone)
                post_height = self.get_highest_point(clone)
                bump = self.get_bumpiness(heights)
                bubble = self.get_bubbles(clone, heights, post_height)
                avg_height = sum(heights) / 10
                avg_diff = abs(post_height - avg_height)

                ag_next_score = 0

                if recurse:
                    ag_next_score = self.get_actions(clone, False)

                if avg_height > 19 and score < 0:
                    avg_height = 23 - avg_height

                if clone.alive == False:
                    aggregate_score[index] = -9000

                aggregate_score[index] += (post_height * self.w1) + (bump * -self.w2) + (bubble * -self.w3) + \
                                          (avg_height * self.w4) + (score * self.w5) + (ag_next_score * self.w6) + \
                                          (avg_diff * -self.w7)

        best_score = max(aggregate_score)
        index = aggregate_score.index(best_score)

        if recurse:
            self.lines_clearing_limiter = 4

        if not recurse:
            return best_score

        self.queue = self.create_queue(index, board.falling, warning)

    def choose_action(self, board):

        for x, y in board.falling.cells:
            if y == 0:
                self.get_actions(board)
                break

        return self.pop_queue()


SelectedPlayer = Yousef
