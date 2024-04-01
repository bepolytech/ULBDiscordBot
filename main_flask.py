from flask import Flask, render_template, request, session, redirect, url_for
#from flask_login import LoginManager # TODO: user session management
from user import User # TODO:
from cas import CASClient # use python-cas : https://djangocas.dev/blog/python-cas-flask-example/
import os

# TODO: add rate-limiting (Flask-Limiter ?)
  
app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY")
#login_manager = LoginManager()
#login_manager.init_app(app)

cas_client = CASClient(
    version=3, # 2 ?
    service_url=os.getenv("CAS_SERVICE_URL") # i.e.: service_url='http://localhost:5000/login?next=%2Fprofile',
    server_url=os.getenv("CAS_SERVER_URL") # i.e.: server_url='https://django-cas-ng-demo-server.herokuapp.com/cas/'
)

@app.route("/") 
def home(): 
    return render_template("home.html")#, user=user)


@app.route('/login')
def login():
    if "username" in session:
        # Already logged in
        if db.get(session["username"]) = None:
            # Not linked to Discord yet
            return redirect(url_for("discord_login"))
        else:
            return redirect(url_for("user"))

    next = request.args.get("next")
    ticket = request.args.get("ticket")
    if not ticket:
        # No ticket, the request come from end user, send to CAS login
        cas_login_url = cas_client.get_login_url()
        app.logger.debug('CAS login URL: %s', cas_login_url)
        return redirect(cas_login_url)

    # There is a ticket, the request come from CAS as callback.
    # need call `verify_ticket()` to validate ticket and get user profile.
    app.logger.debug('ticket: %s', ticket)
    app.logger.debug('next: %s', next)

    user, attributes, pgtiou = cas_client.verify_ticket(ticket)

    app.logger.debug(
        'CAS verify ticket response: user: %s, attributes: %s, pgtiou: %s', user, attributes, pgtiou)

    if not user:
        return 'Failed to verify ticket. Try to login again: <a href="/">Home</a>'
        #return redirect(url_for(("home"))
    else:  # Login successfully, redirect according `next` query parameter.
        session['username'] = user
        #session["attributes"] = attributes # TODO: check what attributes we get
        return redirect(next)

@app.route('/logout')
def logout():
    redirect_url = url_for('logout_callback', _external=True)
    cas_logout_url = cas_client.get_logout_url(redirect_url)
    app.logger.debug('CAS logout URL: %s', cas_logout_url)

    return redirect(cas_logout_url)

@app.route('/logout_callback')
def logout_callback():
    # redirect from CAS logout request after CAS logout successfully
    session.pop('username', None)
    #return 'Logged out from CAS. <a href="/login">Login</a>'
    return redirect(url_for(("home")) # ?
  
@app.route("/discord_login")
def discord_login(): 
    if user.site_lang = "en":
        return render_template("discord-login_en.html"; user=user)
    else:
        return render_template("discord-login_fr.html", user=user) 
  
  
@app.route("/user")
def user(method=['GET']):
    if 'username' in session:
        user = session["username"]
        #return 'Logged in as %s. <a href="/logout">Logout</a>' % session['username']
        if user.site_lang = "en":
            return render_template("user_en.html", user=user)
        else:
            return render_template("user_fr.html", user=user)
    else:
        return 'Login required. <a href="/">Back to Home</a>', 403
        #return redirect(url_for("home"))
  
@app.route("/test") 
def test():
    test_user = User(
        ulbid="test",
        email="test@example.com"
    )
    return render_template("test.html", user=test_user)

@app.route("/ping")
def ping():
    return "pong"
  
  
@app.route("/bot") 
def bot(): 
    # TODO: check if bot status is online
    bot_status = "Online"
    return render_template("bot.html", status=bot_status) 
  
  
if __name__ == "__main__":
    # TODO: run Disnake and Flask in different threads ? asyncio ?
    app.run(debug=False)
    

