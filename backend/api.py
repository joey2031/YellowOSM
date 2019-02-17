import time
import json
import logging
import os

import responder
from dotenv import load_dotenv

from lib.geo58 import Geo58

log = logging.getLogger(__name__)
log.setLevel('DEBUG')

load_dotenv()
SHORT_URL_REDIRECT_URL = os.getenv("SHORT_URL_REDIRECT_URL")

api = responder.API(cors=True)

@api.route("/api/")
@api.route("/api/hello")
def hello_world(req, resp):
    resp.text = "Hello World!"


@api.route("/api/hello/{user}")
@api.route("/api/hello/{user}/json")
def hello_json(req, resp, *, user):
    user = user.strip("/")
    resp.media = {"hello": user}

@api.route("/api/error")
def error(req, resp):
    resp.headers['X-Answer'] = '42'
    resp.status_code = 415
    resp.text = "ooops"

@api.route("/api/expensive-task")
async def handle_task(req, resp):

    @api.background.task
    def process_data(data):
        """This can take some time"""
        print("starting background task...")
        time.sleep(5)
        print("finished background task...")


    # parse incoming data form-encoded
    # json and yaml automatically work
    try:
        data = await req.media()
    except json.decoder.JSONDecodeError:
        data = None
        pass

    process_data(data)

    resp.media = {'success': True}

@api.route("/api/coords_to_geo58/{zoom}/{x}/{y}")
async def convertCoordsToGeo58(req, resp, *, zoom, x, y):
    try:
        g58 = Geo58(zoom=zoom, lat=x, lon=y.strip(' /'))
    except Geo58.Geo58Exception as ex:
        log.debug("geo58_to_coords: invalid short code: %s", ex)
        resp.status_code = 406
        resp.text = "Error: Not Acceptable: coordinates invalid. [{}]".format(ex)
        return
    resp.media = {'g58': g58.get_geo58()}

@api.route("/api/geo58_to_coords/{geo58_str}")
async def convertGeo58ToCoords(req, resp, *, geo58_str):
    try:
        g58 = Geo58(g58=geo58_str)
    except Geo58.Geo58Exception as ex:
        log.debug("geo58_to_coords: invalid short code: %s", ex)
        resp.status_code = 400
        resp.text = "Error: Bad Request: invalid short code. [{}]".format(ex)
        return
    zoom,x,y = g58.get_coordinates()
    resp.media = {'zoom': zoom,'x': x, 'y': y}

@api.route("/api/redirect_geo58/{geo58_str}")
async def convertGeo58ToCoords(req, resp, *, geo58_str):
    geo58_str = str(geo58_str)
    index = geo58_str.find(';',0,12)
    appendix = None if index == -1 else geo58_str[index:]
    geo58 = geo58_str if index == -1 else geo58_str[:index]
    try:
        g58 = Geo58(g58=geo58)
    except Geo58.Geo58Exception as ex:
        log.debug("redirect_geo58: invalid short code: %s", ex)
        resp.status_code = 400
        resp.text = "Error: Bad Request: invalid short code. [{}]".format(ex)
        return
    zoom,x,y = g58.get_coordinates()
    redir_url = SHORT_URL_REDIRECT_URL.format(zoom=zoom, x=x, y=y) + appendix
    log.debug("redirect to --> %s",redir_url)
    resp.status_code = 302
    resp.headers['Location'] = redir_url

if __name__ == '__main__':
    api.run()
