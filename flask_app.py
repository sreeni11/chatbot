
# A very simple Flask Hello World app for you to get started with...

import json
import apiai
import os
import io
import base64
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
from matplotlib.figure import Figure
from flask import (
    Flask,
    g,
    redirect,
    render_template,
    request,
    session,
    url_for,
    jsonify,
    Response
)
from twilio.rest import Client
from twilio.http.http_client import TwilioHttpClient
import mysql.connector
from datetime import datetime
from cryptography.fernet import Fernet

pwd_key = b'WaHrN8rmYFu9eeB0wdiRe_LWWc9ccdyFhlwVQOuLHrY='
f = Fernet(pwd_key)

# Twilio account info
account_sid = "ACae795b7f6704bffa035dee82d42aa977"
auth_token = "351ab75940933239c879def17ea13d05"
account_num = "+12562914495"

proxy_client = TwilioHttpClient()
proxy_client.session.proxies = {'https': os.environ['https_proxy']}

client = Client(account_sid, auth_token, http_client=proxy_client)

# api.ai account info
CLIENT_ACCESS_TOKEN = "cf29375cefb345ca9add9743102aad1f"
ai = apiai.ApiAI(CLIENT_ACCESS_TOKEN)

#MySQL details
db_user = "sreeni11"
db_pwd = "485passwd"
db_host = "sreeni11.mysql.pythonanywhere-services.com"
db_database = "sreeni11$project"

def connect_db():
    con = None
    try:
        con = mysql.connector.connect(host = db_host,user = db_user,
        password = db_pwd, database = db_database)
        con.autocommit = False
    except mysql.connector.Error as err:
        print(err)
    #con = mysql.connector.connect(host = db_host,user = db_user,password = db_pwd, database = db_database)
    return con

def close_db(con):
    if con != None:
        try:
            con.close()
        except mysql.connector.Error as err:
            print(err)
    return

def get_ts():
    return datetime.now().strftime('%Y-%m-%d %H:%M:%S')

class User:
    def __init__(self,phone,password,fname,gender,admin):
        self.phone = phone
        self.password = hash(password)
        self.fname = fname
        self.gender = gender
        self.admin = admin
    def __repr__(self):
        return f'<Phone: {self.phone}>'

#Logged in users
users = []
#users.append(User(phone='2132466278',password='pwd',fname='John',admin='N'))

def getuser(ph):
    res = None
    for i in users:
        if i and i.phone == ph:
            return i
    return res

app = Flask(__name__)
app.secret_key = 'asdf082y3qbfasd8fygabslv0912h4bnaf'

@app.before_request
def before_request():
    g.user = None

    if 'user_phone' in session:
        con = connect_db()
        if con != None:
            cur = con.cursor(buffered=True)
            sql='SELECT * FROM user WHERE phone=' + str(session['user_phone'])
            try:
                #cur.execute(sql,val)
                cur.execute(sql)
                con.commit()
            except mysql.connector.Error as err:
                con.rollback()
                return ("<html><title>Login failed</title><body><h1>Server error in br"+str(err)+"</h1><a href='https://sreeni11.pythonanywhere.com/login'>Retry</a></body>")
            res = cur.fetchall()
            #return ("<html><title>Login failed</title><body><h1>test in br"+str(res)+','+str(sql)+"</h1><a href='https://sreeni11.pythonanywhere.com/login'>Retry</a></body>")
            user = User(res[0][0], res[0][1], res[0][2], res[0][4], 'Y' if res[0][5] == 'A' else 'N')
            #return ("<html><title>Login failed</title><body><h1>test in br"+str(res)+','+str(user)+"</h1><a href='https://sreeni11.pythonanywhere.com/login'>Retry</a></body>")
            cur.close()
            close_db(con)
        else:
            return ("<html><title>Login failed</title><body><h1>SQL connection in br error</h1><a href='https://sreeni11.pythonanywhere.com/login'>Retry</a></body>")
        g.user = user

@app.route('/checkph',methods=['POST'])
def checkph():
    ph = request.form['ph']
    con = connect_db()
    if con != None:
        cur = con.cursor(buffered=True)
        sql = "SELECT * FROM user WHERE phone="+str(ph)
        try:
            cur.execute(sql)
            con.commit()
        except mysql.connector.Error as err:
            con.rollback()
            cur.close()
            close_db(con)
            return jsonify(data='Error in check' + err, status=503)
        res = cur.fetchall()
        if res and len(res) > 0:
            cur.close()
            close_db(con)
            return jsonify(data='Y',status=200)
        else:
            cur.close()
            close_db(con)
            return jsonify(data='N',status=200)
        cur.close()
        close_db(con)
    else:
        return jsonify(data='Error', status=503)

@app.route('/signup',methods=['GET','POST'])
def signup():
    if request.method == 'POST':
        ph = request.form['phone']
        pwd = request.form['password']
        tmp = f.encrypt((pwd).encode()).decode()
        fname = request.form['fname']
        lname = request.form['lname']
        gender = request.form['gender']
        status = 'E'
        user = User(phone=ph,password=tmp,fname=fname,gender=gender,admin='N')
        con = connect_db()
        if con != None:
            cur = con.cursor(buffered=True)
            sql = "INSERT INTO user VALUES(%s,%s,%s,%s,%s,%s)"
            val = (ph,tmp,fname,lname,gender,status)
            try:
                cur.execute(sql,val)

            except mysql.connector.Error as err:
                con.rollback()
                cur.close()
                close_db(con)
                return ("<html><title>Signup failed</title><body><h1>Server error in signup "+str(err)+"</h1><a href='https://sreeni11.pythonanywhere.com/signup'>Retry</a></body></html>")
            session['user_phone'] = ph
            users.append(user)
            sql = "INSERT INTO activity VALUES(%s,%s,%s)"
            ts = get_ts()
            val = (user.phone,'Login',ts)
            try:
                cur.execute(sql,val)
                con.commit()
            except mysql.connector.Error as err:
                con.rollback()
                cur.close()
                close_db(con)
                return ("<html><title>Login failed</title><body><h1>Server error in store "+str(err)+"</h1><a href='https://sreeni11.pythonanywhere.com/login'>Retry</a></body></html>")
            cur.close()
            close_db(con)
            return redirect(url_for('profile'))
        else:
            return ("<html><title>Signup failed</title><body><h1>Server error in signup </h1><a href='https://sreeni11.pythonanywhere.com/signup'>Retry</a></body></html>")
    return render_template('signup.html')

@app.route('/login', methods=['GET','POST'])
def login():
    if request.method == 'POST':
        session.pop('user_phone',None)
        phone = request.form['phone']
        if len(phone) != 10:
            return ("<html><title>Login failed</title><body><h1>Invalid phone number</h1><a href='https://sreeni11.pythonanywhere.com/login'>Retry</a></body></html>")
        password = request.form['password']

        user = getuser(phone)

        con = connect_db()
        if con != None:
            cur = con.cursor(buffered=True)
            sql = "SELECT password,status,phone FROM user WHERE phone="+str(phone)
            try:
                cur.execute(sql)

            except mysql.connector.Error as err:
                con.rollback()
                cur.close()
                close_db(con)
                return ("<html><title>Login failed</title><body><h1>Server error in l "+str(err)+"</h1><a href='https://sreeni11.pythonanywhere.com/login'>Retry</a></body></html>")
            res = cur.fetchall()
            #return ("<html><title>Login failed</title><body><h1>Server error"+str(res[0][0])+"</h1><a href='https://sreeni11.pythonanywhere.com/login'>Retry</a></body></html>")
            tmp = f.decrypt((res[0][0]).encode()).decode()
            if res and len(res) > 0 and res[0][1] != 'D' and password == tmp:
                session['user_phone'] = res[0][2]
                if user == None:
                    sql='SELECT * FROM user WHERE phone=' + str(phone)
                    try:
                        cur.execute(sql)

                    except mysql.connector.Error as err:
                        con.rollback()
                        cur.close()
                        close_db(con)
                        return ("<html><title>Login failed</title><body><h1>Server error in br"+str(err)+"</h1><a href='https://sreeni11.pythonanywhere.com/login'>Retry</a></body>")
                    res = cur.fetchall()
                    #return ("<html><title>Login failed</title><body><h1>test in br"+str(res)+','+str(sql)+"</h1><a href='https://sreeni11.pythonanywhere.com/login'>Retry</a></body>")
                    user = User(res[0][0], res[0][1], res[0][2], res[0][4], 'Y' if res[0][5] == 'A' else 'N')
                users.append(user)
                sql = "INSERT INTO activity VALUES(%s,%s,%s)"
                ts = get_ts()
                val = (user.phone,'Login',ts)
                try:
                    cur.execute(sql,val)
                    con.commit()
                except mysql.connector.Error as err:
                    con.rollback()
                    cur.close()
                    close_db(con)
                    return ("<html><title>Login failed</title><body><h1>Server error in store "+str(val)+str(err)+"</h1><a href='https://sreeni11.pythonanywhere.com/login'>Retry</a></body></html>")
                return redirect(url_for('profile'))
            elif res[0][1] == 'D':
                return ("<html><title>Login failed</title><body><h1>Your account is disabled contact an admin</h1></body>")
            else:
                return ("<html><title>Login failed</title><body><h1>Incorrect password</h1><a href='https://sreeni11.pythonanywhere.com/login'>Retry</a></body></html>")
            #return redirect(url_for('login'))
            cur.close()
            close_db(con)
        else:
            return ("<html><title>Login failed</title><body><h1>SQL connection error in l</h1><a href='https://sreeni11.pythonanywhere.com/login'>Retry</a></body></html>")
    return render_template('login.html')

@app.route('/logout', methods = ['POST'])
def logout():
    ph = request.form['ph']
    sql = "INSERT INTO activity VALUES(%s,%s,%s)"
    ts = get_ts()
    val = (ph, 'Logout', ts)
    con = connect_db()
    if con != None:
        cur = con.cursor(buffered=True)
        try:
            cur.execute(sql,val)
            con.commit()
            for i in range(0,len(users)):
                if users[i].phone == ph:
                    users.pop(i)
                    break
            cur.close()
            close_db(con)
        except mysql.connector.Error as err:
            con.rollback()
            cur.close()
            close_db(con)
            return jsonify(data = str(err), status = 503)
    else:
        return jsonify(status = 502)
    return jsonify(status = 200)

@app.route('/profile')
def profile():
    if not g.user:
        return redirect(url_for('login'))
    res = []
    if g.user.admin == 'Y':
        con = connect_db()
        if con != None:
            cur = con.cursor(buffered=True)
            sql = "SELECT phone,status FROM user"
            try:
                cur.execute(sql)
                con.commit()
            except mysql.connector.Error as err:
                con.rollback()
                cur.close()
                close_db(con)
                return ("<html><title>Server Error</title><body><h1>Server error in p "+str(err)+"</h1><a href='https://sreeni11.pythonanywhere.com/profile'>Retry</a></body></html>")
            res = cur.fetchall()
            if res and len(res) > 0:
                g.resp = res
            cur.close()
            close_db(con)
        else:
            return ("<html><title>Server Error</title><body><h1>SQL error in p </h1><a href='https://sreeni11.pythonanywhere.com/profile'>Retry</a></body></html>")
    #return ("<html><title>test</title><body><h1>"+str(res)+"</h1></body>")
    return render_template('profile.html', value=res)

@app.route('/dis', methods = ['POST'])
def dis():
    ph = request.form['ph']
    ph = str(ph[1:])
    con = connect_db()
    if con:
        cur = con.cursor(buffered=True)
        sql = "SELECT status FROM user WHERE phone=" + ph
        try:
            cur.execute(sql)
        except mysql.connector.Error as err:
            con.rollback()
            cur.close()
            close_db(con)
            return jsonify(data='error 1 ' + ph + str(err),status=503)
        res = cur.fetchall()
        if res and len(res) > 0:
            d = res[0][0]
            sql = "UPDATE user SET status="
            if d == 'D':
                sql += "'E' WHERE phone=" + ph
            else:
                sql += "'D' WHERE phone=" + ph
            try:
                cur.execute(sql)
                con.commit()
            except mysql.connector.Error as err:
                con.rollback()
                cur.close()
                close_db(con)
                return jsonify(data='error 2 ' + str(err), status=503)
        cur.close()
        close_db(con)
    else:
        return jsonify(data='error connecting to db', status=503)
    return jsonify(data='updated successfully',status=200)

@app.route('/promote', methods = ['POST'])
def promote():
    ph = request.form['ph']
    ph = str(ph[1:])
    con = connect_db()
    if con:
        cur = con.cursor(buffered=True)
        sql = "SELECT status FROM user WHERE phone=" + ph
        try:
            cur.execute(sql)

        except mysql.connector.Error as err:
            con.rollback()
            cur.close()
            close_db(con)
            return jsonify(data='error 1' + str(err),status=503)
        res = cur.fetchall()
        if res and len(res) > 0:
            d = res[0][0]
            sql = "UPDATE user SET status="
            if d == 'A':
                sql += "'E' WHERE phone=" + ph
            else:
                sql += "'A' WHERE phone=" + ph
            try:
                cur.execute(sql)
                con.commit()
            except mysql.connector.Error as err:
                con.rollback()
                cur.close()
                close_db(con)
                return jsonify(data='error 2' + str(err), status=503)
        cur.close()
        close_db(con)
    else:
        return jsonify(data='error connecting to db', status=503)
    return jsonify(data='updated successfully',status=200)

@app.route('/activity', methods = ['POST'])
def activity():
    ph = request.form['ph']
    ph = str(ph[1:])
    con = connect_db()
    if con:
        cur = con.cursor(buffered=True)
        sql = "SELECT * FROM activity WHERE patph=" + ph + " ORDER BY timestamp ASC"
        try:
            cur.execute(sql)
            con.commit()
        except mysql.connector.Error as err:
            con.rollback()
            cur.close()
            close_db(con)
            return jsonify(data='error 1' + str(err),status=503)
        res = cur.fetchall()
        cur.close()
        close_db(con)
    return jsonify(res if (res and len(res) > 0) else [])

@app.route('/viewquest', methods = ['POST'])
def viewquest():
    ph = request.form['ph']
    ph = str(ph)
    ts = request.form['ts']
    ts = str(ts[1:])
    dt = datetime.strptime(ts,'%a, %d %b %Y %H:%M:%S %Z')
    s = dt.strftime('%Y-%m-%d %H:%M:%S')
    con = connect_db()
    if con:
        cur = con.cursor(buffered=True)
        sql = "SELECT r.aname, r.timestamp, q.query, r.response FROM question q, responseTo r WHERE r.patph=" + ph + " AND r.timestamp='" + s + "' AND r.qid1 = q.qid ORDER BY r.qid1 ASC"
        try:
            cur.execute(sql)
            con.commit()
        except mysql.connector.Error as err:
            con.rollback()
            cur.close()
            close_db(con)
            return jsonify(data='error 3' + str(err)+sql,status=503)
        res = cur.fetchall()
        #return jsonify(sql)
        cur.close()
        close_db(con)
    return jsonify(res if (res and len(res) > 0) else [sql])

@app.route('/view', methods = ['POST'])
def view():
    ph = request.form['ph']
    ph = str(ph)
    ts = request.form['ts']
    ts = str(ts[1:])
    dt = datetime.strptime(ts,'%a, %d %b %Y %H:%M:%S %Z')
    s = dt.strftime('%Y-%m-%d %H:%M:%S')
    con = connect_db()
    if con:
        cur = con.cursor(buffered=True)
        sql = "SELECT * FROM headache WHERE patph=" + ph + " AND timestamp='" + s + "' ORDER BY timestamp ASC"
        try:
            cur.execute(sql)

        except mysql.connector.Error as err:
            con.rollback()
            cur.close()
            close_db(con)
            return jsonify(data='error 3' + str(err)+sql,status=503)
        res = cur.fetchall()
        #return jsonify(sql)
        sql = "SELECT * FROM medication WHERE patph=" + ph + " AND timestamp='" + s + "' ORDER BY timestamp ASC"
        try:
            cur.execute(sql)
            con.commit()
        except mysql.connector.Error as err:
            con.rollback()
            cur.close()
            close_db(con)
            return jsonify(data='error 3' + str(err)+sql,status=503)
        res2 = cur.fetchall()
        if res and len(res) > 0:
            res.append(res2)
        elif res == None or len(res) == 0:
            res = res2
        cur.close()
        close_db(con)
    return jsonify(res if (res and len(res) > 0) else [])
    #return jsonify(sql)

@app.route('/graph', methods = ['POST'])
def graph():
    ph = request.form['ph']
    con = connect_db()
    if con:
        #sql = "SELECT COUNT(*) AS Number, CONCAT(YEAR(timestamp),'-',MONTH(timestamp)) AS thedate FROM headache WHERE patph=%s GROUP BY CONCAT(YEAR(timestamp),'-',MONTH(timestamp)) ORDER BY thedate ASC"
        #val = (ph)
        sql = "SELECT COUNT(*) AS Number, CONCAT(YEAR(timestamp),'-',MONTH(timestamp)) AS thedate FROM headache WHERE patph=" + ph + " GROUP BY CONCAT(YEAR(timestamp),'-',MONTH(timestamp)) ORDER BY thedate ASC"
        cur = con.cursor(buffered=True)
        try:
            cur.execute(sql)
            con.commit()
        except mysql.connector.Error as err:
            con.rollback()
            cur.close()
            close_db(con)
            return jsonify(data=ph,err=str(err),status=503)
        res = cur.fetchall()
        num = []
        dt = []
        if res and len(res) > 0:
            for i in res:
                num.append(i[0])
                dt.append(i[1])
            fig = Figure()
            axis = fig.add_subplot(1, 1, 1)
            axis.set_title("Number of headaches per month")
            axis.set_xlabel("Date")
            axis.set_ylabel("Number of headaches")
            axis.grid()
            axis.plot(dt, num, "ro-")

            # Convert plot to PNG image
            pngImage = io.BytesIO()
            FigureCanvas(fig).print_png(pngImage)

            # Encode PNG image to base64 string
            pngImageB64String = "data:image/png;base64,"
            pngImageB64String += base64.b64encode(pngImage.getvalue()).decode('utf8')
            val = pngImageB64String
        else:
            val = '0'
        cur.close()
        close_db(con)
    else:
        return jsonify(data='Error connecting to db', status=503)
    return jsonify(img=val, status=200)

@app.route('/update', methods = ['POST'])
def update():
    #TO DO
    tm = get_ts()
    con = connect_db()
    if con:
        cur = con.cursor(buffered=True)

        if request.form['hname'] and request.form['mname']:
            ph = request.form['ph']
            hname = request.form['hname']
            ts = request.form['ts']
            dt = datetime.strptime(ts,'%a, %d %b %Y %H:%M:%S %Z')
            ts = dt.strftime('%Y-%m-%d %H:%M:%S')
            wakeup = request.form['wakeup']
            severity = request.form['severity']
            duration = request.form['duration']
            count = request.form['count']
            tmed = request.form['tmed']
            mcycle = request.form['mcycle']
            phy = request.form['phy']
            usc = request.form['usc']
            mname = request.form['mname']
            pills = request.form['pills']
            mhelp = request.form['mhelp']
            aname = 'Record headache and medication'

            try:
                cur.execute("DELETE FROM responseTo WHERE patph=%s AND timestamp=%s",(ph,ts))

                cur.execute("DELETE FROM headache WHERE patph=%s AND timestamp=%s",(ph,ts))

                cur.execute("DELETE FROM medication WHERE patph=%s AND timestamp=%s",(ph,ts))

                cur.execute("DELETE FROM activity WHERE patph=%s AND timestamp=%s",(ph,ts))

            except mysql.connector.Error as err:
                con.rollback()
                cur.close()
                close_db(con)
                return jsonify(data='Error storing info' + str(err),status=503)
            sql1 = "INSERT INTO headache(patph,hname,timestamp,wokeup,severity,duration,count,takemed,mcycle,physician,usc) VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)"
            val1 = (ph,hname,tm,wakeup,severity,duration,count,tmed,mcycle,phy,usc)
            sql2 = "INSERT INTO medication(patph,mname,timestamp,pills,help) VALUES(%s,%s,%s,%s,%s)"
            val2 = (ph,mname,tm,pills,mhelp)
            sql3 = "INSERT INTO activity VALUES(%s,%s,%s)"
            val3 = (ph,aname,tm)

            try:
                cur.execute(sql1,val1)

                cur.execute(sql2,val2)

                cur.execute(sql3,val3)

            except mysql.connector.Error as err:
                con.rollback()
                cur.close()
                close_db(con)
                return jsonify(data='Error storing info' + str(err),status=503)

            sql1 = 'INSERT INTO responseTo(qid1,qid2,patph,aname,timestamp,response) VALUES(%s,%s,%s,%s,%s,%s)'
            val1 = ('5','6',ph,aname,tm,hname)
            try:
                cur.execute(sql1,val1)

            except mysql.connector.Error as err:
                con.rollback()
                cur.close()
                close_db(con)
                return jsonify(data='Error storing info' + str(err),status=503)
            val1 = ('6','7',ph,aname,tm,'Yes' if wakeup == 'Y' else 'No')
            try:
                cur.execute(sql1,val1)

            except mysql.connector.Error as err:
                con.rollback()
                cur.close()
                close_db(con)
                return jsonify(data='Error storing info' + str(err),status=503)
            val1 = ('7','8',ph,aname,tm,duration)
            try:
                cur.execute(sql1,val1)

            except mysql.connector.Error as err:
                con.rollback()
                cur.close()
                close_db(con)
                return jsonify(data='Error storing info' + str(err),status=503)
            val1 = ('8','9',ph,aname,tm,severity)
            try:
                cur.execute(sql1,val1)

            except mysql.connector.Error as err:
                con.rollback()
                cur.close()
                close_db(con)
                return jsonify(data='Error storing info' + str(err),status=503)
            val1 = ('9','10',ph,aname,tm,count)
            try:
                cur.execute(sql1,val1)

            except mysql.connector.Error as err:
                con.rollback()
                cur.close()
                close_db(con)
                return jsonify(data='Error storing info' + str(err),status=503)
            val1 = ('10','11',ph,aname,tm,'Yes')
            try:
                cur.execute(sql1,val1)

            except mysql.connector.Error as err:
                con.rollback()
                cur.close()
                close_db(con)
                return jsonify(data='Error storing info' + str(err),status=503)
            val1 = ('11','12',ph,aname,tm,mname)
            try:
                cur.execute(sql1,val1)

            except mysql.connector.Error as err:
                con.rollback()
                cur.close()
                close_db(con)
                return jsonify(data='Error storing info' + str(err),status=503)
            val1 = ('12','13',ph,aname,tm,pills)
            try:
                cur.execute(sql1,val1)

            except mysql.connector.Error as err:
                con.rollback()
                cur.close()
                close_db(con)
                return jsonify(data='Error storing info' + str(err),status=503)
            val1 = ('13','15',ph,aname,tm,'Yes' if mhelp == 'Y' else 'No')
            try:
                cur.execute(sql1,val1)

            except mysql.connector.Error as err:
                con.rollback()
                cur.close()
                close_db(con)
                return jsonify(data='Error storing info' + str(err),status=503)
            val1 = ('15','16' if mcycle != 'NULL' else '17',ph,aname,tm,'No')
            try:
                cur.execute(sql1,val1)

            except mysql.connector.Error as err:
                con.rollback()
                cur.close()
                close_db(con)
                return jsonify(data='Error storing info' + str(err),status=503)
            if mcycle != 'NULL':
                val1 = ('16','17',ph,aname,tm,mcycle)
                try:
                    cur.execute(sql1,val1)

                except mysql.connector.Error as err:
                    con.rollback()
                    cur.close()
                    close_db(con)
                    return jsonify(data='Error storing info' + str(err),status=503)
            if phy != 'NULL':
                val1 = ('15' if mcycle == 'NULL' else '16','17',ph,aname,tm,phy)
                try:
                    cur.execute(sql1,val1)

                except mysql.connector.Error as err:
                    con.rollback()
                    cur.close()
                    close_db(con)
                    return jsonify(data='Error storing info' + str(err),status=503)
            if usc != 'NULL':
                val1 = ('17','18',ph,aname,tm,usc)
                try:
                    cur.execute(sql1,val1)

                except mysql.connector.Error as err:
                    con.rollback()
                    cur.close()
                    close_db(con)
                    return jsonify(data='Error storing info' + str(err),status=503)
        elif request.form['hname']:
            ph = request.form['ph']
            hname = request.form['hname']
            ts = request.form['ts']
            dt = datetime.strptime(ts,'%a, %d %b %Y %H:%M:%S %Z')
            ts = dt.strftime('%Y-%m-%d %H:%M:%S')
            wakeup = request.form['wakeup']
            severity = request.form['severity']
            duration = request.form['duration']
            count = request.form['count']
            tmed = request.form['tmed']
            mcycle = request.form['mcycle']
            phy = request.form['phy']
            usc = request.form['usc']
            aname = 'Record headache'

            try:
                cur.execute("DELETE FROM responseTo WHERE patph=%s AND timestamp=%s",(ph,ts))

                cur.execute("DELETE FROM headache WHERE patph=%s AND timestamp=%s",(ph,ts))

                cur.execute("DELETE FROM medication WHERE patph=%s AND timestamp=%s",(ph,ts))

                cur.execute("DELETE FROM activity WHERE patph=%s AND timestamp=%s",(ph,ts))

            except mysql.connector.Error as err:
                con.rollback()
                cur.close()
                close_db(con)
                return jsonify(data='Error storing info' + str(err),status=503)

            sql1 = "INSERT INTO headache(patph,hname,timestamp,wokeup,severity,duration,count,takemed,mcycle,physician,usc) VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)"
            val1 = (ph,hname,tm,wakeup,severity,duration,count,tmed,mcycle,phy,usc)
            sql3 = "INSERT INTO activity VALUES(%s,%s,%s)"
            val3 = (ph,aname,tm)
            try:
                cur.execute(sql1,val1)

                cur.execute(sql3,val3)

            except mysql.connector.Error as err:
                con.rollback()
                cur.close()
                close_db(con)
                return jsonify(data='Error storing data' + str(err),status=503)
            sql1 = 'INSERT INTO responseTo(qid1,qid2,patph,aname,timestamp,response) VALUES(%s,%s,%s,%s,%s,%s)'
            val1 = ('5','6',ph,aname,tm,hname)
            try:
                cur.execute(sql1,val1)

            except mysql.connector.Error as err:
                con.rollback()
                cur.close()
                close_db(con)
                return jsonify(data='Error storing info' + str(err),status=503)
            val1 = ('6','7',ph,aname,tm,'Yes' if wakeup == 'Y' else 'No')
            try:
                cur.execute(sql1,val1)

            except mysql.connector.Error as err:
                con.rollback()
                cur.close()
                close_db(con)
                return jsonify(data='Error storing info' + str(err),status=503)
            val1 = ('7','8',ph,aname,tm,duration)
            try:
                cur.execute(sql1,val1)

            except mysql.connector.Error as err:
                con.rollback()
                cur.close()
                close_db(con)
                return jsonify(data='Error storing info' + str(err),status=503)
            val1 = ('8','9',ph,aname,tm,severity)
            try:
                cur.execute(sql1,val1)

            except mysql.connector.Error as err:
                con.rollback()
                cur.close()
                close_db(con)
                return jsonify(data='Error storing info' + str(err),status=503)
            val1 = ('9','10',ph,aname,tm,count)
            try:
                cur.execute(sql1,val1)

            except mysql.connector.Error as err:
                con.rollback()
                cur.close()
                close_db(con)
                return jsonify(data='Error storing info' + str(err),status=503)
            val1 = ('10','15',ph,aname,tm,'No')
            try:
                cur.execute(sql1,val1)

            except mysql.connector.Error as err:
                con.rollback()
                cur.close()
                close_db(con)
                return jsonify(data='Error storing info' + str(err),status=503)
            val1 = ('15','16' if mcycle != 'NULL' else '17',ph,aname,tm,'No')
            try:
                cur.execute(sql1,val1)

            except mysql.connector.Error as err:
                con.rollback()
                cur.close()
                close_db(con)
                return jsonify(data='Error storing info' + str(err),status=503)
            if mcycle != 'NULL':
                val1 = ('16','17',ph,aname,tm,mcycle)
                try:
                    cur.execute(sql1,val1)

                except mysql.connector.Error as err:
                    con.rollback()
                    cur.close()
                    close_db(con)
                    return jsonify(data='Error storing info' + str(err),status=503)
            if phy != 'NULL':
                val1 = ('15' if mcycle == 'NULL' else '16','17',ph,aname,tm,phy)
                try:
                    cur.execute(sql1,val1)

                except mysql.connector.Error as err:
                    con.rollback()
                    cur.close()
                    close_db(con)
                    return jsonify(data='Error storing info' + str(err),status=503)
            if usc != 'NULL':
                val1 = ('17','18',ph,aname,tm,usc)
                try:
                    cur.execute(sql1,val1)

                except mysql.connector.Error as err:
                    con.rollback()
                    cur.close()
                    close_db(con)
                    return jsonify(data='Error storing info' + str(err),status=503)
        elif request.form['mname']:
            ph = request.form['ph']
            mname = request.form['mname']
            ts = request.form['ts']
            dt = datetime.strptime(ts,'%a, %d %b %Y %H:%M:%S %Z')
            ts = dt.strftime('%Y-%m-%d %H:%M:%S')
            pills = request.form['pills']
            mhelp = request.form['mhelp']
            aname = 'Record medication'

            try:
                cur.execute("DELETE FROM responseTo WHERE patph=%s AND timestamp=%s",(ph,ts))
                cur.execute("DELETE FROM headache WHERE patph=%s AND timestamp=%s",(ph,ts))
                cur.execute("DELETE FROM medication WHERE patph=%s AND timestamp=%s",(ph,ts))
                cur.execute("DELETE FROM activity WHERE patph=%s AND timestamp=%s",(ph,ts))
            except mysql.connector.Error as err:
                con.rollback()
                cur.close()
                close_db(con)
                return jsonify(data='Error storing info' + str(err),status=503)

            sql2 = "INSERT INTO medication(patph,mname,timestamp,pills,help) VALUES(%s,%s,%s,%s,%s)"
            val2 = (ph,mname,tm,pills,mhelp)
            sql3 = "INSERT INTO activity VALUES(%s,%s,%s)"
            val3 = (ph,aname,tm)
            try:
                cur.execute(sql2,val2)
                cur.execute(sql3,val3)
            except mysql.connector.Error as err:
                con.rollback()
                cur.close()
                close_db(con)
                return jsonify(data='Error storing info' + str(err),status=503)


            sql1 = 'INSERT INTO responseTo(qid1,qid2,patph,aname,timestamp,response) VALUES(%s,%s,%s,%s,%s,%s)'
            val1 = ('1','2',ph,aname,tm,'No')
            try:
                cur.execute(sql1,val1)

            except mysql.connector.Error as err:
                con.rollback()
                cur.close()
                close_db(con)
                return jsonify(data='Error storing info' + str(err),status=503)
            val1 = ('2','3',ph,aname,tm,'No')
            try:
                cur.execute(sql1,val1)

            except mysql.connector.Error as err:
                con.rollback()
                cur.close()
                close_db(con)
                return jsonify(data='Error storing info' + str(err),status=503)
            val1 = ('3','11',ph,aname,tm,'Yes')
            try:
                cur.execute(sql1,val1)

            except mysql.connector.Error as err:
                con.rollback()
                cur.close()
                close_db(con)
                return jsonify(data='Error storing info' + str(err),status=503)

            val1 = ('11','12',ph,aname,tm,mname)
            try:
                cur.execute(sql1,val1)

            except mysql.connector.Error as err:
                con.rollback()
                cur.close()
                close_db(con)
                return jsonify(data='Error storing info' + str(err),status=503)
            val1 = ('12','13',ph,aname,tm,pills)
            try:
                cur.execute(sql1,val1)

            except mysql.connector.Error as err:
                con.rollback()
                cur.close()
                close_db(con)
                return jsonify(data='Error storing info' + str(err),status=503)
            val1 = ('13','15',ph,aname,tm,'Yes' if mhelp == 'Y' else 'No')
            try:
                cur.execute(sql1,val1)

            except mysql.connector.Error as err:
                con.rollback()
                cur.close()
                close_db(con)
                return jsonify(data='Error storing info' + str(err),status=503)

        else:
            return jsonify(data='Error in update',status=503)
        try:
            con.commit()
            cur.close()
            close_db(con)
        except mysql.connector.Error as err:
            con.rollback()
            cur.close()
            close_db(con)
            return jsonify(data='Error storing info' + str(err), status=503)
    else:
        return jsonify(data='Error connecting to db',status=502)
    return jsonify(data='Successfully updated entry', status=200)

@app.route('/record', methods=['POST'])
def record():
    from flask import request, make_response, jsonify
    req = request.get_json(force=True)
    context = req.get('queryResult').get('outputContexts')
    msg = 'Thank you for recording your headache. You may always review and edit your current or previous.'
    j = 0
    for i in range(0,len(context)):
        if 'name-intent' in ((context[i]).get('name')):
            j = i
            break
    parameters = (context[j]).get('parameters')
    #store_data(parameters)
    hname = parameters.get('hname')
    old = parameters.get('old')
    wakeup = parameters.get('wakeup')
    duration = parameters.get('duration')
    severity = parameters.get('severity')
    count = parameters.get('count')
    mcycle = parameters.get('mcycle')
    phy = parameters.get('phy')
    usc = parameters.get('usc')
    mname = parameters.get('mname')
    pills = parameters.get('pills')
    mhelp = parameters.get('mhelp')
    ts = get_ts()
    patph = (req.get('session'))[-10:]
    con = connect_db()
    val = ()
    if con != None:
        cur = con.cursor(buffered=True)
        aname = 'Record medication'
        msg = 'Thank you for recording your responses. You may always review and edit your current or previous answers'
        if hname == None and mname == None:
            aname = 'Talk to chatbot'
            msg = 'Have a wonderful day!'
            sql1 = 'INSERT INTO activity VALUES(%s,%s,%s)'
            val1 = (patph,aname,ts)

            sql2 = 'INSERT INTO responseTo(qid1,qid2,patph,aname,timestamp,response) VALUES(%s,%s,%s,%s,%s,%s)'
            try:
                cur.execute(sql1,val1)

            except mysql.connector.Error as err:
                con.rollback()
                close_db(con)
                cur.close()
                msg = 'An error occured while storing data please try again.' + str(val1) +' Error - ' + str(err)
                return make_response(jsonify({'fulfillmentText': msg}))

            val2 = ('1','2',patph,aname,ts,'No')
            try:
                cur.execute(sql2,val2)

            except mysql.connector.Error as err:
                con.rollback()
                cur.close()
                close_db(con)
                msg = 'An error occured while storing data please try again.' + str(val2) +' Error - ' + str(err)
                return make_response(jsonify({'fulfillmentText': msg}))

            val2 = ('2','3',patph,aname,ts,'No')
            try:
                cur.execute(sql2,val2)

            except mysql.connector.Error as err:
                con.rollback()
                cur.close()
                close_db(con)
                msg = 'An error occured while storing data please try again.' + str(val2) +' Error - ' + str(err)
                return make_response(jsonify({'fulfillmentText': msg}))

            val2 = ('3', '4',patph,aname,ts,'No')
            try:
                cur.execute(sql2,val2)

            except mysql.connector.Error as err:
                con.rollback()
                cur.close()
                close_db(con)
                msg = 'An error occured while storing data please try again' + str(val2) +'. Error - ' + str(err)
                return make_response(jsonify({'fulfillmentText': msg}))
        elif hname == None and mname != None:
            sql1 = 'INSERT INTO activity VALUES(%s,%s,%s)'
            val1 = (patph,aname,ts)

            sql2 = 'INSERT INTO responseTo(qid1,qid2,patph,aname,timestamp,response) VALUES(%s,%s,%s,%s,%s,%s)'
            try:
                cur.execute(sql1,val1)

            except mysql.connector.Error as err:
                con.rollback()
                cur.close()
                close_db(con)
                msg = 'An error occured while storing data please try again.' + str(val1) +' Error - ' + str(err)
                return make_response(jsonify({'fulfillmentText': msg}))

            val2 = ('1','2',patph,aname,ts,'No')
            try:
                cur.execute(sql2,val2)

            except mysql.connector.Error as err:
                con.rollback()
                cur.close()
                close_db(con)
                msg = 'An error occured while storing data please try again' + str(val2) +'. Error - ' + str(err)
                return make_response(jsonify({'fulfillmentText': msg}))

            val2 = ('2','3',patph,aname,ts,'No')
            try:
                cur.execute(sql2,val2)

            except mysql.connector.Error as err:
                con.rollback()
                cur.close()
                close_db(con)
                msg = 'An error occured while storing data please try again' + str(val2) +'. Error - ' + str(err)
                return make_response(jsonify({'fulfillmentText': msg}))

            val2 = ('3', '4',patph,aname,ts,'Yes')
            try:
                cur.execute(sql2,val2)

            except mysql.connector.Error as err:
                con.rollback()
                cur.close()
                close_db(con)
                msg = 'An error occured while storing data please try again.' + str(val2) +' Error - ' + str(err)
                return make_response(jsonify({'fulfillmentText': msg}))
        elif hname != None and mname == None:
            sql1 = 'INSERT INTO activity VALUES(%s,%s,%s)'
            aname = 'Record headache'
            val1 = (patph,aname,ts)

            sql2 = 'INSERT INTO responseTo(qid1,qid2,patph,aname,timestamp,response) VALUES(%s,%s,%s,%s,%s,%s)'
            try:
                cur.execute(sql1,val1)

            except mysql.connector.Error as err:
                con.rollback()
                cur.close()
                close_db(con)
                msg = 'An error occured while storing data please try again' + str(val1) +'. Error - ' + str(err)
                return make_response(jsonify({'fulfillmentText': msg}))

            if old != None:
                val2 = ('1','2',patph,aname,ts,'No')
                try:
                    cur.execute(sql2,val2)

                except mysql.connector.Error as err:
                    con.rollback()
                    cur.close()
                    close_db(con)
                    msg = 'An error occured while storing data please try again' + str(val2) +'. Error - ' + str(err)
                    return make_response(jsonify({'fulfillmentText': msg}))

                val2 = ('2','5',patph,aname,ts,'Yes')
                try:
                    cur.execute(sql2,val2)

                except mysql.connector.Error as err:
                    con.rollback()
                    cur.close()
                    close_db(con)
                    msg = 'An error occured while storing data please try again' + str(val2) +'. Error - ' + str(err)
                    return make_response(jsonify({'fulfillmentText': msg}))
            else:
                val2 = ('1','5',patph,aname,ts,'Yes')
                try:
                    cur.execute(sql2,val2)

                except mysql.connector.Error as err:
                    con.rollback()
                    cur.close()
                    close_db(con)
                    msg = 'An error occured while storing data please try again' + str(val2) +'. Error - ' + str(err)
                    return make_response(jsonify({'fulfillmentText': msg}))
        else:
            sql1 = 'INSERT INTO activity VALUES(%s,%s,%s)'
            aname = 'Record headache and medication'
            val1 = (patph,aname,ts)

            sql2 = 'INSERT INTO responseTo(qid1,qid2,patph,aname,timestamp,response) VALUES(%s,%s,%s,%s,%s,%s)'
            try:
                cur.execute(sql1,val1)

            except mysql.connector.Error as err:
                con.rollback()
                cur.close()
                close_db(con)
                msg = 'An error occured while storing data please try again' + str(val2) +'. Error - ' + str(err)
                return make_response(jsonify({'fulfillmentText': msg}))

            if old != None:
                val2 = ('1','2',patph,aname,ts,'No')
                try:
                    cur.execute(sql2,val2)

                except mysql.connector.Error as err:
                    con.rollback()
                    cur.close()
                    close_db(con)
                    msg = 'An error occured while storing data please try again' + str(val2) +'. Error - ' + str(err)
                    return make_response(jsonify({'fulfillmentText': msg}))

                val2 = ('2','5',patph,aname,ts,'Yes')
                try:
                    cur.execute(sql2,val2)

                except mysql.connector.Error as err:
                    con.rollback()
                    cur.close()
                    close_db(con)
                    msg = 'An error occured while storing data please try again' + str(val2) +'. Error - ' + str(err)
                    return make_response(jsonify({'fulfillmentText': msg}))
            else:
                val2 = ('1','5',patph,aname,ts,'Yes')
                try:
                    cur.execute(sql2,val2)

                except mysql.connector.Error as err:
                    con.rollback()
                    cur.close()
                    close_db(con)
                    msg = 'An error occured while storing data please try again' + str(val2) +'. Error - ' + str(err)
                    return make_response(jsonify({'fulfillmentText': msg}))

        if hname != None:
            sql1 = 'INSERT INTO headache(patph,hname,timestamp,wokeup,severity,duration,count,takemed,mcycle,physician,usc) VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)'
            sql2 = 'INSERT INTO responseTo(qid1,qid2,patph,aname,timestamp,response) VALUES(%s,%s,%s,%s,%s,%s)'
            tmp = [patph]
            tmp.append(hname)
            tmp2 = ['5','6',patph]
            #aname = 'Record headache'
            #if mname != None:
                #aname = 'Record headache and medication'
            tmp2.append(aname)
            tmp2.append(ts)
            tmp2.append(hname)
            val2 = tuple(tmp2)
            try:
                cur.execute(sql2,val2)

            except mysql.connector.Error as err:
                con.rollback()
                cur.close()
                close_db(con)
                msg = 'An error occured while storing data please try again' + str(val2) +'. Error - ' + str(err)
                return make_response(jsonify({'fulfillmentText': msg}))
            #tmp.append(str(test))
            tmp.append(ts)

            tmp2 = ['6','7',patph,aname,ts]
            if wakeup != None:
                tmp.append(wakeup[0])
                tmp2.append(wakeup)
            else:
                tmp.append('NULL')
                tmp2.append('NULL')
            val2 = tuple(tmp2)
            try:
                cur.execute(sql2,val2)

            except mysql.connector.Error as err:
                con.rollback()
                cur.close()
                close_db(con)
                msg = 'An error occured while storing data please try again' + str(val2) +'. Error - ' + str(err)
                return make_response(jsonify({'fulfillmentText': msg}))

            tmp2 = ['8','9',patph,aname,ts]
            if severity != None:
                tmp.append(severity)
                tmp2.append(severity)
            else:
                tmp.append('NULL')
                tmp2.append('NULL')
            val2 = tuple(tmp2)
            try:
                cur.execute(sql2,val2)

            except mysql.connector.Error as err:
                con.rollback()
                cur.close()
                close_db(con)
                msg = 'An error occured while storing data please try again' + str(val2) +'. Error - ' + str(err)
                return make_response(jsonify({'fulfillmentText': msg}))

            tmp2 = ['7','8',patph,aname,ts]
            if duration != None:
                tmp.append(duration)
                tmp2.append(duration)
            else:
                tmp.append('NULL')
                tmp2.append('NULL')
            val2 = tuple(tmp2)
            try:
                cur.execute(sql2,val2)

            except mysql.connector.Error as err:
                con.rollback()
                cur.close()
                close_db(con)
                msg = 'An error occured while storing data please try again' + str(val2) +'. Error - ' + str(err)
                return make_response(jsonify({'fulfillmentText': msg}))

            tmp2 = ['9','10',patph,aname,ts]
            if count != None:
                tmp.append(count)
                tmp2.append(count)
            else:
                tmp.append('NULL')
                tmp2.append('NULL')
            val2 = tuple(tmp2)
            try:
                cur.execute(sql2,val2)

            except mysql.connector.Error as err:
                con.rollback()
                cur.close()
                close_db(con)
                msg = 'An error occured while storing data please try again' + str(val2) +'. Error - ' + str(err)
                return make_response(jsonify({'fulfillmentText': msg}))

            tmp2 = ['10','11',patph,aname,ts]
            if mname != None:
                tmp.append('Y')
                tmp2.append('Yes')
            else:
                tmp.append('N')
                tmp2.append('No')
                tmp2[1] = '15'
            val2 = tuple(tmp2)
            try:
                cur.execute(sql2,val2)

            except mysql.connector.Error as err:
                con.rollback()
                cur.close()
                close_db(con)
                msg = 'An error occured while storing data please try again' + str(val2) +'. Error - ' + str(err)
                return make_response(jsonify({'fulfillmentText': msg}))

            if mcycle != None and getuser(patph).gender == 'F':
                tmp.append(mcycle[0] if mcycle != 'NULL' else mcycle)
                tmp2 = ['16','17',patph,aname,ts,mcycle]
                val2 = tuple(tmp2)
                try:
                    cur.execute(sql2,val2)

                except mysql.connector.Error as err:
                    con.rollback()
                    cur.close()
                    close_db(con)
                    msg = 'An error occured while storing data please try again' + str(val2) +'. Error - ' + str(err)
                    return make_response(jsonify({'fulfillmentText': msg}))
            else:
                tmp.append('NULL')
                tmp2 = 'N'

            if phy != None:
                tmp.append(phy[0])
                if tmp2 == 'N':
                    tmp2 = ['15','17',patph,aname,ts,'No']
                    val2 = tuple(tmp2)
                    try:
                        cur.execute(sql2,val2)

                    except mysql.connector.Error as err:
                        con.rollback()
                        cur.close()
                        close_db(con)
                        msg = 'An error occured while storing data please try again' + str(val2) +'. Error - ' + str(err)
                        return make_response(jsonify({'fulfillmentText': msg}))
                else:
                    tmp2 = ['15','16',patph,aname,ts,'No']
                    val2 = tuple(tmp2)
                    try:
                        cur.execute(sql2,val2)

                    except mysql.connector.Error as err:
                        con.rollback()
                        cur.close()
                        close_db(con)
                        msg = 'An error occured while storing data please try again' + str(val2) +'. Error - ' + str(err)
                        return make_response(jsonify({'fulfillmentText': msg}))
                tmp2 = ['17','18',patph,aname,ts,phy]
            else:
                tmp.append('NULL')
                tmp2 = ['15','5',patph,aname,ts,'Yes']
                val2 = tuple(tmp2)
                try:
                    cur.execute(sql2,val2)

                except mysql.connector.Error as err:
                    con.rollback()
                    cur.close()
                    close_db(con)
                    msg = 'An error occured while storing data please try again' + str(val2) +'. Error - ' + str(err)
                    return make_response(jsonify({'fulfillmentText': msg}))
            val2 = tuple(tmp2)
            try:
                cur.execute(sql2,val2)

            except mysql.connector.Error as err:
                con.rollback()
                cur.close()
                close_db(con)
                msg = 'An error occured while storing data please try again' + str(val2) +'. Error - ' + str(err)
                return make_response(jsonify({'fulfillmentText': msg}))

            if usc != None:
                tmp.append(usc[0])
                tmp2 = ['18','19',patph,aname,ts,usc]
                val2 = tuple(tmp2)
                try:
                    cur.execute(sql2,val2)

                except mysql.connector.Error as err:
                    con.rollback()
                    cur.close()
                    close_db(con)
                    msg = 'An error occured while storing data please try again' + str(val2) +'. Error - ' + str(err)
                    return make_response(jsonify({'fulfillmentText': msg}))
            else:
                tmp.append('N')

            val = tuple(tmp)
            try:
                cur.execute(sql1,val)

            except mysql.connector.Error as err:
                con.rollback()
                cur.close()
                close_db(con)
                msg = 'An error occured while storing data of headache please try again' + str(val) +'. Error - ' + str(err)
                return make_response(jsonify({'fulfillmentText': msg}))

        if mname != None:
            tmp = [patph,mname,ts]
            if 'headache' not in aname:
                val2 = ('3','11',patph,aname,ts,'Yes')
                try:
                    cur.execute(sql2,val2)

                except mysql.connector.Error as err:
                    con.rollback()
                    cur.close()
                    close_db(con)
                    msg = 'An error occured while storing data please try again' + str(val2) +'. Error - ' + str(err)
                    return make_response(jsonify({'fulfillmentText': msg}))

            val2 = ('11','12',patph,aname,ts,mname)
            try:
                cur.execute(sql2,val2)

            except mysql.connector.Error as err:
                con.rollback()
                cur.close()
                close_db(con)
                msg = 'An error occured while storing responseTo data please try again.' + str(val2) + ' Error - ' + str(err)
                return make_response(jsonify({'fulfillmentText': msg}))

            if pills != None:
                tmp.append(pills)
                tmp2 = ['12','13',patph,aname,ts,pills]
            else:
                tmp.append('NULL')
                tmp2 = ['12','13',patph,aname,ts,'NULL']
            val2 = tuple(tmp2)
            try:
                cur.execute(sql2,val2)

            except mysql.connector.Error as err:
                con.rollback()
                cur.close()
                close_db(con)
                msg = 'An error occured while storing data responseTo please try again' + str(val2) +'. Error - ' + str(err)
                return make_response(jsonify({'fulfillmentText': msg}))

            if mhelp != None:
                tmp.append(mhelp[0])
                tmp2 = ['13','15',patph,aname,ts,mhelp]
            else:
                tmp.append('NULL')
                tmp2 = ['13','15',patph,aname,ts,'NULL']
            val2 = tuple(tmp2)
            try:
                cur.execute(sql2,val2)

            except mysql.connector.Error as err:
                con.rollback()
                cur.close()
                close_db(con)
                msg = 'An error occured while storing data please try again. Error - ' + str(err)
                return make_response(jsonify({'fulfillmentText': msg}))
            val = tuple(tmp)
            sql = 'INSERT INTO medication(patph,mname,timestamp,pills,help) VALUES(%s,%s,%s,%s,%s)'
            try:
                cur.execute(sql,val)

            except mysql.connector.Error as err:
                con.rollback()
                cur.close()
                close_db(con)
                msg = 'An error occured while storing data of medication please try again. Error - ' + str(err)
                return make_response(jsonify({'fulfillmentText': msg}))
        try:
            con.commit()
        except mysql.connector.Error as err:
            con.rollback()
            cur.close()
            close_db(con)
            msg = 'An error occured while commiting data please try again. Error - ' + str(err)
            return make_response(jsonify({'fulfillmentText': msg}))
        cur.close()
        close_db(con)
    #con.close()
    return make_response(jsonify({'fulfillmentText': msg}))

@app.route("/", methods=['GET', 'POST'])
def server():
    from flask import request

    # get SMS metadata
    msg_from = request.values.get("From", None)
    msg = request.values.get("Body", None)

    ph = msg_from[2:]

    if getuser(ph):
        # prepare API.ai request
        req = ai.text_request()
        req.lang = 'en'  # optional, default value equal 'en'
        req.session_id = ph
        req.query = msg

        # get response from API.ai
        api_response = req.getresponse()
        responsestr = api_response.read().decode('utf-8')
        response_obj = json.loads(responsestr)
        reply="Hello"
        if 'result' in response_obj:
            response = response_obj["result"]["fulfillment"]["speech"]
            if 'cycle' in response and getuser(ph).gender != 'F':
                req1 = ai.text_request()
                req1.lang = 'en'
                req1.session_id = ph
                req1.query = 'NULL'
                api_response1 = req1.getresponse()
                responsestr1 = api_response1.read().decode('utf-8')
                response_obj1 = json.loads(responsestr1)
                if 'result' in response_obj1:
                    response1 = response_obj1["result"]["fulfillment"]["speech"]
                    reply = client.messages.create(to=msg_from, from_= account_num, body=response1)
            else:
                # send SMS response back via twilio
                reply=client.messages.create(to=msg_from, from_= account_num, body=response)
    else:
        con = connect_db()
        if con:
            cur = con.cursor(buffered=True)
            sql = "SELECT * FROM user WHERE phone=" + str(ph)
            try:
                cur.execute(sql)
                con.commit()
            except mysql.connector.Error as err:
                con.rollback()
                cur.close()
                close_db(con)
                return str(client.messages.create(to=msg_from,from_=account_num,body='An error occured' + str(err)))
            res = cur.fetchall()
            cur.close()
            close_db(con)
            if res and len(res) > 0:
                return str(client.messages.create(to=msg_from,from_=account_num,body='Please login - https://sreeni11.pythonanywhere.com/login'))
            else:
                return str(client.messages.create(to=msg_from,from_=account_num,body='Signup at - https://sreeni11.pythonanywhere.com/signup'))
    return str(reply)

if __name__ == "__main__":
    app.run(debug=True)