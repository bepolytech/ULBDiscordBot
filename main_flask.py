from flask import Flask, render_template
from flask_login import LoginManager # TODO: user session management
from user import User # TODO:
  
app = Flask(__name__)
login_manager = LoginManager()
login_manager.init_app(app)
 
@app.route("/") 
def home(): 
    return render_template("home.html", user=user) 
  
  
@app.route("/discord-login") 
@login_required
def discord_login(): 
    if user.site_lang = "en":
        return render_template("discord-login_en.html"; user=user)
    else:
        return render_template("discord-login_fr.html", user=user) 
  
  
@app.route("/user")
@login_required
def user(): 
    if user.site_lang = "en":
        return render_template("user_en.html", user=user)
    else:
        return render_template("user_fr.html", user=user)
  
@app.route("/test") 
def test():
    test_user = User(
        "Test",
        "test@example.com"
    )
    return render_template("test.html", user=test_user)
  
  
@app.route("/bot") 
def bot(): 
    # TODO: check if bot status is online
    bot_status = "Online"
    return render_template("bot.html", status=bot_status) 
  
  
if __name__ == "__main__":
    # TODO: run Disnake and Flask in different threads ? asyncio ?
    app.run(debug=False)
    

