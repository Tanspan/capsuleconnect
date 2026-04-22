import streamlit as st
import mysql.connector
import hashlib
import os
from datetime import datetime
from PIL import Image
import io

# ── PAGE CONFIG ──
st.set_page_config(
    page_title="CapsuleConnect",
    page_icon="⏳",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ── STYLING ──
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@600;700&family=DM+Sans:wght@300;400;500&display=swap');

html, body, [class*="css"] {
    font-family: 'DM Sans', sans-serif;
}
h1, h2, h3 { font-family: 'Playfair Display', serif; }

/* Sidebar */
section[data-testid="stSidebar"] {
    background: linear-gradient(160deg, #1a1a2e 0%, #16213e 100%);
    color: white;
}
section[data-testid="stSidebar"] * { color: white !important; }
section[data-testid="stSidebar"] .stButton button {
    background: rgba(255,255,255,0.08);
    color: white !important;
    border: 1px solid rgba(255,255,255,0.15);
    border-radius: 8px;
    width: 100%;
    text-align: left;
    margin-bottom: 4px;
    transition: all 0.2s;
}
section[data-testid="stSidebar"] .stButton button:hover {
    background: rgba(255,165,0,0.25);
    border-color: #f0a500;
}

/* Cards */
.capsule-card {
    background: white;
    border-radius: 16px;
    padding: 1.4rem 1.6rem;
    margin-bottom: 1rem;
    border: 1px solid #eee;
    box-shadow: 0 2px 12px rgba(0,0,0,0.06);
    transition: box-shadow 0.2s;
}
.capsule-card:hover { box-shadow: 0 4px 24px rgba(0,0,0,0.12); }
.locked-card {
    background: linear-gradient(135deg, #f8f8ff, #e8e8f8);
    border-color: #c0c0e0;
}
.capsule-title { font-family: 'Playfair Display', serif; font-size: 1.2rem; font-weight: 700; color: #1a1a2e; }
.capsule-meta { font-size: 0.82rem; color: #888; margin: 0.3rem 0 0.8rem; }
.capsule-msg { color: #333; line-height: 1.6; }
.badge {
    display: inline-block; padding: 3px 10px; border-radius: 20px;
    font-size: 0.75rem; font-weight: 500; margin-right: 6px;
}
.badge-public { background:#e8f5e9; color:#2e7d32; }
.badge-private { background:#fce4ec; color:#c62828; }
.badge-locked { background:#fff3e0; color:#e65100; }
.badge-unlocked { background:#e3f2fd; color:#1565c0; }
.user-card {
    background: white; border-radius: 12px; padding: 1rem 1.2rem;
    border: 1px solid #eee; margin-bottom: 0.6rem;
    display: flex; align-items: center; gap: 1rem;
}
.avatar {
    width: 42px; height: 42px; border-radius: 50%;
    background: linear-gradient(135deg, #667eea, #764ba2);
    display: flex; align-items: center; justify-content: center;
    color: white; font-weight: 700; font-size: 1.1rem;
    flex-shrink: 0;
}
.msg-bubble-me {
    background: linear-gradient(135deg, #667eea, #764ba2);
    color: white; border-radius: 18px 18px 4px 18px;
    padding: 0.6rem 1rem; max-width: 70%; margin: 0.3rem 0 0.3rem auto;
    font-size: 0.9rem;
}
.msg-bubble-other {
    background: #f0f0f0; color: #333;
    border-radius: 18px 18px 18px 4px;
    padding: 0.6rem 1rem; max-width: 70%; margin: 0.3rem auto 0.3rem 0;
    font-size: 0.9rem;
}
.msg-time { font-size: 0.7rem; color: #aaa; margin: 0 0.5rem; }
.stat-box {
    background: white; border-radius: 14px; padding: 1.2rem;
    text-align: center; border: 1px solid #eee;
    box-shadow: 0 2px 8px rgba(0,0,0,0.05);
}
.stat-num { font-size: 2rem; font-weight: 700; color: #1a1a2e; font-family: 'Playfair Display', serif; }
.stat-label { font-size: 0.8rem; color: #888; margin-top: 0.2rem; }
.section-header {
    font-family: 'Playfair Display', serif;
    font-size: 1.5rem; font-weight: 700; color: #1a1a2e;
    margin-bottom: 1rem; padding-bottom: 0.5rem;
    border-bottom: 2px solid #f0a500;
    display: inline-block;
}
.hero-banner {
    background: linear-gradient(135deg, #1a1a2e 0%, #16213e 60%, #0f3460 100%);
    border-radius: 20px; padding: 2.5rem; margin-bottom: 2rem;
    color: white; text-align: center;
}
.hero-banner h1 { color: white; font-size: 2.2rem; margin: 0; }
.hero-banner p { color: rgba(255,255,255,0.7); margin: 0.5rem 0 0; }
</style>
""", unsafe_allow_html=True)

# ── DB CONFIG ── (update these for your deployment)
DB_CONFIG = {
    'host': st.secrets.get("DB_HOST", "localhost"),
    'user': st.secrets.get("DB_USER", "root"),
    'password': st.secrets.get("DB_PASSWORD", "root0_0"),
    'database': st.secrets.get("DB_NAME", "capsuleconnect")
}

UPLOADS = os.path.join("static", "uploads")
os.makedirs(UPLOADS, exist_ok=True)

# ── HELPERS ──
def db():
    try:
        return mysql.connector.connect(**DB_CONFIG)
    except Exception as e:
        st.error(f"Database connection failed: {e}")
        return None

def hp(p): return hashlib.sha256(p.encode()).hexdigest()

def init_session():
    for key in ['uid', 'uname', 'page', 'chat_with', 'view_capsule', 'view_profile']:
        if key not in st.session_state:
            st.session_state[key] = None
    if 'page' not in st.session_state or st.session_state.page is None:
        st.session_state.page = 'landing'

def go(page, **kwargs):
    st.session_state.page = page
    for k, v in kwargs.items():
        st.session_state[k] = v
    st.rerun()

def is_logged_in():
    return st.session_state.get('uid') is not None

def friends_list(uid):
    g = db()
    if not g: return []
    c = g.cursor(dictionary=True)
    c.execute("""SELECT u.id, u.username FROM users u
                 JOIN connections cn ON (cn.sender_id=%s AND cn.receiver_id=u.id)
                    OR (cn.receiver_id=%s AND cn.sender_id=u.id)
                 WHERE cn.status='accepted'""", (uid, uid))
    r = c.fetchall(); c.close(); g.close()
    return r

def avatar_html(username, size=42):
    letter = username[0].upper() if username else "?"
    colors = ["#667eea","#764ba2","#f093fb","#f5576c","#4facfe","#43e97b","#fa709a","#fee140"]
    color = colors[ord(letter) % len(colors)]
    return f'<div style="width:{size}px;height:{size}px;border-radius:50%;background:{color};display:inline-flex;align-items:center;justify-content:center;color:white;font-weight:700;font-size:{size//2.5:.0f}px;">{letter}</div>'

# ── PAGES ──

def page_landing():
    st.markdown("""
    <div class="hero-banner">
        <h1>⏳ CapsuleConnect</h1>
        <p>Lock your memories. Unlock the future.</p>
    </div>
    """, unsafe_allow_html=True)
    c1, c2, c3 = st.columns([1, 2, 1])
    with c2:
        tab1, tab2 = st.tabs(["🔑 Login", "📝 Register"])
        with tab1:
            with st.form("login_form"):
                email = st.text_input("Email")
                password = st.text_input("Password", type="password")
                if st.form_submit_button("Login", use_container_width=True):
                    g = db()
                    if g:
                        c = g.cursor(dictionary=True)
                        c.execute("SELECT * FROM users WHERE email=%s AND password=%s", (email, hp(password)))
                        u = c.fetchone(); c.close(); g.close()
                        if u:
                            st.session_state.uid = u['id']
                            st.session_state.uname = u['username']
                            go('feed')
                        else:
                            st.error("Invalid credentials.")
        with tab2:
            with st.form("reg_form"):
                username = st.text_input("Username")
                email = st.text_input("Email")
                password = st.text_input("Password", type="password")
                if st.form_submit_button("Create Account", use_container_width=True):
                    g = db()
                    if g:
                        c = g.cursor()
                        try:
                            c.execute("INSERT INTO users(username,email,password) VALUES(%s,%s,%s)",
                                      (username, email, hp(password)))
                            g.commit()
                            st.success("Account created! Please login.")
                        except:
                            st.error("Username or email already exists.")
                        finally:
                            c.close(); g.close()


def page_feed():
    g = db()
    if not g: return
    c = g.cursor(dictionary=True)
    now = datetime.now()
    uid = st.session_state.uid

    # Friend IDs
    c.execute("""SELECT CASE WHEN sender_id=%s THEN receiver_id ELSE sender_id END AS fid
                 FROM connections WHERE (sender_id=%s OR receiver_id=%s) AND status='accepted'""",
              (uid,)*3)
    fids = [r['fid'] for r in c.fetchall()]

    # Pending requests
    c.execute("""SELECT cn.*,u.username FROM connections cn JOIN users u ON cn.sender_id=u.id
                 WHERE cn.receiver_id=%s AND cn.status='pending'""", (uid,))
    reqs = c.fetchall()

    if reqs:
        st.markdown('<div class="section-header">🔔 Friend Requests</div>', unsafe_allow_html=True)
        for req in reqs:
            col1, col2, col3 = st.columns([3, 1, 1])
            with col1:
                st.markdown(f"{avatar_html(req['username'])} **{req['username']}** sent you a request", unsafe_allow_html=True)
            with col2:
                if st.button("✅ Accept", key=f"acc_{req['id']}"):
                    g2 = db()
                    if g2:
                        c2 = g2.cursor()
                        c2.execute("UPDATE connections SET status='accepted' WHERE id=%s AND receiver_id=%s", (req['id'], uid))
                        g2.commit(); c2.close(); g2.close()
                        st.rerun()
            with col3:
                if st.button("❌ Reject", key=f"rej_{req['id']}"):
                    g2 = db()
                    if g2:
                        c2 = g2.cursor()
                        c2.execute("DELETE FROM connections WHERE id=%s AND receiver_id=%s", (req['id'], uid))
                        g2.commit(); c2.close(); g2.close()
                        st.rerun()
        st.divider()

    st.markdown('<div class="section-header">📰 Friend\'s Capsules</div>', unsafe_allow_html=True)
    if fids:
        fmt = ','.join(['%s']*len(fids))
        c.execute(f"""SELECT cp.*,u.username FROM capsules cp JOIN users u ON cp.user_id=u.id
                      WHERE cp.user_id IN ({fmt}) AND cp.is_public=1 AND cp.unlock_date<=%s
                      ORDER BY cp.unlock_date DESC LIMIT 20""", (*fids, now))
        posts = c.fetchall()
        if posts:
            for p in posts:
                locked = p['unlock_date'] > now
                badge_vis = '<span class="badge badge-public">Public</span>'
                badge_lock = f'<span class="badge badge-{"locked" if locked else "unlocked"}">{"🔒 Locked" if locked else "🔓 Unlocked"}</span>'
                card_cls = "capsule-card locked-card" if locked else "capsule-card"
                content = p['message'] if not locked else "🔒 This capsule is still locked."
                st.markdown(f"""
                <div class="{card_cls}">
                    <div class="capsule-title">{p['title']}</div>
                    <div class="capsule-meta">by {p['username']} · {p['unlock_date'].strftime('%b %d, %Y') if isinstance(p['unlock_date'], datetime) else p['unlock_date']} {badge_vis} {badge_lock}</div>
                    <div class="capsule-msg">{content}</div>
                </div>
                """, unsafe_allow_html=True)
                if st.button("View", key=f"view_feed_{p['id']}"):
                    go('view', view_capsule=p['id'])
        else:
            st.info("No public capsules from friends yet.")
    else:
        st.info("Connect with friends to see their capsules here.")
    c.close(); g.close()


def page_dashboard():
    g = db()
    if not g: return
    c = g.cursor(dictionary=True)
    now = datetime.now()
    uid = st.session_state.uid

    c.execute("SELECT * FROM capsules WHERE user_id=%s ORDER BY created_at DESC", (uid,))
    caps = c.fetchall()
    c.execute("""SELECT cp.*,u.username as sname FROM capsules cp JOIN users u ON cp.user_id=u.id
                 WHERE cp.recipient_id=%s ORDER BY cp.created_at DESC""", (uid,))
    recv = c.fetchall()
    c.close(); g.close()

    total = len(caps)
    locked = sum(1 for cap in caps if cap['unlock_date'] > now)
    unlocked = total - locked

    col1, col2, col3 = st.columns(3)
    for col, num, label in [(col1, total, "Total Capsules"), (col2, locked, "Still Locked"), (col3, unlocked, "Unlocked")]:
        with col:
            st.markdown(f'<div class="stat-box"><div class="stat-num">{num}</div><div class="stat-label">{label}</div></div>', unsafe_allow_html=True)
    st.write("")

    st.markdown('<div class="section-header">📦 My Capsules</div>', unsafe_allow_html=True)
    if caps:
        for cap in caps:
            locked = cap['unlock_date'] > now
            badge_vis = f'<span class="badge badge-{"public" if cap["is_public"] else "private"}">{"Public" if cap["is_public"] else "Private"}</span>'
            badge_lock = f'<span class="badge badge-{"locked" if locked else "unlocked"}">{"🔒 Locked" if locked else "🔓 Unlocked"}</span>'
            content = cap['message'] if not locked else "🔒 Opens on " + (cap['unlock_date'].strftime('%b %d, %Y %I:%M %p') if isinstance(cap['unlock_date'], datetime) else str(cap['unlock_date']))
            st.markdown(f"""
            <div class="capsule-card {"locked-card" if locked else ""}">
                <div class="capsule-title">{cap['title']}</div>
                <div class="capsule-meta">Created {cap['created_at'].strftime('%b %d, %Y') if isinstance(cap['created_at'], datetime) else cap['created_at']} {badge_vis} {badge_lock}</div>
                <div class="capsule-msg">{content}</div>
            </div>
            """, unsafe_allow_html=True)
            if st.button("View", key=f"view_dash_{cap['id']}"):
                go('view', view_capsule=cap['id'])
    else:
        st.info("You haven't created any capsules yet.")
        if st.button("➕ Create your first capsule"):
            go('create')

    if recv:
        st.divider()
        st.markdown('<div class="section-header">📬 Received Capsules</div>', unsafe_allow_html=True)
        for cap in recv:
            locked = cap['unlock_date'] > now
            content = cap['message'] if not locked else "🔒 This capsule is still locked."
            st.markdown(f"""
            <div class="capsule-card">
                <div class="capsule-title">{cap['title']}</div>
                <div class="capsule-meta">from {cap['sname']}</div>
                <div class="capsule-msg">{content}</div>
            </div>
            """, unsafe_allow_html=True)


def page_create():
    st.markdown('<div class="section-header">✨ Create a New Capsule</div>', unsafe_allow_html=True)
    with st.form("create_capsule"):
        title = st.text_input("Capsule Title", placeholder="e.g. My 2024 Memories")
        message = st.text_area("Your Message", placeholder="Write what you want to remember...", height=180)
        col1, col2 = st.columns(2)
        with col1:
            ctype = st.selectbox("Type", ["personal", "shared", "public_event"])
        with col2:
            is_public = st.checkbox("Make Public", value=True)
        unlock_date = st.date_input("Unlock Date", min_value=datetime.now().date())
        unlock_time = st.time_input("Unlock Time")
        recipient = st.text_input("Send to (username, optional)", placeholder="Leave blank for yourself")
        submitted = st.form_submit_button("🔒 Lock Capsule", use_container_width=True)

        if submitted:
            if not title or not message:
                st.error("Title and message are required.")
            else:
                unlock_dt = datetime.combine(unlock_date, unlock_time)
                g = db()
                if g:
                    c = g.cursor(dictionary=True)
                    rid = None
                    if recipient.strip():
                        c.execute("SELECT id FROM users WHERE username=%s", (recipient.strip(),))
                        r = c.fetchone()
                        if not r:
                            st.error("Recipient not found.")
                            c.close(); g.close()
                            return
                        rid = r['id']
                    c.execute("""INSERT INTO capsules(user_id,title,message,type,unlock_date,is_public,recipient_id)
                                 VALUES(%s,%s,%s,%s,%s,%s,%s)""",
                              (st.session_state.uid, title, message, ctype, unlock_dt, 1 if is_public else 0, rid))
                    g.commit()
                    cid = c.lastrowid
                    try:
                        c.execute("INSERT INTO stories(user_id,capsule_id) VALUES(%s,%s)", (st.session_state.uid, cid))
                        g.commit()
                    except: pass
                    c.close(); g.close()
                    st.success("🎉 Capsule locked!")
                    go('dashboard')


def page_view():
    cid = st.session_state.get('view_capsule')
    if not cid:
        go('dashboard')
        return
    g = db()
    if not g: return
    c = g.cursor(dictionary=True)
    c.execute("SELECT cp.*,u.username FROM capsules cp JOIN users u ON cp.user_id=u.id WHERE cp.id=%s", (cid,))
    cap = c.fetchone(); c.close(); g.close()
    if not cap:
        st.error("Capsule not found.")
        go('dashboard'); return

    uid = st.session_state.uid
    now = datetime.now()
    unlocked = cap['unlock_date'] <= now
    can_view = (cap['user_id'] == uid or cap['recipient_id'] == uid or cap['is_public'])

    if not can_view:
        st.error("Access denied.")
        go('feed'); return

    if st.button("← Back"):
        go('dashboard')

    badge_lock = f'🔓 Unlocked' if unlocked else f'🔒 Locked until {cap["unlock_date"].strftime("%b %d, %Y %I:%M %p") if isinstance(cap["unlock_date"], datetime) else cap["unlock_date"]}'
    st.markdown(f"""
    <div class="capsule-card" style="padding:2rem;">
        <div class="capsule-title" style="font-size:1.8rem;">{cap['title']}</div>
        <div class="capsule-meta" style="font-size:0.9rem;">
            by {cap['username']} · {badge_lock}
            {'<span class="badge badge-public">Public</span>' if cap['is_public'] else '<span class="badge badge-private">Private</span>'}
        </div>
        {"<hr><div class='capsule-msg' style='font-size:1rem;line-height:1.8;'>" + cap['message'] + "</div>" if unlocked else "<div style='color:#e65100;font-size:1.1rem;margin-top:1rem;'>🔒 This capsule is still sealed. Come back on the unlock date!</div>"}
    </div>
    """, unsafe_allow_html=True)


def page_chat():
    uid = st.session_state.uid
    fl = friends_list(uid)
    now = datetime.now()

    col_left, col_right = st.columns([1, 2])

    with col_left:
        st.markdown("**💬 Friends**")
        if not fl:
            st.info("No friends yet. Search for users to connect.")
        for f in fl:
            if st.button(f"{f['username']}", key=f"chat_friend_{f['id']}"):
                st.session_state.chat_with = f['id']
                st.rerun()

    with col_right:
        oid = st.session_state.get('chat_with')
        if not oid:
            st.info("Select a friend to start chatting.")
            return

        # Get other user info
        g = db()
        if not g: return
        c = g.cursor(dictionary=True)
        c.execute("SELECT id,username FROM users WHERE id=%s", (oid,))
        other = c.fetchone()
        if not other:
            st.warning("User not found.")
            c.close(); g.close(); return

        st.markdown(f"### {avatar_html(other['username'])} &nbsp; {other['username']}", unsafe_allow_html=True)
        st.divider()

        # Load messages
        c.execute("""SELECT m.*,u.username as sname FROM messages m JOIN users u ON m.sender_id=u.id
                     WHERE ((m.sender_id=%s AND m.receiver_id=%s) OR (m.sender_id=%s AND m.receiver_id=%s))
                     AND (m.scheduled_at IS NULL OR m.scheduled_at<=%s)
                     ORDER BY COALESCE(m.scheduled_at,m.sent_at) ASC""",
                  (uid, oid, oid, uid, now))
        msgs = c.fetchall()

        # Mark as read
        c.execute("UPDATE messages SET is_read=1 WHERE receiver_id=%s AND sender_id=%s", (uid, oid))
        g.commit(); c.close(); g.close()

        # Display messages
        chat_html = ""
        for m in msgs:
            is_me = m['sender_id'] == uid
            bubble_cls = "msg-bubble-me" if is_me else "msg-bubble-other"
            time_str = m['sent_at'].strftime('%I:%M %p') if m.get('sent_at') else ""
            content = m.get('content') or ''
            chat_html += f'<div><div class="{bubble_cls}">{content}</div><div class="msg-time" style="text-align:{"right" if is_me else "left"}">{time_str}</div></div>'

        st.markdown(f'<div style="max-height:400px;overflow-y:auto;padding:0.5rem;">{chat_html}</div>', unsafe_allow_html=True)
        st.write("")

        # Send message
        with st.form(f"send_msg_{oid}", clear_on_submit=True):
            col_msg, col_btn = st.columns([4, 1])
            with col_msg:
                content = st.text_input("Message", label_visibility="collapsed", placeholder="Type a message...")
            with col_btn:
                send = st.form_submit_button("Send")
            if send and content.strip():
                g2 = db()
                if g2:
                    c2 = g2.cursor()
                    c2.execute("INSERT INTO messages(sender_id,receiver_id,content) VALUES(%s,%s,%s)",
                               (uid, oid, content.strip()))
                    g2.commit(); c2.close(); g2.close()
                    st.rerun()


def page_search():
    st.markdown('<div class="section-header">🔍 Find Users</div>', unsafe_allow_html=True)
    uid = st.session_state.uid
    q = st.text_input("Search by username", placeholder="Type a name...")

    if q:
        g = db()
        if not g: return
        c = g.cursor(dictionary=True)
        c.execute("""SELECT u.*,
                     (SELECT status FROM connections
                      WHERE (sender_id=%s AND receiver_id=u.id) OR (sender_id=u.id AND receiver_id=%s) LIMIT 1) cs
                     FROM users u WHERE u.username LIKE %s AND u.id!=%s LIMIT 20""",
                  (uid, uid, f'%{q}%', uid))
        users = c.fetchall(); c.close(); g.close()

        if not users:
            st.info("No users found.")
        for u in users:
            col1, col2, col3 = st.columns([3, 1, 1])
            with col1:
                st.markdown(f"{avatar_html(u['username'])} &nbsp; **{u['username']}**", unsafe_allow_html=True)
            with col2:
                if st.button("View Profile", key=f"view_prof_{u['id']}"):
                    go('profile', view_profile=u['username'])
            with col3:
                cs = u.get('cs')
                if cs == 'accepted':
                    st.markdown("✅ Friends")
                elif cs == 'pending':
                    st.markdown("⏳ Pending")
                else:
                    if st.button("➕ Connect", key=f"conn_{u['id']}"):
                        g2 = db()
                        if g2:
                            c2 = g2.cursor()
                            try:
                                c2.execute("INSERT INTO connections(sender_id,receiver_id) VALUES(%s,%s)", (uid, u['id']))
                                g2.commit()
                                st.success("Request sent!")
                            except:
                                st.warning("Already sent.")
                            finally:
                                c2.close(); g2.close()
                        st.rerun()


def page_profile():
    uname = st.session_state.get('view_profile') or st.session_state.get('uname')
    uid = st.session_state.uid
    now = datetime.now()

    g = db()
    if not g: return
    c = g.cursor(dictionary=True)
    c.execute("SELECT * FROM users WHERE username=%s", (uname,))
    u = c.fetchone()
    if not u:
        st.error("User not found.")
        c.close(); g.close(); go('feed'); return

    is_own = u['id'] == uid
    cs = None; crow = None
    if not is_own:
        c.execute("""SELECT * FROM connections
                     WHERE (sender_id=%s AND receiver_id=%s) OR (sender_id=%s AND receiver_id=%s)""",
                  (uid, u['id'], u['id'], uid))
        crow = c.fetchone()
        if crow:
            cs = 'accepted' if crow['status'] == 'accepted' else ('sent' if crow['sender_id'] == uid else 'recv')

    c.execute("SELECT COUNT(*) n FROM capsules WHERE user_id=%s", (u['id'],))
    total = c.fetchone()['n']
    c.execute("SELECT COUNT(*) n FROM capsules WHERE user_id=%s AND unlock_date>%s", (u['id'], now))
    locked = c.fetchone()['n']
    c.execute("SELECT COUNT(*) n FROM connections WHERE (sender_id=%s OR receiver_id=%s) AND status='accepted'", (u['id'], u['id']))
    fc = c.fetchone()['n']
    c.execute("SELECT * FROM capsules WHERE user_id=%s AND is_public=1 ORDER BY created_at DESC", (u['id'],))
    caps = c.fetchall()
    c.close(); g.close()

    if st.button("← Back"):
        go('feed')

    col_av, col_info = st.columns([1, 3])
    with col_av:
        st.markdown(f'<div style="margin-top:1rem;">{avatar_html(u["username"], size=80)}</div>', unsafe_allow_html=True)
    with col_info:
        st.markdown(f"## {u['username']}")
        st.markdown(f"📧 {u['email']}")
        if not is_own:
            if cs == 'accepted':
                st.success("✅ Friends")
                if st.button("💬 Message"):
                    st.session_state.chat_with = u['id']
                    go('chat')
            elif cs == 'sent':
                st.info("⏳ Request sent")
            elif cs == 'recv':
                if st.button("✅ Accept Request"):
                    g2 = db()
                    if g2:
                        c2 = g2.cursor()
                        c2.execute("UPDATE connections SET status='accepted' WHERE id=%s AND receiver_id=%s", (crow['id'], uid))
                        g2.commit(); c2.close(); g2.close()
                        st.rerun()
            else:
                if st.button("➕ Connect"):
                    g2 = db()
                    if g2:
                        c2 = g2.cursor()
                        try:
                            c2.execute("INSERT INTO connections(sender_id,receiver_id) VALUES(%s,%s)", (uid, u['id']))
                            g2.commit()
                            st.success("Request sent!")
                        except:
                            st.warning("Already sent.")
                        c2.close(); g2.close()
                    st.rerun()

    col1, col2, col3 = st.columns(3)
    for col, num, label in [(col1, total, "Capsules"), (col2, locked, "Locked"), (col3, fc, "Friends")]:
        with col:
            st.markdown(f'<div class="stat-box"><div class="stat-num">{num}</div><div class="stat-label">{label}</div></div>', unsafe_allow_html=True)
    st.write("")

    if caps:
        st.markdown('<div class="section-header">Public Capsules</div>', unsafe_allow_html=True)
        for cap in caps:
            lk = cap['unlock_date'] > now
            content = cap['message'] if not lk else "🔒 Locked"
            st.markdown(f"""
            <div class="capsule-card {"locked-card" if lk else ""}">
                <div class="capsule-title">{cap['title']}</div>
                <div class="capsule-meta">{cap['unlock_date'].strftime('%b %d, %Y') if isinstance(cap['unlock_date'], datetime) else cap['unlock_date']}</div>
                <div class="capsule-msg">{content}</div>
            </div>
            """, unsafe_allow_html=True)


# ── SIDEBAR NAV ──
def sidebar():
    with st.sidebar:
        st.markdown("## ⏳ CapsuleConnect")
        st.markdown(f"👤 **{st.session_state.uname}**")
        st.divider()

        pages = [
            ("🏠", "Feed", "feed"),
            ("📦", "My Capsules", "dashboard"),
            ("✨", "Create Capsule", "create"),
            ("💬", "Chat", "chat"),
            ("🔍", "Search Users", "search"),
            ("👤", "My Profile", "profile"),
        ]
        for icon, label, page_key in pages:
            if st.button(f"{icon}  {label}", key=f"nav_{page_key}"):
                if page_key == 'profile':
                    st.session_state.view_profile = st.session_state.uname
                go(page_key)

        st.divider()
        if st.button("🚪  Logout"):
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()


# ── ROUTER ──
def main():
    init_session()

    if not is_logged_in():
        page_landing()
        return

    sidebar()

    page = st.session_state.get('page', 'feed')

    if page == 'feed':       page_feed()
    elif page == 'dashboard': page_dashboard()
    elif page == 'create':   page_create()
    elif page == 'view':     page_view()
    elif page == 'chat':     page_chat()
    elif page == 'search':   page_search()
    elif page == 'profile':  page_profile()
    else:                    page_feed()


main()
