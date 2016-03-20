
import os.path
import tornado.escape
import tornado.web
import tornado.wsgi
import services
import commonWords
import settings
import cryptAES

# actually unused, but could be quickly added to require login to the admin area.
from google.appengine.api import users

# choose datastore based on settings
if settings.selected_datastor_type==0:
    # MySQLdb import failing to install on my mac. Will use NDB for now
    dbi = services.DataInterfaceMySQL()
else:
    dbi = services.DataInterfaceGAE()


class BaseHandler(tornado.web.RequestHandler):
    """Implements Google Accounts authentication methods.
    Well, actually I haven't, but this is where we could.
    """
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

class AdminHandler(BaseHandler):
    def get(self):
        """
        Render th page which lists the counts, in an orderable searchable list
        TODO: this should be login secured ideally
        """
        wrs_enc = dbi.list()
        ciph = cryptAES.AESCipher()
        wrs = [{"word":ciph.decrypt(wr.encrypted_word), "count": wr.count} for wr in wrs_enc]
        self.render("admin.html", wrs=wrs)


class HomeHandler(BaseHandler):
    def get(self):
        """
        Main handler for queries against the system on the home page.
        """
        q = self.get_argument("q", default="", strip=True)
        resp = ""
        error=""
        instruction=""

        #  scraping can be trixy. Some servers try to prevent it, so a little error handling required
        #  Also users may fail to input a valid input
        #  TODO: ideally we should have a little client side validation here.
        #  I've used HTML5 url validation but older browser will not benefit from this.
        try:
            raw_html = services.scrape(q)
        except Exception as e:

            if q=="":
                instruction="Please enter a URL"
            else:
                error = "Could not fetch URL. Please check the address is correct."
            #  Not sure I need to send all the parameters every time. This could be cleaner
            self.render("home.html", top100=[], max_freq=0, error=error, instruction=instruction)
        try:
            resp = services.html2text(raw_html)
        except Exception as e:
            error = "Could not parse that page. Try another."
            self.render("home.html", top100=[], max_freq=0, error=error, instruction=instruction)


        #  punctuation can cause the same word to get handled as many. so let strip it
        #  translate() is faster, but seems hacky. Still possibly better.
        for ch in commonWords.superfluous_characters:
            resp = resp.replace(ch, "")

        #  get case insensitive at the list
        significant_words = services.str2words(resp.lower())
        #removing the most common prepositions, articles and top X words used in English
        to_exclude = commonWords.preps + commonWords.arts + commonWords.word_list[:50]
        significant_words = [w for w in significant_words if len(w) > 1 and w not in to_exclude]

        #  finally we have some freqs
        top100 = services.topFreq(significant_words, 100)

        #  persist the top selection
        for wrt in top100:
            dbi.insert(wrt[0], wrt[1])

        #  send the max value to the template so we can normalize the rendered sizes a little
        max_freq = max([v for k,v in top100])
        self.render("home.html", top100=top100, max_freq=max_freq, error=error, instruction=instruction)

settings = {
    "title": u"Word Freq",
    "template_path": os.path.join(os.path.dirname(__file__), "templates"),
    "xsrf_cookies": True,
}
application = tornado.web.Application([
    (r"/", HomeHandler),
    (r"/admin", AdminHandler),
], **settings)

application = tornado.wsgi.WSGIAdapter(application)