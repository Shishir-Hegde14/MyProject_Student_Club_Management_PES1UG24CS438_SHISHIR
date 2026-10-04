from concurrent.futures import ThreadPoolExecutor
from datetime import date, timedelta

import pytest
from werkzeug.security import generate_password_hash

from app import create_app
from services import PortalError


@pytest.fixture
def app(tmp_path):
    app = create_app({'TESTING': True, 'DATABASE': str(tmp_path / 'test.sqlite3'), 'SECRET_KEY': 'test-only-secret'})
    p = app.extensions['portal']
    with p.db(True) as con:
        con.execute("INSERT INTO clubs VALUES(1,'Test club',1000000)")
        for id, name, role, club in [(1,'lead','lead',1),(2,'faculty','coordinator',None),(3,'finance','finance',None),(4,'dean','dean',None),(5,'student','student',None),(6,'gate','checkin',None),(7,'student2','student',None),(8,'otherlead','lead',1)]:
            con.execute('INSERT INTO users VALUES(?,?,?,?,?)', (id, name, generate_password_hash('test-pass', method='pbkdf2:sha256:1000'), role, club))
    return app


@pytest.fixture
def p(app):
    return app.extensions['portal']


def draft(p, amount='1000', capacity=20):
    return p.create_event(1, 'Club workshop', (date.today()+timedelta(days=7)).isoformat(), 'Seminar hall', capacity, [('Equipment', amount)])


def approved(p, capacity=20):
    e = draft(p, capacity=capacity)
    p.submit(1, e)
    for actor in (2, 3, 4):
        p.review(actor, e, 'approve')
    return e


def sign_in(client, user_id):
    with client.session_transaction() as session:
        session['user_id'] = user_id
        session['csrf'] = 'form-test-token'


def test_TC01_required_fields_and_money(p):
    with pytest.raises(PortalError):
        p.create_event(1, '', date.today().isoformat(), 'Hall', 10, [('Food','100')])
    for value in ('-1', '0', 'NaN', 'Infinity', '0.001', 'abc'):
        with pytest.raises(PortalError):
            p.money(value)
    assert p.money('125.50') == 12550


def test_TC02_proposal_and_budget_items(p):
    e = draft(p)
    d = p.details(1,e)
    assert d['status'] == 'Draft' and d['budget'] == 100000
    assert d['items'][0]['description'] == 'Equipment'


def test_TC03_approval_order_and_signoffs(p):
    e = draft(p)
    p.submit(1,e)
    with pytest.raises(PortalError):
        p.review(4,e,'approve')
    p.review(2,e,'approve')
    with pytest.raises(PortalError):
        p.review(4,e,'approve')
    p.review(3,e,'approve')
    p.review(4,e,'approve')
    d = p.details(1,e)
    assert d['status'] == 'Approved'
    assert [a['actor_id'] for a in d['approvals']] == [2,3,4]
    assert all(a['signed_at'] for a in d['approvals'])


def test_TC04_reject_reason_and_release(p):
    e = draft(p)
    p.submit(1,e)
    assert p.dashboard(1)[1] == 900000
    with pytest.raises(PortalError):
        p.review(2,e,'reject')
    p.review(2,e,'reject','Venue is unavailable')
    assert p.details(1,e)['status'] == 'Rejected'
    assert p.dashboard(1)[1] == 1000000
    with pytest.raises(PortalError):
        p.review(3,e,'approve')


def test_TC05_budget_limit_and_revision(p):
    e = draft(p, '10001')
    with pytest.raises(PortalError):
        p.submit(1,e)
    assert p.details(1,e)['status'] == 'Draft'
    p.create_event(1,'Revised workshop',(date.today()+timedelta(days=7)).isoformat(),'Hall',20,[('Equipment','2000')],e)
    p.submit(1,e)
    assert p.details(1,e)['status'] == 'Faculty pending'


def test_TC06_registration_requires_approval(p):
    e = draft(p)
    with pytest.raises(PortalError):
        p.register(5,e)
    p.submit(1,e)
    with pytest.raises(PortalError):
        p.register(5,e)


def test_TC07_unique_tickets_and_repeat_registration(p):
    e = approved(p)
    t1, t2 = p.register(5,e), p.register(7,e)
    assert t1 != t2 and p.register(5,e) == t1
    assert p.details(1,e)['registrations'] == 2
    assert p.token(p.ticket(5,t1)).split(':')[1:3] == [str(e),'5']


def test_TC08_capacity(p):
    e = approved(p,capacity=1)
    p.register(5,e)
    with pytest.raises(PortalError):
        p.register(7,e)


def test_TC09_single_use(p):
    e = approved(p)
    token = p.token(p.ticket(5,p.register(5,e)))
    assert p.checkin(6,e,token) == 5
    with pytest.raises(PortalError,match='already been used'):
        p.checkin(6,e,token)


def test_TC10_tampering_wrong_event_and_expiry(p):
    e, other = approved(p), approved(p)
    token = p.token(p.ticket(5,p.register(5,e)))
    with pytest.raises(PortalError):
        p.checkin(6,e,token[:-1] + ('0' if token[-1]!='0' else '1'))
    with pytest.raises(PortalError):
        p.checkin(6,other,token)
    with p.db(True) as con:
        con.execute('UPDATE events SET event_date=? WHERE id=?', ((date.today()-timedelta(days=1)).isoformat(),e))
    with pytest.raises(PortalError,match='expired'):
        p.checkin(6,e,token)


def test_TC11_permissions_and_ownership(p):
    e = draft(p)
    with pytest.raises(PortalError):
        p.submit(8,e)
    with pytest.raises(PortalError):
        p.details(8,e)
    with pytest.raises(PortalError):
        p.create_event(5,'Test',date.today().isoformat(),'Hall',2,[('Food','20')])
    e = approved(p)
    t = p.register(5,e)
    with pytest.raises(PortalError):
        p.ticket(7,t)
    with pytest.raises(PortalError):
        p.checkin(5,e,p.token(p.ticket(5,t)))


def test_TC12_concurrent_scan_accepts_once(p):
    e = approved(p)
    token = p.token(p.ticket(5,p.register(5,e)))
    def scan(_):
        try:
            p.checkin(6,e,token)
            return True
        except PortalError:
            return False
    with ThreadPoolExecutor(max_workers=8) as pool:
        assert sum(pool.map(scan,range(8))) == 1


def test_TC13_concurrent_budget_requests(p):
    events = [draft(p,'7000'),draft(p,'7000')]
    def submit(e):
        try:
            p.submit(1,e)
            return True
        except PortalError:
            return False
    with ThreadPoolExecutor(max_workers=2) as pool:
        assert sum(pool.map(submit,events)) == 1
    assert p.dashboard(1)[1] == 300000


def test_TC14_live_status_api(app,p):
    client = app.test_client()
    sign_in(client,1)
    e = draft(p)
    assert client.get('/api/status').json['events'][0]['status'] == 'Draft'
    p.submit(1,e)
    assert client.get('/api/status').json['events'][0]['status'] == 'Faculty pending'


def test_TC15_login_csrf_logout_and_access(app):
    c = app.test_client()
    assert c.get('/').status_code == 302
    assert c.post('/login',data={'username':'lead','password':'test-pass'}).status_code == 400
    c.get('/login')
    with c.session_transaction() as s:
        csrf = s['csrf']
    assert c.post('/login',data={'csrf':csrf,'username':'lead','password':'wrong'}).status_code == 200
    assert c.post('/login',data={'csrf':csrf,'username':'lead','password':'test-pass'}).status_code == 302
    assert b'Club allocation available' in c.get('/').data
    with c.session_transaction() as s:
        csrf = s['csrf']
    c.post('/logout',data={'csrf':csrf})
    assert c.get('/').status_code == 302


def test_TC16_web_end_to_end_and_qr(app,p):
    c = app.test_client()
    sign_in(c,1)
    result = c.post('/events/new',data={'csrf':'form-test-token','name':'Web workshop','event_date':(date.today()+timedelta(days=7)).isoformat(),'venue':'Hall','capacity':'20','budget_items':'Food | 500\nEquipment | 250'},follow_redirects=True)
    assert result.status_code == 200 and b'750.00' in result.data
    e = p.dashboard(1)[0][0]['id']
    c.post(f'/events/{e}/submit',data={'csrf':'form-test-token'})
    for actor in (2,3,4):
        sign_in(c,actor)
        c.post(f'/events/{e}/review',data={'csrf':'form-test-token','decision':'approve'})
    sign_in(c,5)
    result = c.post(f'/events/{e}/register',data={'csrf':'form-test-token'})
    assert result.status_code == 302
    ticket_url = result.headers['Location']
    assert b'Your event ticket' in c.get(ticket_url).data
    qr = c.get(ticket_url+'.svg')
    assert qr.status_code == 200 and b'<svg' in qr.data
    sign_in(c,7)
    assert c.get(ticket_url).status_code == 404
    sign_in(c,6)
    token = p.token(p.ticket(5,ticket_url.rsplit('/',1)[1]))
    data = {'csrf':'form-test-token','event_id':e,'token':token}
    assert b'Entry accepted' in c.post('/checkin',data=data).data
    assert b'already been used' in c.post('/checkin',data=data).data


def test_TC17_malformed_non_ascii_ticket(p):
    e = approved(p)
    with pytest.raises(PortalError):
        p.checkin(6,e,'fake:1:5:'+'é'*64)


def test_TC18_concurrent_last_seat(p):
    e = approved(p,capacity=1)
    def register(actor):
        try:
            p.register(actor,e)
            return True
        except PortalError:
            return False
    with ThreadPoolExecutor(max_workers=2) as pool:
        assert sum(pool.map(register,[5,7])) == 1


def test_TC19_edit_draft_and_lock_after_submission(app,p):
    c=app.test_client()
    sign_in(c,1)
    e=draft(p)
    assert b'Equipment | 1000.00' in c.get(f'/events/{e}/edit').data
    data={'csrf':'form-test-token','name':'Updated event','event_date':date.today().isoformat(),'venue':'Room 2','capacity':'10','budget_items':'Materials | 300'}
    assert c.post(f'/events/{e}/edit',data=data).status_code==302
    assert p.details(1,e)['budget']==30000
    p.submit(1,e)
    assert c.get(f'/events/{e}/edit').status_code==403


def test_TC20_escape_html_and_reject_sql_login(app,p):
    c=app.test_client()
    sign_in(c,1)
    e=p.create_event(1,'<script>alert(1)</script>',date.today().isoformat(),'Hall',1,[('Food','100')])
    html=c.get(f'/events/{e}').data
    assert b'&lt;script&gt;' in html and b'<script>alert(1)</script>' not in html
    c.post('/logout',data={'csrf':'form-test-token'})
    c.get('/login')
    with c.session_transaction() as s:
        csrf=s['csrf']
    c.post('/login',data={'csrf':csrf,'username':"' OR 1=1 --",'password':'x'})
    assert c.get('/').status_code==302
