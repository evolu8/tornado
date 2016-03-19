
import os.path
import tornado.escape
import tornado.web
import tornado.wsgi
import services
import commonWords


from google.appengine.api import users


class BaseHandler(tornado.web.RequestHandler):
    """Implements Google Accounts authentication methods."""
    def get_current_user(self):
        user = users.get_current_user()
        if user: user.administrator = users.is_current_user_admin()
        return user

    def get_login_url(self):
        return users.create_login_url(self.request.uri)

    def get_template_namespace(self):
        # Let the templates access the users module to generate login URLs
        ns = super(BaseHandler, self).get_template_namespace()
        ns['users'] = users
        return ns


class HomeHandler(BaseHandler):
    def get(self):
        q = self.get_argument("q", default="", strip=True)
        resp = ""
        error=""
        instruction=""
        try:
            raw_html = services.scrape(q)
        except Exception as e:

            if q=="":
                instruction="Please enter a URL"
            else:
                error = "Could fetch URL. Please check it is correct."
            self.render("home.html", top100=[], max_freq=0, error=error, instruction=instruction)
        try:
            resp = services.html2text(raw_html)
        except Exception as e:
            error = "Could not parse that page. Try another."
            self.render("home.html", top100=[], max_freq=0, error=error, instruction=instruction)

        for ch in commonWords.superfluous_characters:
            resp = resp.replace(ch, "")

        significant_words = services.str2words(resp.lower())

        significant_words = [w for w in significant_words if len(w) > 1 and w not in commonWords.word_list[:100]]

        top100 = services.topFreq(significant_words, 100)
        max_freq = max([v for k,v in top100])
        self.render("home.html", top100=top100, max_freq=max_freq, error=error, instruction=instruction)

settings = {
    "title": u"Word Freq",
    "template_path": os.path.join(os.path.dirname(__file__), "templates"),
    "xsrf_cookies": True,
}
application = tornado.web.Application([
    (r"/", HomeHandler)
], **settings)

application = tornado.wsgi.WSGIAdapter(application)