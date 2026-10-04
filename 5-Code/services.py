import hashlib
import hmac
import secrets
import sqlite3
from contextlib import contextmanager
from datetime import date
from decimal import Decimal, InvalidOperation
from pathlib import Path


class PortalError(ValueError):
    pass


class Portal:
    stages = {
        'Faculty pending': ('coordinator', 'Finance pending'),
        'Finance pending': ('finance', 'Dean pending'),
        'Dean pending': ('dean', 'Approved'),
    }

    def __init__(self, path, secret):
        self.path = str(path)
        self.secret = secret.encode() if isinstance(secret, str) else secret

    @contextmanager
    def db(self, write=False):
        con = sqlite3.connect(self.path, timeout=15)
        con.row_factory = sqlite3.Row
        con.execute('PRAGMA foreign_keys=ON')
        try:
            if write:
                con.execute('BEGIN IMMEDIATE')
            yield con
            con.commit()
        except Exception:
            con.rollback()
            raise
        finally:
            con.close()

    def init(self):
        with self.db() as con:
            con.execute('PRAGMA journal_mode=WAL')
            con.executescript(Path(__file__).with_name('schema.sql').read_text())

    @staticmethod
    def money(value):
        try:
            value = Decimal(str(value))
            if not value.is_finite() or value <= 0 or value > 10000000:
                raise PortalError('Enter a positive amount up to Rs 1,00,00,000.')
            if value * 100 != (value * 100).to_integral_value():
                raise PortalError('Use at most two decimal places for amounts.')
            return int(value * 100)
        except (InvalidOperation, TypeError):
            raise PortalError('Enter a valid amount.')

    @staticmethod
    def actor(con, actor_id, role=None):
        user = con.execute('SELECT * FROM users WHERE id=?', (actor_id,)).fetchone()
        if user is None or (role and user['role'] != role):
            raise PortalError('This action is not allowed for your account.')
        return user

    @staticmethod
    def event(con, event_id):
        row = con.execute('SELECT * FROM events WHERE id=?', (event_id,)).fetchone()
        if row is None:
            raise PortalError('Event not found.')
        return row

    @staticmethod
    def available(con, club_id):
        club = con.execute('SELECT allocation FROM clubs WHERE id=?', (club_id,)).fetchone()
        reserved = con.execute("SELECT COALESCE(SUM(budget),0) FROM events WHERE club_id=? AND status NOT IN ('Draft','Rejected')", (club_id,)).fetchone()[0]
        return club['allocation'] - reserved

    def create_event(self, actor_id, name, event_date, venue, capacity, items, event_id=None):
        name, venue = name.strip(), venue.strip()
        if not name or not venue or len(name) > 120 or len(venue) > 120:
            raise PortalError('Enter an event name and venue, each within 120 characters.')
        try:
            parsed_date = date.fromisoformat(event_date)
            if parsed_date < date.today():
                raise ValueError()
            if not str(capacity).isdigit() or not 1 <= int(capacity) <= 10000:
                raise ValueError()
        except (ValueError, TypeError):
            raise PortalError('Use today or a future date and a capacity from 1 to 10000.')
        if not items or len(items) > 30:
            raise PortalError('Enter between 1 and 30 budget items.')
        clean = []
        for description, amount in items:
            if not description.strip() or len(description.strip()) > 120:
                raise PortalError('Each budget item needs a description within 120 characters.')
            clean.append((description.strip(), self.money(amount)))
        total = sum(amount for _, amount in clean)
        if total > 1000000000:
            raise PortalError('The total budget is too large.')
        with self.db(True) as con:
            user = self.actor(con, actor_id, 'lead')
            if user['club_id'] is None:
                raise PortalError('Your account has no club assigned.')
            if event_id is None:
                event_id = con.execute('INSERT INTO events(club_id,lead_id,name,event_date,venue,capacity,budget) VALUES(?,?,?,?,?,?,?)',
                                       (user['club_id'], actor_id, name, parsed_date.isoformat(), venue, int(capacity), total)).lastrowid
            else:
                old = self.event(con, event_id)
                if old['lead_id'] != actor_id or old['status'] != 'Draft':
                    raise PortalError('Only your own draft can be edited.')
                con.execute('UPDATE events SET name=?, event_date=?, venue=?, capacity=?, budget=? WHERE id=?', (name, parsed_date.isoformat(), venue, int(capacity), total, event_id))
                con.execute('DELETE FROM budget_items WHERE event_id=?', (event_id,))
            con.executemany('INSERT INTO budget_items(event_id,description,amount) VALUES(?,?,?)', [(event_id, d, a) for d, a in clean])
            return event_id

    def submit(self, actor_id, event_id):
        with self.db(True) as con:
            self.actor(con, actor_id, 'lead')
            event = self.event(con, event_id)
            if event['lead_id'] != actor_id or event['status'] != 'Draft':
                raise PortalError('Only your own draft can be submitted.')
            if event['event_date'] < date.today().isoformat():
                raise PortalError('The event date has passed.')
            remaining = self.available(con, event['club_id'])
            if event['budget'] > remaining:
                raise PortalError(f'Request exceeds the remaining allocation of Rs {remaining / 100:.2f}.')
            con.execute("UPDATE events SET status='Faculty pending' WHERE id=?", (event_id,))

    def review(self, actor_id, event_id, decision, reason=''):
        if decision not in ('approve', 'reject'):
            raise PortalError('Choose approve or reject.')
        reason = reason.strip()
        if len(reason) > 500 or (decision == 'reject' and not reason):
            raise PortalError('Rejection needs a reason. Keep comments within 500 characters.')
        with self.db(True) as con:
            user = self.actor(con, actor_id)
            event = self.event(con, event_id)
            required = self.stages.get(event['status'])
            if required is None or user['role'] != required[0]:
                raise PortalError('This request is not waiting for your approval stage.')
            if event['event_date'] < date.today().isoformat():
                raise PortalError('The event date has passed.')
            con.execute('INSERT INTO approvals(event_id,actor_id,stage,decision,reason) VALUES(?,?,?,?,?)',
                        (event_id, actor_id, event['status'], decision, reason))
            status = 'Rejected' if decision == 'reject' else required[1]
            con.execute('UPDATE events SET status=? WHERE id=?', (status, event_id))

    def register(self, actor_id, event_id):
        with self.db(True) as con:
            self.actor(con, actor_id, 'student')
            event = self.event(con, event_id)
            if event['status'] != 'Approved' or event['event_date'] < date.today().isoformat():
                raise PortalError('Registration is only open for approved, unexpired events.')
            existing = con.execute('SELECT id FROM tickets WHERE event_id=? AND attendee_id=?', (event_id, actor_id)).fetchone()
            if existing:
                return existing['id']
            count = con.execute('SELECT COUNT(*) FROM tickets WHERE event_id=?', (event_id,)).fetchone()[0]
            if count >= event['capacity']:
                raise PortalError('This event is full.')
            ticket_id = secrets.token_hex(16)
            con.execute('INSERT INTO tickets(id,event_id,attendee_id) VALUES(?,?,?)', (ticket_id, event_id, actor_id))
            return ticket_id

    def token(self, ticket):
        payload = f"{ticket['id']}:{ticket['event_id']}:{ticket['attendee_id']}"
        signature = hmac.new(self.secret, payload.encode(), hashlib.sha256).hexdigest()
        return payload + ':' + signature

    def ticket(self, actor_id, ticket_id):
        with self.db() as con:
            self.actor(con, actor_id, 'student')
            ticket = con.execute('SELECT t.*, e.name, e.event_date, e.venue FROM tickets t JOIN events e ON e.id=t.event_id WHERE t.id=? AND t.attendee_id=?', (ticket_id, actor_id)).fetchone()
            if ticket is None:
                raise PortalError('Ticket not found for your account.')
            return dict(ticket)

    def checkin(self, actor_id, event_id, token):
        if not isinstance(token, str) or len(token) > 200:
            raise PortalError('Invalid ticket.')
        parts = token.strip().split(':')
        if len(parts) != 4:
            raise PortalError('Invalid ticket.')
        payload, signature = ':'.join(parts[:3]), parts[3]
        expected = hmac.new(self.secret, payload.encode(), hashlib.sha256).hexdigest()
        if not hmac.compare_digest(signature, expected):
            raise PortalError('Invalid ticket signature.')
        with self.db(True) as con:
            self.actor(con, actor_id, 'checkin')
            event = self.event(con, event_id)
            if event['status'] != 'Approved' or event['event_date'] < date.today().isoformat():
                raise PortalError('Event is not approved or the ticket has expired.')
            row = con.execute('SELECT * FROM tickets WHERE id=? AND event_id=?', (parts[0], event_id)).fetchone()
            if row is None or str(row['event_id']) != parts[1] or str(row['attendee_id']) != parts[2]:
                raise PortalError('Ticket does not belong to this event or attendee.')
            changed = con.execute('UPDATE tickets SET used_at=CURRENT_TIMESTAMP WHERE id=? AND used_at IS NULL', (row['id'],)).rowcount
            if changed != 1:
                raise PortalError('Ticket has already been used.')
            return row['attendee_id']

    def dashboard(self, actor_id):
        with self.db() as con:
            user = self.actor(con, actor_id)
            where, args = '', ()
            if user['role'] == 'lead':
                where, args = 'WHERE e.lead_id=?', (actor_id,)
            elif user['role'] in ('student', 'checkin'):
                where = "WHERE e.status='Approved'"
            rows = con.execute('SELECT e.*, (SELECT COUNT(*) FROM tickets t WHERE t.event_id=e.id) registrations FROM events e ' + where + ' ORDER BY e.id DESC', args).fetchall()
            available = self.available(con, user['club_id']) if user['club_id'] else None
            return [dict(row) for row in rows], available

    def details(self, actor_id, event_id):
        events, _ = self.dashboard(actor_id)
        event = next((e for e in events if e['id'] == event_id), None)
        if event is None:
            raise PortalError('You cannot view this event.')
        with self.db() as con:
            event['items'] = [dict(r) for r in con.execute('SELECT * FROM budget_items WHERE event_id=?', (event_id,))]
            event['approvals'] = [dict(r) for r in con.execute('SELECT a.*, u.username FROM approvals a JOIN users u ON u.id=a.actor_id WHERE event_id=? ORDER BY a.id', (event_id,))]
        return event
