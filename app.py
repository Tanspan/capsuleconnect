from flask import Flask, render_template, request, redirect, url_for, session, jsonify, flash
import mysql.connector, hashlib, os
from datetime import datetime
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = 'cc2024'

# ── CHANGE THESE ──
DB = {'host':'localhost','user':'root','password':'root0_0','database':'capsuleconnect'}
UPLOADS = os.path.join('static','uploads')
os.makedirs(UPLOADS, exist_ok=True)

def db(): return mysql.connector.connect(**DB)
def hp(p): return hashlib.sha256(p.encode()).hexdigest()
def auth(f):
    from functools import wraps
    @wraps(f)
    def w(*a,**k):
        if 'uid' not in session: return redirect(url_for('login'))
        return f(*a,**k)
    return w

def friends(uid):
    g = db(); c = g.cursor(dictionary=True)
    c.execute("SELECT u.id,u.username FROM users u JOIN connections cn ON (cn.sender_id=%s AND cn.receiver_id=u.id) OR (cn.receiver_id=%s AND cn.sender_id=u.id) WHERE cn.status='accepted'",(uid,uid))
    r = c.fetchall(); c.close(); g.close(); return r

# ── AUTH ──
@app.route('/')
def index(): return redirect(url_for('feed')) if 'uid' in session else render_template('landing.html')

@app.route('/register', methods=['GET','POST'])
def register():
    if request.method=='POST':
        g = db(); c = g.cursor()
        try:
            c.execute("INSERT INTO users(username,email,password) VALUES(%s,%s,%s)",(request.form['username'],request.form['email'],hp(request.form['password'])))
            g.commit(); flash('Account created! Login now.','success')
            return redirect(url_for('login'))
        except: flash('Username or email exists.','danger')
        finally: c.close(); g.close()
    return render_template('register.html')

@app.route('/login', methods=['GET','POST'])
def login():
    if request.method=='POST':
        g = db(); c = g.cursor(dictionary=True)
        c.execute("SELECT * FROM users WHERE email=%s AND password=%s",(request.form['email'],hp(request.form['password'])))
        u = c.fetchone(); c.close(); g.close()
        if u: session['uid']=u['id']; session['uname']=u['username']; return redirect(url_for('feed'))
        flash('Invalid credentials.','danger')
    return render_template('login.html')

@app.route('/logout')
def logout(): session.clear(); return redirect(url_for('index'))

# ── PAGES ──
@app.route('/feed')
@auth
def feed():
    g = db(); c = g.cursor(dictionary=True); now = datetime.now()
    c.execute("SELECT CASE WHEN sender_id=%s THEN receiver_id ELSE sender_id END AS fid FROM connections WHERE (sender_id=%s OR receiver_id=%s) AND status='accepted'",(session['uid'],)*3)
    fids = [r['fid'] for r in c.fetchall()]
    posts = []
    if fids:
        fmt = ','.join(['%s']*len(fids))
        c.execute(f"SELECT cp.*,u.username FROM capsules cp JOIN users u ON cp.user_id=u.id WHERE cp.user_id IN ({fmt}) AND cp.is_public=1 AND cp.unlock_date<=%s ORDER BY cp.unlock_date DESC LIMIT 20",(*fids,now))
        posts = c.fetchall()
    c.execute("SELECT cp.* FROM stories s JOIN capsules cp ON s.capsule_id=cp.id WHERE s.user_id=%s AND cp.unlock_date<=%s",(session['uid'],now))
    stories = c.fetchall()
    c.execute("SELECT cn.*,u.username FROM connections cn JOIN users u ON cn.sender_id=u.id WHERE cn.receiver_id=%s AND cn.status='pending'",(session['uid'],))
    reqs = c.fetchall(); c.close(); g.close()
    return render_template('feed.html', posts=posts, stories=stories, reqs=reqs, fids=fids, now=now)

@app.route('/dashboard')
@auth
def dashboard():
    g = db(); c = g.cursor(dictionary=True); now = datetime.now()
    c.execute("SELECT * FROM capsules WHERE user_id=%s ORDER BY created_at DESC",(session['uid'],))
    caps = c.fetchall()
    c.execute("SELECT cp.*,u.username as sname FROM capsules cp JOIN users u ON cp.user_id=u.id WHERE cp.recipient_id=%s ORDER BY cp.created_at DESC",(session['uid'],))
    recv = c.fetchall(); c.close(); g.close()
    return render_template('dashboard.html', caps=caps, recv=recv, now=now)

@app.route('/capsule/create', methods=['GET','POST'])
@app.route('/submit', methods=['POST'])
@auth
def create():
    if request.method=='POST':
        g = db(); c = g.cursor(dictionary=True); rid = None
        ru = request.form.get('recipient_username','').strip()
        if ru:
            c.execute("SELECT id FROM users WHERE username=%s",(ru,))
            r = c.fetchone()
            if not r: flash('User not found.','danger'); return redirect(url_for('create'))
            rid = r['id']
        c.execute("INSERT INTO capsules(user_id,title,message,type,unlock_date,is_public,recipient_id) VALUES(%s,%s,%s,%s,%s,%s,%s)",
            (session['uid'],request.form['title'],request.form['message'],request.form['type'],
             request.form['unlock_date'].replace('T',' '),1 if request.form.get('is_public') else 0,rid))
        g.commit(); cid = c.lastrowid
        c.execute("INSERT INTO stories(user_id,capsule_id) VALUES(%s,%s)",(session['uid'],cid))
        g.commit(); c.close(); g.close()
        flash('Capsule locked!','success')
        return redirect(url_for('success'))
    return render_template('create.html')

@app.route('/success')
@auth
def success(): return render_template('success.html')

@app.route('/capsule/<int:cid>')
@auth
def view(cid):
    g = db(); c = g.cursor(dictionary=True)
    c.execute("SELECT cp.*,u.username FROM capsules cp JOIN users u ON cp.user_id=u.id WHERE cp.id=%s",(cid,))
    cap = c.fetchone(); c.close(); g.close()
    if not cap: flash('Not found.','danger'); return redirect(url_for('dashboard'))
    now = datetime.now()
    if not (cap['user_id']==session['uid'] or cap['recipient_id']==session['uid'] or cap['is_public']):
        flash('Access denied.','danger'); return redirect(url_for('feed'))
    return render_template('view.html', cap=cap, now=now, unlocked=cap['unlock_date']<=now)

# ── CONNECTIONS ──
@app.route('/connect/<int:oid>', methods=['POST'])
@auth
def connect(oid):
    g = db(); c = g.cursor()
    try: c.execute("INSERT INTO connections(sender_id,receiver_id) VALUES(%s,%s)",(session['uid'],oid)); g.commit(); flash('Request sent.','success')
    except: flash('Already sent.','danger')
    finally: c.close(); g.close()
    return redirect(request.referrer or url_for('feed'))

@app.route('/accept/<int:cid>', methods=['POST'])
@auth
def accept(cid):
    g = db(); c = g.cursor()
    c.execute("UPDATE connections SET status='accepted' WHERE id=%s AND receiver_id=%s",(cid,session['uid']))
    g.commit(); c.close(); g.close(); flash('Connected!','success')
    return redirect(url_for('feed'))

@app.route('/reject/<int:cid>', methods=['POST'])
@auth
def reject(cid):
    g = db(); c = g.cursor()
    c.execute("DELETE FROM connections WHERE id=%s AND receiver_id=%s",(cid,session['uid']))
    g.commit(); c.close(); g.close()
    return redirect(url_for('feed'))

# ── CHAT ──
@app.route('/chat')
@auth
def chat(): return render_template('chat.html', users=friends(session['uid']))

@app.route('/chat/<int:oid>')
@auth
def chat_with(oid):
    g = db(); c = g.cursor(dictionary=True); now = datetime.now()
    c.execute("SELECT id,username FROM users WHERE id=%s",(oid,)); other = c.fetchone()
    c.execute("SELECT m.*,u.username as sname FROM messages m JOIN users u ON m.sender_id=u.id WHERE ((m.sender_id=%s AND m.receiver_id=%s) OR (m.sender_id=%s AND m.receiver_id=%s)) AND (m.scheduled_at IS NULL OR m.scheduled_at<=%s) ORDER BY COALESCE(m.scheduled_at,m.sent_at) ASC",
        (session['uid'],oid,oid,session['uid'],now))
    msgs = c.fetchall()
    c.execute("SELECT * FROM messages WHERE sender_id=%s AND receiver_id=%s AND scheduled_at>%s ORDER BY scheduled_at ASC",(session['uid'],oid,now))
    sched = c.fetchall()
    c.execute("UPDATE messages SET is_read=1 WHERE receiver_id=%s AND sender_id=%s",(session['uid'],oid))
    g.commit(); c.close(); g.close()
    return render_template('chat.html', users=friends(session['uid']), other=other, msgs=msgs, sched=sched, now=now)

@app.route('/send', methods=['POST'])
@auth
def send():
    rid = request.form.get('receiver_id')
    content = (request.form.get('content') or '').strip()
    sat = request.form.get('scheduled_at') or None
    img = None
    if 'image' in request.files:
        f = request.files['image']
        if f and f.filename:
            ext = f.filename.rsplit('.',1)[-1].lower()
            if ext in {'png','jpg','jpeg','gif','webp'}:
                fn = f"{session['uid']}_{int(datetime.now().timestamp())}.{ext}"
                f.save(os.path.join(app.root_path, UPLOADS, fn))
                img = url_for('static', filename=f'uploads/{fn}')
    if not content and not img: return jsonify({'ok':False})
    sdt = None; is_sched = False
    if sat:
        try:
            sdt = datetime.strptime(sat,'%Y-%m-%dT%H:%M')
            if sdt > datetime.now(): is_sched = True
            else: sdt = None
        except: pass
    g = db(); c = g.cursor()
    try: c.execute("INSERT INTO messages(sender_id,receiver_id,content,scheduled_at,image_url) VALUES(%s,%s,%s,%s,%s)",(session['uid'],rid,content,sdt,img))
    except: c.execute("INSERT INTO messages(sender_id,receiver_id,content,scheduled_at) VALUES(%s,%s,%s,%s)",(session['uid'],rid,content,sdt))
    g.commit(); c.close(); g.close()
    return jsonify({'ok':True,'content':content,'img':img or '','time':sdt.strftime('%I:%M %p') if is_sched else datetime.now().strftime('%I:%M %p'),'sched':is_sched})

# ── PROFILE & SEARCH ──
@app.route('/profile/<uname>')
@auth
def profile(uname):
    g = db(); c = g.cursor(dictionary=True); now = datetime.now()
    c.execute("SELECT * FROM users WHERE username=%s",(uname,)); u = c.fetchone()
    if not u: flash('Not found.','danger'); return redirect(url_for('feed'))
    is_own = u['id']==session['uid']
    cs = None; crow = None
    if not is_own:
        c.execute("SELECT * FROM connections WHERE (sender_id=%s AND receiver_id=%s) OR (sender_id=%s AND receiver_id=%s)",(session['uid'],u['id'],u['id'],session['uid']))
        crow = c.fetchone()
        if crow: cs = 'accepted' if crow['status']=='accepted' else ('sent' if crow['sender_id']==session['uid'] else 'recv')
    c.execute("SELECT * FROM capsules WHERE user_id=%s AND (is_public=1 OR %s=1) ORDER BY created_at DESC",(u['id'],1 if is_own else 0))
    caps = c.fetchall()
    c.execute("SELECT COUNT(*) n FROM capsules WHERE user_id=%s",(u['id'],)); total = c.fetchone()['n']
    c.execute("SELECT COUNT(*) n FROM capsules WHERE user_id=%s AND unlock_date>%s",(u['id'],now)); locked = c.fetchone()['n']
    c.execute("SELECT COUNT(*) n FROM connections WHERE (sender_id=%s OR receiver_id=%s) AND status='accepted'",(u['id'],u['id'])); fc = c.fetchone()['n']
    c.close(); g.close()
    return render_template('profile.html', u=u, caps=caps, now=now, total=total, locked=locked, fc=fc, cs=cs, crow=crow, is_own=is_own)

@app.route('/search_users')
@auth
def search_users():
    q = request.args.get('q','')
    g = db(); c = g.cursor(dictionary=True)
    c.execute("SELECT username FROM users WHERE username LIKE %s AND id!=%s LIMIT 5",(f'%{q}%',session['uid']))
    r = c.fetchall(); c.close(); g.close()
    return jsonify([x['username'] for x in r])

@app.route('/search')
@auth
def search():
    q = request.args.get('q','').strip(); users = []
    if q:
        g = db(); c = g.cursor(dictionary=True)
        c.execute("SELECT u.*,(SELECT status FROM connections WHERE (sender_id=%s AND receiver_id=u.id) OR (sender_id=u.id AND receiver_id=%s) LIMIT 1) cs FROM users u WHERE u.username LIKE %s AND u.id!=%s LIMIT 20",
            (session['uid'],session['uid'],f'%{q}%',session['uid']))
        users = c.fetchall(); c.close(); g.close()
    return render_template('search.html', users=users, q=q)

if __name__ == '__main__': app.run(debug=True, use_reloader=True, reloader_type='stat', extra_files=[])