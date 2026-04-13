import sqlite3
import logging
from flask import Flask, jsonify, json, render_template, request, url_for, redirect, flash
from werkzeug.exceptions import abort


app = Flask(__name__)
app.config['SECRET_KEY'] = 'your secret key'
app.config['DB_CONNECTION_COUNT'] = 0

formatter = logging.Formatter('%(asctime)s %(levelname)s: %(message)s')

app.logger.setLevel(logging.DEBUG)

werkzeug_logger = logging.getLogger('werkzeug')
werkzeug_logger.setLevel(logging.INFO)


def get_db_connection():
    app.config['DB_CONNECTION_COUNT'] += 1
    connection = sqlite3.connect('database.db')
    connection.row_factory = sqlite3.Row
    return connection


def get_post(post_id):
    connection = get_db_connection()
    post = connection.execute('SELECT * FROM posts WHERE id = ?',
                        (post_id,)).fetchone()
    connection.close()
    return post


@app.route('/')
def index():
    connection = get_db_connection()
    posts = connection.execute('SELECT * FROM posts').fetchall()
    connection.close()
    return render_template('index.html', posts=posts)


@app.route('/<int:post_id>')
def post(post_id):
    post = get_post(post_id)
    if post is None:
      app.logger.debug('404 not found')
      return render_template('404.html'), 404
    else:
      title = post['title']
      app.logger.debug(f"Viewing post: {title}")
      return render_template('post.html', post=post)


@app.route('/about')
def about():
    app.logger.debug("About page requested")
    return render_template('about.html')


@app.route('/create', methods=('GET', 'POST'))
def create():
    if request.method == 'POST':
        title = request.form['title']
        content = request.form['content']

        if not title:
            flash('Title is required!')
        else:
            connection = get_db_connection()
            connection.execute('INSERT INTO posts (title, content) VALUES (?, ?)',
                         (title, content))
            connection.commit()
            connection.close()
            app.logger.debug(f"Article {title} created")
            return redirect(url_for('index'))

    return render_template('create.html')


@app.route('/healthz')
def status():
    response = app.response_class(
            response=json.dumps({"result":"OK - healthy"}),
            status=200,
            mimetype='application/json'
    )
    return response
    

@app.route('/metrics')
def metrics():
    connection = get_db_connection()
    post_count = connection.execute(
        'SELECT COUNT(*) AS count FROM posts'
    ).fetchone()['count']
    connection.close()

    response = app.response_class(
        response=json.dumps({
            "status": "success",
            "code": 0,
            "data": {
                "db_connection_count": app.config['DB_CONNECTION_COUNT'],
                "post_count": post_count
            }
        }),
        status=200,
        mimetype='application/json'
    )
    return response


if __name__ == "__main__":
   app.run(host='0.0.0.0', port='3111', debug=True)
