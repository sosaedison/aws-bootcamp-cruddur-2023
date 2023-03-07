import logging
import os
from time import strftime

import rollbar
import rollbar.contrib.flask
import watchtower
from aws_xray_sdk.core import xray_recorder
from aws_xray_sdk.ext.flask.middleware import XRayMiddleware
from flask import Flask, got_request_exception, request
from flask_cors import CORS, cross_origin
from lib.cognito_token_verification import (
    CognitoJwtToken,
    TokenVerifyError,
    extract_access_token,
)
from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.flask import FlaskInstrumentor
from opentelemetry.instrumentation.requests import RequestsInstrumentor
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from services.create_activity import *
from services.create_message import *
from services.create_reply import *
from services.home_activities import *
from services.message_groups import *
from services.messages import *
from services.notification_activities import *
from services.search_activities import *
from services.show_activity import *
from services.user_activities import *

# Configuring Logger to Use CloudWatch
# logger = logging.getLogger(__name__)
# logger.setLevel(logging.DEBUG)
# console_handler = logging.StreamHandler()
# cw_handler = watchtower.CloudWatchLogHandler(log_group="cruddur")
# logger.addHandler(console_handler)
# logger.addHandler(cw_handler)
# logger.info("some message")

# xray_url = os.getenv("AWS_XRAY_URL")
# xray_recorder.configure(service="backend-flask", dynamic_naming=xray_url)


# HONEYCOMB INSTRUMENTATION
# provider = TracerProvider()
# processor = BatchSpanProcessor(OTLPSpanExporter())
# provider.add_span_processor(processor)
# trace.set_tracer_provider(provider)
# tracer = trace.get_tracer(__name__)

app = Flask(__name__)

# XRAY INSTRUMENTATION
# XRayMiddleware(app, xray_recorder)

# HONEYCOMB INSTRUMENTATION
# FlaskInstrumentor().instrument_app(app)
# RequestsInstrumentor().instrument()

frontend = os.getenv("FRONTEND_URL")
backend = os.getenv("BACKEND_URL")
origins = [frontend, backend]
cors = CORS(
    app,
    resources={r"/api/*": {"origins": origins}},
    headers=["Content-Type", "Authorization"],
    expose_headers="Authorization",
    methods="OPTIONS,GET,HEAD,POST",
)


cognito_jwt_token = CognitoJwtToken(
    user_pool_id=os.environ.get("AWS_COGNITO_USER_POOL_ID"),
    user_pool_client_id=os.environ.get("AWS_COGNITO_USER_POOL_CLIENT_ID"),
    region=os.getenv("AWS_DEFAULT_REGION"),
)

# CLOUDWATCH LOGS TEST
# @app.after_request
# def after_request(response):
#     timestamp = strftime("[%Y-%b-%d %H:%M]")
#     logger.error(
#         "%s %s %s %s %s %s",
#         timestamp,
#         request.remote_addr,
#         request.method,
#         request.scheme,
#         request.full_path,
#         response.status,
#     )
#     return response


# ROLLBAR INSTRUMENTATION
# @app.before_first_request
# def init_rollbar():
#     """init rollbar module"""
#     rollbar.init(
#         # access token
#         access_token=os.getenv("ROLLBAR_ACCESS_TOKEN"),
#         # environment name
#         environment="production",
#         # server root directory, makes tracebacks prettier
#         root=os.path.dirname(os.path.realpath(__file__)),
#         # flask already sets up logging
#         allow_logging_basic_config=False,
#     )

#     # send exceptions from `app` to rollbar, using flask's signal system.
#     got_request_exception.connect(rollbar.contrib.flask.report_exception, app)


# @app.route("/rollbar/test")
# def rollbar_test():
#     rollbar.report_message("Hello World!", "warning")
#     return "Hello World!"


@app.route("/api/message_groups", methods=["GET"])
def data_message_groups():
    user_handle = "andrewbrown"
    model = MessageGroups.run(user_handle=user_handle)
    if model["errors"] is not None:
        return model["errors"], 422
    else:
        return model["data"], 200


@app.route("/api/messages/@<string:handle>", methods=["GET"])
def data_messages(handle):
    user_sender_handle = "andrewbrown"
    user_receiver_handle = request.args.get("user_reciever_handle")

    model = Messages.run(
        user_sender_handle=user_sender_handle, user_receiver_handle=user_receiver_handle
    )
    if model["errors"] is not None:
        return model["errors"], 422
    else:
        return model["data"], 200
    return


@app.route("/api/messages", methods=["POST", "OPTIONS"])
@cross_origin()
def data_create_message():
    user_sender_handle = "andrewbrown"
    user_receiver_handle = request.json["user_receiver_handle"]
    message = request.json["message"]

    model = CreateMessage.run(
        message=message,
        user_sender_handle=user_sender_handle,
        user_receiver_handle=user_receiver_handle,
    )
    if model["errors"] is not None:
        return model["errors"], 422
    else:
        return model["data"], 200
    return


@app.route("/api/activities/home", methods=["GET"])
def data_home():
    access_token = extract_access_token(request.headers)
    try:
        claims = cognito_jwt_token.verify(token=access_token)
        # authenticated request
        app.logger.debug("authenticated")
        app.logger.debug(claims)
        app.logger.debug(claims["username"])
        data = HomeActivities.run(cognito_user_id=claims["username"])
    except TokenVerifyError as e:
        # unauthenticated request
        app.logger.debug(e)
        app.logger.debug("unauthenticated")
        data = HomeActivities.run()
    return data, 200


@app.route("/api/activities/@<string:handle>", methods=["GET"])
def data_handle(handle):
    model = UserActivities.run(handle)
    if model["errors"] is not None:
        return model["errors"], 422
    else:
        return model["data"], 200


@app.route("/api/activities/search", methods=["GET"])
def data_search():
    term = request.args.get("term")
    model = SearchActivities.run(term)
    if model["errors"] is not None:
        return model["errors"], 422
    else:
        return model["data"], 200
    return


@app.route("/api/activities", methods=["POST", "OPTIONS"])
@cross_origin()
def data_activities():
    user_handle = "andrewbrown"
    message = request.json["message"]
    ttl = request.json["ttl"]
    model = CreateActivity.run(message, user_handle, ttl)
    if model["errors"] is not None:
        return model["errors"], 422
    else:
        return model["data"], 200
    return


@app.route("/api/activities/<string:activity_uuid>", methods=["GET"])
def data_show_activity(activity_uuid):
    data = ShowActivity.run(activity_uuid=activity_uuid)
    return data, 200


@app.route("/api/activities/<string:activity_uuid>/reply", methods=["POST", "OPTIONS"])
@cross_origin()
def data_activities_reply(activity_uuid):
    user_handle = "andrewbrown"
    message = request.json["message"]
    model = CreateReply.run(message, user_handle, activity_uuid)
    if model["errors"] is not None:
        return model["errors"], 422
    else:
        return model["data"], 200
    return


@app.route("/api/activities/notifications", methods=["GET"])
def data_notifications():
    data = NotificationActivities.run()

    return data


if __name__ == "__main__":
    app.run(debug=True)
