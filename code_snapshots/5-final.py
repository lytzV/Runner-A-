import os
from flask import Flask, render_template, g, request
import requests
import random

app = Flask(__name__)

@app.route('/')
def index(name=None):
    return render_template('index.html')

@app.route('/categories')
def categories():
    categories = requests.get('http://jservice.io/api/categories/', data={'count': 6})
    categories_json = categories.json()
    return render_template('categories.html', categories_json=categories_json)

@app.route('/question')
@app.route('/question/<category_id>')
def get_random_question(category_id=None):
    if category_id:
        question_list = requests.get('http://jservice.io/api/category', data={'id': category_id}).json()['clues']
        question_obj = random.choice(question_list)
    else:
        question_obj = requests.get('http://jservice.io/api/random').json()[0]
    question, answer = question_obj['question'], question_obj['answer']
    return render_template('question.html', question=question, answer=answer)


@app.route('/answer')
def check_answer():
    input_answer = request.args['input_answer']
    real_answer = request.args['real_answer']
    correct_answer_string = 'Correct' if input_answer.lower() == real_answer.lower() else 'Incorrect'
    return render_template('answer.html', input_answer=input_answer, real_answer=real_answer, correct_answer_string=correct_answer_string)

if __name__ == '__main__':
    app.run(debug=True)
