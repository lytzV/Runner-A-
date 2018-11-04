import os
from flask import Flask, render_template, g, request
import requests
import random

app = Flask(__name__)

@app.route('/')
def home():
    return 'home'

@app.route('/categories')
def category():
    categories = requests.get('http://jservice.io/api/categories', {
        'count': 10
    })
    category_json = categories.json()
    return categories.text


@app.route('/question')
@app.route('/question/<category_id>')
def get_random_question(category_id=None):
    if category_id:
        question_list = requests.get('http://jservice.io/api/category', data={'id': category_id}).json()['clues']
        question_obj = random.choice(question_list)
    else:
        question_obj = requests.get('http://jservice.io/api/random').json()[0]
    question, answer = question_obj['question'], question_obj['answer']
    return question + ', ' + answer


@app.route('/answer')
def check_answer():
    real_answer = 'Yes'
    input_answer = 'Yes'
    if real_answer.lower() == input_answer.lower():
        return 'Correct'
    else :
        return 'Incorrect'

if __name__ == '__main__':
    app.run(debug = True)
