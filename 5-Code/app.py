import io
import os
import secrets
from functools import wraps
from pathlib import Path

import click
import qrcode
import qrcode.image.svg
from flask import Flask, abort, flash, g, jsonify, redirect, render_template, request, send_file, session, url_for
from werkzeug.security import check_password_hash, generate_password_hash

from services import Portal, PortalError


def create_app(config=None):
    app = Flask(__name__, instance_relative_config=True)
    Path(app.instance_path).mkdir(parents=True, exist_ok=True)
    secret_path = Path(app.instance_path) / 'secret.key'
    secret = os.environ.get('PORTAL_SECRET')
    if not secret:
        if not secret_path.exists():
            secret_path.write_text(secrets.token_hex(32))
        secret = secret_path.read_text().strip()
    app.config.update(SECRET_KEY=secret, DATABASE=str(Path(app.instance_path) / 'portal.sqlite3'),
                      SESSION_COOKIE_HTTPONLY=True, SESSION_COOKIE_SAMESITE='Lax', MAX_CONTENT_LENGTH=16384)
    if config:
        app.config.update(config)
    portal = Portal(app.config['DATABASE'], app.config['SECRET_KEY'])
    portal.init()
    app.extensions['portal'] = portal

    @app.template_filter('rupees')
    def rupees(value):
        return f'{value / 100:,.2f}'

    @app.before_request
    def load_user():
        g.user = None
        if session.get('user_id'):
            with portal.db() as con:
                g.user = con.execute('SELECT id,username,role,club_id FROM users WHERE id=?', (session['user_id'],)).fetchone()
        session.setdefault('csrf', secrets.token_hex(24))
        if request.method == 'POST':
            supplied = request.form.get('csrf', '')
            if not supplied or not secrets.compare_digest(supplied.encode(), session['csrf'].encode()):
                abort(400, 'The form expired. Refresh the page and try again.')

    @app.after_request
    def security_headers(response):
        response.headers['Cache-Control'] = 'no-store'
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-Frame-Options'] = 'DENY'
        response.headers['Content-Security-Policy'] = "default-src 'self'; img-src 'self'; style-src 'self'; script-src 'self'; form-action 'self'; frame-ancestors 'none'"
        return response

    def login_required(fn):
        @wraps(fn)
        def wrapped(*args, **kwargs):
            if g.user is None:
                return redirect(url_for('login'))
            return fn(*args, **kwargs)
        return wrapped

    @app.route('/login', methods=['GET', 'POST'])
    def login():
        if request.method == 'POST':
            with portal.db() as con:
                user = con.execute('SELECT * FROM users WHERE username=?', (request.form.get('username', '').strip(),)).fetchone()
            if user and check_password_hash(user['password_hash'], request.form.get('password', '')):
                session.clear()
                session['user_id'] = user['id']
                session['csrf'] = secrets.token_hex(24)
                return redirect(url_for('dashboard'))
            flash('Incorrect username or password.')
        return render_template('login.html')

    @app.post('/logout')
    def logout():
        session.clear()
        return redirect(url_for('login'))

    @app.get('/')
    @login_required
    def dashboard():
        events, available = portal.dashboard(g.user['id'])
        return render_template('dashboard.html', events=events, available=available)

    @app.get('/api/status')
    @login_required
    def status():
        events, available = portal.dashboard(g.user['id'])
        return jsonify(events=[{'id': e['id'], 'status': e['status'], 'registrations': e['registrations']} for e in events], available=available)

    @app.route('/events/new', methods=['GET', 'POST'])
    @app.route('/events/<int:event_id>/edit', methods=['GET', 'POST'])
    @login_required
    def new_event(event_id=None):
        if g.user['role'] != 'lead':
            abort(403)
        values = {}
        if event_id is not None:
            try:
                values = portal.details(g.user['id'], event_id)
                if values['status'] != 'Draft':
                    abort(403)
                values['budget_items'] = '\n'.join(f"{i['description']} | {i['amount']/100:.2f}" for i in values['items'])
            except PortalError:
                abort(404)
        if request.method == 'POST':
            try:
                items = []
                for line in request.form.get('budget_items', '').splitlines():
                    if line.strip():
                        description, sep, amount = line.rpartition('|')
                        if not sep:
                            raise PortalError('Write each budget item as description | amount.')
                        items.append((description, amount.strip()))
                event_id = portal.create_event(g.user['id'], request.form.get('name', ''), request.form.get('event_date', ''), request.form.get('venue', ''), request.form.get('capacity', ''), items, event_id)
                flash('Proposal saved. Check the details and submit the budget request.')
                return redirect(url_for('event', event_id=event_id))
            except PortalError as error:
                flash(str(error))
        return render_template('new_event.html', values=request.form if request.method == 'POST' else values)

    @app.get('/events/<int:event_id>')
    @login_required
    def event(event_id):
        try:
            details = portal.details(g.user['id'], event_id)
        except PortalError:
            abort(404)
        return render_template('event.html', event=details, stages=portal.stages)

    @app.post('/events/<int:event_id>/submit')
    @login_required
    def submit(event_id):
        try:
            portal.submit(g.user['id'], event_id)
            flash('Budget request sent to the Faculty Coordinator.')
        except PortalError as error:
            flash(str(error))
        return redirect(url_for('event', event_id=event_id))

    @app.post('/events/<int:event_id>/review')
    @login_required
    def review(event_id):
        try:
            portal.review(g.user['id'], event_id, request.form.get('decision'), request.form.get('reason', ''))
            flash('Decision recorded with your account and the current time.')
        except PortalError as error:
            flash(str(error))
        return redirect(url_for('event', event_id=event_id))

    @app.post('/events/<int:event_id>/register')
    @login_required
    def register(event_id):
        try:
            ticket_id = portal.register(g.user['id'], event_id)
            return redirect(url_for('ticket', ticket_id=ticket_id))
        except PortalError as error:
            flash(str(error))
            return redirect(url_for('event', event_id=event_id))

    @app.get('/tickets/<ticket_id>')
    @login_required
    def ticket(ticket_id):
        try:
            row = portal.ticket(g.user['id'], ticket_id)
        except PortalError:
            abort(404)
        return render_template('ticket.html', ticket=row, token=portal.token(row))

    @app.get('/tickets/<ticket_id>.svg')
    @login_required
    def ticket_svg(ticket_id):
        try:
            row = portal.ticket(g.user['id'], ticket_id)
        except PortalError:
            abort(404)
        output = io.BytesIO()
        qrcode.make(portal.token(row), image_factory=qrcode.image.svg.SvgPathImage).save(output)
        output.seek(0)
        return send_file(output, mimetype='image/svg+xml')

    @app.route('/checkin', methods=['GET', 'POST'])
    @login_required
    def checkin():
        if g.user['role'] != 'checkin':
            abort(403)
        result, accepted = None, False
        if request.method == 'POST':
            try:
                attendee = portal.checkin(g.user['id'], int(request.form.get('event_id', '0')), request.form.get('token', ''))
                result, accepted = f'Entry accepted for attendee {attendee}.', True
            except (PortalError, ValueError) as error:
                result = str(error)
        events, _ = portal.dashboard(g.user['id'])
        return render_template('checkin.html', events=events, result=result, accepted=accepted)

    @app.cli.command('seed-demo')
    def seed_demo():
        with portal.db(True) as con:
            if con.execute('SELECT COUNT(*) FROM users').fetchone()[0]:
                raise click.ClickException('Database already has users; nothing was changed.')
            con.execute("INSERT INTO clubs(id,name,allocation) VALUES(1,'Student Technical Club',10000000)")
            for name, role, club in [('lead','lead',1), ('faculty','coordinator',None), ('finance','finance',None), ('dean','dean',None), ('student','student',None), ('student2','student',None), ('gate','checkin',None)]:
                con.execute('INSERT INTO users(username,password_hash,role,club_id) VALUES(?,?,?,?)', (name, generate_password_hash('club-demo-2026'), role, club))
        click.echo('Local demo accounts created. Password: club-demo-2026. Do not expose this demo on a public server.')

    return app


if __name__ == '__main__':
    create_app().run(host='127.0.0.1', port=5000, debug=False)
