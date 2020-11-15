import os
from flask import Flask, request, abort, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
import random

from models import setup_db, Question, Category

QUESTIONS_PER_PAGE = 10


def paginate_questions(request, selection):
    page = request.args.get('page', 1, type=int)
    start = (page - 1) * QUESTIONS_PER_PAGE
    end = start + QUESTIONS_PER_PAGE
    formatted_questions = [question.format() for question in selection]
    questions = formatted_questions[start:end]
    return questions


def formatted_categories():
    categories = Category.query.all()
    formated_categories = {}
    for category in categories:
        formated_categories[category.id] = category.type

    return formated_categories


def create_app(test_config=None):
    app = Flask(__name__)
    setup_db(app)
    # CORS(app)
    cors = CORS(app, resources={r"/api/*": {"origins": "*"}})

    '''
  Set up CORS. Allow '*' for origins.
  '''

    '''
  Use the after_request decorator to set Access-Control-Allow
  '''

    @app.after_request
    def after_request(response):
        response.headers.add(
            'Access-Control-Allow-Headers',
            'Content-Type,Authorization,true')
        response.headers.add(
            'Access-Control-Allow-Methods',
            'GET,PUT,POST,DELETE,OPTIONS')
        return response

    '''
  handle GET requests for all available categories.
  '''

    @app.route('/categories')
    def get_categories():
        categories = formatted_categories()

        if len(categories) == 0:
            abort(404)

        return jsonify({
            "success": True,
            "categories": categories,
            "total_categories": len(categories)
        })

    '''
  handle GET requests for questions,
  including pagination (every 10 questions).
  '''

    @app.route('/questions')
    def get_questions():
        questions = Question.query.order_by(Question.id).all()
        if questions is None:
            abort(404)

        formatted_questions = paginate_questions(request, questions)
        categories = formatted_categories()
        return jsonify({
            'success': True,
            'questions': formatted_questions,
            'total_questions': len(Question.query.all()),
            'categories': categories,
            'current_category': None
        })

    '''
  DELETE question using a question ID.
  '''

    @app.route('/questions/<int:question_id>', methods=['DELETE'])
    def delete_question(question_id):
        try:
            question = Question.query.filter(
                Question.id == question_id).one_or_none()

            if question is None:
                abort(404)

            question.delete()
            selection = Question.query.all()
            questions = paginate_questions(request, selection)

            return jsonify({
                'success': True,
                'deleted': question_id,
                'questions': questions,
                'total_questions': len(questions)
            })

        except BaseException:
            abort(422)

    '''
  POST a new question,
  which will require the question and answer text,
  category, and difficulty score.

  POST endpoint to get questions based on a search term.
  '''

    @app.route('/questions', methods=['POST'])
    def post_questions():
        body = request.get_json()
        search = body.get('searchTerm', None)
        question = body.get('question', None),
        answer = body.get('answer', None),
        difficulty = body.get('difficulty', None),
        category = body.get('category', None),

        if search is not None:
            selection = Question.query.order_by(
                Question.id).filter(
                Question.question.ilike(
                    '%{}%'.format(search))).all()
            if len(selection) == 0:
                abort(404)
            current_questions = paginate_questions(request, selection)

            return jsonify({
                'success': True,
                'questions': current_questions,
                'total_questions': len(selection),
            })

        else:
            if question is not None and answer is not None and \
               difficulty is not None and category is not None:
                try:
                    question = Question(
                        question=question,
                        answer=answer,
                        difficulty=difficulty,
                        category=category)
                    question.insert()
                    return jsonify({
                        "success": True,
                        "message": "Question have been created successfully",
                        'question': question.format()
                    })
                except BaseException:
                    abort(422)

    '''
    GET endpoint to get questions based on category.
  '''

    @app.route('/categories/<category_id>/questions', methods=['GET'])
    def questions_by_category(category_id):
        category = Category.query.filter(
            Category.id == category_id).one_or_none()
        if category is None:
            abort(404)

        questions = Question.query.filter(
            Question.category == category_id).all()
        questions_all = paginate_questions(request, questions)

        return jsonify({
            "success": True,
            'questions': questions_all,
            'totalQuestions': len(questions),
            'currentCategory': category.format()
        }), 200

    '''
  POST endpoint to get questions to play the quiz.
  '''

    @app.route('/quizzes', methods=['POST'])
    def make_quizzes():

        body = request.get_json()
        previousQuestions = body.get('previous_questions', [])
        quizCategory = body.get('quiz_category', None)

        if previousQuestions is None or quizCategory is None:
            abort(404)

        if quizCategory['id'] != 0:
            questions = Question.query.filter_by(
                category=quizCategory['id']).all()
        else:
            questions = Question.query.all()

        if len(previousQuestions) == len(questions):
            quizQuestion = None
        else:
            questionsid = []
            for q in questions:
                questionsid.append(q.format()['id'])

            for questionID, question in zip(questionsid, questions):
                if questionID not in previousQuestions:
                    quizQuestion = question.format()
                    previousQuestions.append(questionID)
                    break

        return jsonify({
            'success': True,
            'question': quizQuestion,
            'previous_questions': previousQuestions
        })

    '''
  error handlers for all expected errors
  including 404 and 422.
  '''

    @app.errorhandler(404)
    def not_found(error):
        return jsonify({
            'success': False,
            'error': 404,
            "message": "Resource not found"
        }), 404

        @app.errorhandler(422)
        def unprocessable(error):
            return jsonify({
                "success": False,
                "error": 422,
                "message": "Unprocessable"
            }), 422

        @app.errorhandler(400)
        def bad_request(error):
            return jsonify({
                "success": False,
                "error": 400,
                "message": "Bad request"
            }), 400

    return app
