"""
    defines a 20Qs bot
"""
try:
    from math import log2
except ImportError:
    from math import log
    log2 = lambda x: log(x, 2)
from .db import ANSWERS, Question, Animal, add_game, log_game,\
     get_all, query_all_responses, NO_RESPONSE

NUM_QUESTIONS = 20

class QaBot(object):
    """
        Takes a dataset and a set of questions questions
        Makes guesses about good questions to ask
        and possible solutions
    """
    def __init__(self, serialized=None):
        self.questions = []
        self.guesses = None
        if serialized is not None:
            self.questions = serialized['questions']
            if 'guesses' in serialized:
                try:
                    self.guesses = []
                    for (name, _id, prob) in serialized['guesses']:
                        animal = Animal(name)
                        animal.id = _id
                        animal.prob = prob
                        self.guesses.append(animal)
                except ValueError:
                    print("CORRUPTED")
            else:
                print("GUESSES NOT SAVED")

    def serialize(self):
        out = {'questions': self.questions}
        if self.guesses is not None:
            out['guesses'] = [(guess.name, guess.id, guess.prob) for guess in self.guesses]
        return out

    def get_guesses(self):
        """
        Get a weighted list of animals that 'best' fit our information
        """
        if self.guesses is not None:
            return self.guesses
        print("RECALCULATING GUESSES")
        self.guesses = get_all(Animal)
        for animal in self.guesses:
            animal.prob = 1
            # to consider how often animals are guessed use animal.count
        self.guesses = normalize_guesses(self.guesses)

        for question, answer in self.questions:
            self.guesses = adjust_guesses(self.guesses, question, answer)
        return self.guesses

    def get_question(self):
        """ Return the next question to ask """
        best_q = None
        questions = get_all(Question)
        if self.questions != []:
            asked_txt = set([q[0] for q in self.questions])
            questions = [q for q in questions if q.question not in asked_txt]

        # filter / order and limit to get maximal split
        animals = self.get_guesses()
        for question in questions:
            split = get_entropy(question.question, animals)
            if best_q is None or split > best_q.entropy: # maximize entropy
                best_q = question
                best_q.entropy = split

        if best_q is None:
            best_q = Question("Sorry, I don't know this one")
            best_q.entropy = 0
            return (best_q, [])

        return (best_q, ANSWERS)

    def give_answer(self, question, answer):
        print("Q: \"{}\", A: \"{}\"".format(question, answer))
        if question and answer:
            self.questions.append((question, answer))
            self.guesses = adjust_guesses(self.get_guesses(), question, answer)
        return self.questions

    def finish_game(self, solution):
        if solution is not None:
            # save solution and questions to data base
            add_game(solution, self.questions)
            #log the outcome
            log_game(solution, self.guesses)

    def undo(self):
        if self.questions != []:
            question, answer = self.questions[-1]
            self.guesses = adjust_guesses(self.guesses, question, answer, weighting=-1)
            self.questions.pop()

    def question_number(self):
        return len(self.questions)+1

    def game_finished(self):
        return self.question_number() > NUM_QUESTIONS

def get_entropy(question, animals):
    """ Finds the entropy of the answers of a question for a set of animals """
    response_set = {answer:0.000001 for answer in ANSWERS}

    all_responses = query_all_responses(question=question, animals=animals)
    for animal in animals:
        responses = all_responses.get(animal.name, NO_RESPONSE)
        if responses is not None:
            responses = sorted(
                responses.items(),
                key=lambda resp: -resp[1]
            )
            (first, _) = responses[0]
            (last, _) = responses[-1]
            response_set[first] += animal.prob
            response_set[last] += (1-animal.prob)
        else:
            print("COULDN'T FIND ANIMAL \"{}\"".format(animal.name))

    total = sum(response_set.values())
    probs = [count/total for count in response_set.values()]

    entropy = sum([-(p)*log2(p) for p in probs])
    return entropy


def adjust_guesses(animals, question, answer, weighting=1):
    """
    Takes a set of guesses and applies a question's answer probability distribution
    """

    all_responses = query_all_responses(question=question, animals=animals)
    for animal in animals:
        responses = all_responses.get(animal.name, NO_RESPONSE)
        update = responses[answer] / sum(responses.values())
        animal.prob *= pow(update, weighting)
    return normalize_guesses(animals)

def normalize_guesses(animals):
    total_plays = sum([animal.prob for animal in animals])
    if total_plays != 0:
        for animal in animals:
            animal.prob /= total_plays

    animals = sorted(animals, key=lambda animal: -animal.prob)
    return animals
