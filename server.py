from flask import Flask, render_template, request, jsonify, url_for, send_file
from sqlalchemy import text
from flask_sqlalchemy import SQLAlchemy
from math import pi as pi
import datetime, hashlib, os

app = Flask(__name__)

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_DATABASE_URI'] ='sqlite:///db.sqlite3'

db = SQLAlchemy(app)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50))
    password = db.Column(db.String(64))
    email = db.Column(db.String(64))
    isBanned = db.Column(db.String, default='0')
    score = db.Column(db.Integer, default=0)
    accurancy = db.Column(db.Integer, default=100)
    playcount = db.Column(db.Integer, default=100)


class Banned_Maps(db.Model):
    mapHash = db.Column(db.String(32), primary_key=True)
    reason = db.Column(db.String)


class Scores(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    mapHash = db.Column(db.String(32))
    playerID = db.Column(db.Integer)
    score = db.Column(db.Integer)
    combo = db.Column(db.Integer)
    count50 = db.Column(db.Integer)
    count100 = db.Column(db.Integer)
    count300 = db.Column(db.Integer)
    countMiss = db.Column(db.Integer)
    countKatu = db.Column(db.Integer)
    countGeki = db.Column(db.Integer)
    perfect = db.Column(db.Integer)
    mods = db.Column(db.Integer)
    isPass = db.Column(db.Integer)
    outdated = db.Column(db.Integer, default=0)



class Posts(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    postby = db.Column(db.Integer, default=1)
    username = db.Column(db.String(1024))
    postTitle = db.Column(db.String(1024))
    post = db.Column(db.String(1024))


@app.route('/post', methods=['GET', 'POST'])
def makePost():
    if request.method == 'GET':
        post = Posts.query.all()
        return render_template('post.html', posts=post)

    if request.method == 'POST':
        title = request.values.get('title')
        by = request.values.get('by')
        postText = request.values.get('post')

        user = User.query.filter_by(id=by).first()

        post = Posts(postby=by, username=user.username, postTitle=title, post=postText)
        db.session.add(post)
        db.session.commit()

        return 'Done!'




@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.values.get('username')
        email = request.values.get('email')
        password = hashlib.md5(request.values.get('password').encode('utf-8')).hexdigest()
        regUser = User(username=username, password=password, email=email)
        
        if bool(User.query.filter_by(username=username).first()):
            return '<h1>no lol</h1>'
        
        db.session.add(regUser)
        db.session.commit()
        return 'Registered!'

    if request.method == 'GET':
        return render_template('register.html')



@app.route('/leaderboard')
def leaderboard():
    user = User.query.all()
    return render_template('leaderboard.html', leaderboard=user)

@app.route('/u/<userID>')
def showUserPage(userID):
    userData = User.query.filter_by(id=userID).first()
    plays = getPlay(userID)
    return render_template('userpage.html', user=userData, plays=plays)


@app.route('/')
def testAcc():
    post = Posts.query.all()
    return render_template('home.html', posts=post)

@app.route('/about')
def about():
    return render_template('about.html')
    
@app.route('/faq')
def faq():
    return render_template('faq.html')





# game backend starts here
@app.route('/avatar/<int:uid>')
def serveAvatar(uid):
    if os.path.isfile("{}/{}.png".format('static/avatar', uid)):
        avatarid = uid
    else:
        avatarid = -1

    # Serve actual avatar or default one
    return send_file("{}/{}.png".format('static/avatar', avatarid))

@app.route('/web/osu-login.php', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.values.get('username')
        password = request.values.get('password')
    
    if request.method == 'GET':
        username = request.args.get('username')
        password = request.args.get('password')


    if len(password) == 32:
        userData = User.query.filter_by(username=username).first() # get user data

        if userData == None:
            return '0'
        elif userData.isBanned == '1':
            return '0'

        return '1' if password == userData.password else '0'


    return '0' # if failed everything

@app.route('/web/osu-getscores.php')
@app.route('/web/osu-getscores3.php')
def getLeaderboard():
    mapHash = request.args.get('c')
    mapScore = Scores.query.filter_by(mapHash=mapHash).order_by(text('score desc')).all()
    scoresText = ''
    existedUser = []

    #print(mapHash)



    if mapHash == None or mapScore == []:
        return ''

    for x in mapScore:
        if x.outdated == '1': continue
        #if x.isPass == 0: continue
        if x.playerID in existedUser: continue
        userData = User.query.filter_by(id=x.playerID).first()
        perfect = 'False'
        name = userData.username
        name += f' ({calcPlay(x.id)}%)'
        if x.perfect != 0:
            perfect = 'True'

        if x.isPass == 0: name += ' [FAILED]'

        scoresText += f'{x.id}:{name}:{x.score}:{x.combo}:{x.count50}:{x.count100}:{x.count300}:{x.countMiss}:{x.countKatu}:{x.countGeki}:{perfect}:{x.mods}\n'
        existedUser.append(x.playerID)
    
    return scoresText


@app.route('/web/osu-submit.php', methods=['POST'])
def submitScore():
    print(request.files)
    score = request.values.get('score').split(':')
    password = request.values.get('pass') # password for the user

    userData = User.query.filter_by(username=score[1]).first()
    #print('aaaaaa ->>',userData)

    if userData != []:
        if password != userData.password:
            return ''

        if score[14].lower() == 'true': # if pass add score and playcount
            userData.playcount += 1
            userData.score += int(score[9])
            db.session.commit()

        playerScore = Scores.query.filter_by(playerID=userData.id).first()
        if bool(playerScore):
            #print('aaa')
            if int(playerScore.score) > int(score[9]): return ''

            playerScore.outdated = '1'
            db.session.commit()

        perfect = 0
        isPass = 0

        if score[11].lower() == 'true':
            perfect = 1

        if score[14].lower() == 'true':
            isPass = 1
        
        SubmitData = Scores(mapHash=score[0], playerID=userData.id, score=score[9], combo=score[10], count50=score[5], count100=score[4], count300=score[3], countMiss=score[8], countKatu=score[7], countGeki=score[6],perfect=perfect, mods=score[13], isPass=isPass)
        db.session.add(SubmitData)
        db.session.commit()

        userData.accurancy = calculateOverallAcc(userData.id)
        db.session.commit()

        return ''

@app.template_filter()
def accRound(value):
    return str(value)[:5]
        
    
def calculateOverallAcc(playerID):
    userPlay = Scores.query.filter_by(playerID=playerID).order_by(text('score desc')).all()
    isAlreadyPlayed = []
    allAcc = []
    avrgAcc = 0

    for score in userPlay:
        allAcc.append(calcAcc(int(score.count300),int(score.count100), int(score.count50), int(score.countMiss)))

    

    
    return sum(allAcc)/len(allAcc)



def calcAcc(count300: int, count100: int, count50: int,countmiss: int):
        ### MATH SHIT
        acc =  ((count300 * 300 + count100 * 100 + count50 * 50 + countmiss * 0)/((count300 + count100 + count50 + countmiss) * 300) * 100) 

        return acc

@app.template_filter()
def calcPlay(playID):
        play = Scores.query.filter_by(id=playID).first()
        count300 = play.count300
        count100 = play.count100
        count50 = play.count50
        countmiss = play.countMiss
        ### MATH SHIT
        acc =  ((count300 * 300 + count100 * 100 + count50 * 50 + countmiss * 0)/((count300 + count100 + count50 + countmiss) * 300) * 100) 

        return round(acc)

def getPlay(playerID):
    userPlay = Scores.query.filter_by(playerID=playerID).order_by(text('score desc')).all()
    isAlreadyPlayed = []
    plays = []
    avrgAcc = 0

    for score in userPlay:
        if score.mapHash in isAlreadyPlayed: continue
        plays.append(score)
        isAlreadyPlayed.append(score.mapHash)


    return plays


if __name__ == "__main__":
    app.run(port=80, debug=True)

