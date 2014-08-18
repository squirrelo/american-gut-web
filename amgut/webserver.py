from os.path import dirname, join
from base64 import b64encode
from uuid import uuid4

import tornado.httpserver import HTTPServer
import tornado.ioloop import IOLoop
from tornado.web import Application, StaticFileHandler
import tornado.websocket
from tornado.options import define, options, parse_command_line

from amgut.base_handlers import MainHandler, NoPageHandler

define("port", default=8888, help="run on the given port", type=int)

DIRNAME = dirname(__file__)
STATIC_PATH = join(DIRNAME, "static")
TEMPLATE_PATH = join(DIRNAME, "templates")  # base folder for webpages
RES_PATH = join(DIRNAME, "results")
COOKIE_SECRET = b64encode(uuid4().bytes + uuid4().bytes)
DEBUG = True


class Application(Application):
    def __init__(self):
        handlers = [
            (r"/", MainHandler),
            (r"/results/(.*)", StaticFileHandler, {"path": RES_PATH}),
            (r"/static/(.*)", StaticFileHandler, {"path": STATIC_PATH}),
            # 404 PAGE MUST BE LAST IN THIS LIST!
            (r".*", NoPageHandler)
        ]
        settings = {
            "template_path": TEMPLATE_PATH,
            "debug": DEBUG,
            "cookie_secret": COOKIE_SECRET,
            "login_url": "/auth/login/"
        }
        Application.__init__(self, handlers, **settings)


def main():
    parse_command_line()
    http_server = HTTPServer(Application())
    http_server.listen(options.port)
    print("Tornado started on port", options.port)
    IOLoop.instance().start()

if __name__ == "__main__":
    main()
