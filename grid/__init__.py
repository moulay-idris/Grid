import os
import subprocess
import random
import json
from flask import Flask
import socket
from contextlib import closing
from flask_sqlalchemy import SQLAlchemy
from .grid import Grid
from .client import GridClient


def run_command(cmd="sleep 100"):
    _id = "process" + str(random.randint(0, 1e10))
    cmd = "screen -d -m -S " + str(_id) + " " + cmd

    process = subprocess.Popen(
        cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE
    )

    cmd = "screen -ls " + str(_id)
    process = subprocess.Popen(
        cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE
    )

    # wait for the process to terminate
    out, err = process.communicate()
    errcode = process.returncode

    pid = int(out.decode("ascii").split("\t")[1].split(".")[0]) + 1
    return pid


def kill_command(pid):
    cmd = "kill " + pid
    process = subprocess.Popen(
        cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE
    )

    # wait for the process to terminate
    out, err = process.communicate()
    errcode = process.returncode


def find_free_port():
    with closing(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as s:
        s.bind(("", 0))
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        return s.getsockname()[1]


def create_app(test_config=None):
    # create and configure the app
    app = Flask(__name__, instance_relative_config=True)

    app.config.from_mapping(
        SECRET_KEY="dev", DATABASE=os.path.join(app.instance_path, "grid.sqlite")
    )

    host = os.environ.get("GRID_HOST")
    port = os.environ.get("GRID_PORT")

    print("GRID_HOST:" + str(host))
    print("GRID_PORT:" + str(port))

    app.config["SQLALCHEMY_DATABASE_URI"] = (
        "sqlite:////tmp/openmined.grid." + str(host) + "." + str(port) + ".db"
    )

    db = SQLAlchemy(app)

    class User(db.Model):
        id = db.Column(db.Integer, primary_key=True)
        hostport = db.Column(db.String(200), unique=True, nullable=False)
        host = db.Column(db.String(80), unique=False, nullable=False)
        port = db.Column(db.String(120), unique=False, nullable=False)

        def __repr__(self):
            return "<User %r>" % self.username

    db.create_all()

    if test_config is None:
        # load the instance config, if it exists, when not testing
        app.config.from_pyfile("config.py", silent=True)
    else:
        # load the test config if passed in
        app.config.from_mapping(test_config)

    # ensure the instance folder exists
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    # a simple page that says hello
    @app.route("/get_connection")
    def get_connection():

        port = find_free_port()

        pid = run_command("python grid/create_process.py " + str(port))
        print("PID:" + str(pid))

        output = {}
        output["host"] = os.environ.get("GRID_HOST")
        output["port"] = port
        output["pid"] = pid

        return json.dumps(output)

    # @app.route("/kill_workers/")
    # def kill_workers():
    #     cmd = "ps -ef | grep create_process"
    #     process = subprocess.Popen(
    #         cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE
    #     )
    #
    #     # wait for the process to terminate
    #     out, err = process.communicate()
    #     for row in list(
    #         filter(
    #             lambda x: "SCREEN" in x and "grep" not in x,
    #             out.decode("ascii").split("\n"),
    #         )
    #     ):
    #         pid = str(int(row.split(" ")[1]) + 1)
    #         kill_connection(pid)
    #
    #     return "{}"

    #
    # @app.route("/kill_connection/<pid>")
    # def kill_connection(pid):
    #     kill_command(pid)
    #     return "Done!"
    #
    # def users2json(users):
    #
    #     out = list()
    #
    #     for user in users:
    #         dict = {}
    #         dict["host"] = str(user.host)
    #         dict["port"] = str(user.port)
    #         out.append(dict)
    #
    #     return json.dumps(out)
    #
    # @app.route("/get_known_workers/")
    # def get_know_workers():
    #
    #     return users2json(User.query.all())
    #
    # @app.route("/add_worker/<hostname>/<port>")
    # def add_worker(hostname, port):
    #
    #     try:
    #         new_user = User(
    #             host=hostname, port=port, hostport=str(hostname) + ":" + str(port)
    #         )
    #         db.session.add(new_user)
    #         db.session.commit()
    #
    #     except IntegrityError as e:
    #
    #         return json.dumps({"error": "Worker already known"})
    #
    #     return users2json(User.query.all())
    #
    return app
