"""
    defines a 20Qs bot
"""
from db import Entry, Question

class QaBot(object):
    """
        Takes a dataset and a set of answered questions
        Makes guesses about good questions to ask
        and possible solutions
    """
    def __init__(self, settings):
        self.settings = settings

    def get_question(self):
        questions_asked = []

        new_questions = Question.query.filter(~Question.id.any(questions_asked))

        # filter / order and limit to get maximal split
        question_query = new_questions.all()

        question = question_query.first()
        options = ['Yes', 'No', 'Unsure']

        # print('Q: {}'.format(question))
        # print('A: {}'.format(options))
        return (question.question, options)

    def give_answer(self, question, answer):
        print('Q: {}'.format(question))
        print('A: {}'.format(answer))

    def guesses(self):
        guesses = [("kangaroo", 0.5), ("dog", 0.9), ("rabbit", 0.1)]
        guesses = [("kangaroo", 10.5), ("dog", 0.9), ("rabbit", -0.1)]
        return sorted(guesses, key=lambda x: -x[1])