from flask import Blueprint, render_template, redirect, url_for, request, flash, current_app, g
from flask_login import login_required, current_user
import sqlite3
import datetime

cases_bp = Blueprint('cases', __name__)


def get_db():
    if 'db' not in g:
        db_path = current_app.config['SQLALCHEMY_DATABASE_URI'].replace('sqlite:///', '')
        g.db = sqlite3.connect(db_path)
        g.db.row_factory = sqlite3.Row
    return g.db


def execute_query(query, args=(), one=False, commit=False):
    db = get_db()
    cursor = db.execute(query, args)

    if commit:
        db.commit()
        return cursor.lastrowid

    if one:
        return cursor.fetchone()

    return cursor.fetchall()


@cases_bp.teardown_request
def close_db(exception):
    db = g.pop('db', None)
    if db is not None:
        db.close()


@cases_bp.route('/')
@login_required
def index():
    # Get all cases with raw SQL
    cases = execute_query('''
        SELECT a.*, r.REG_NAMN, h.HAND_NAMN, d.NAMN as DOSS_NAMN, e.ENHT_NAMN
        FROM AERENDE a
        LEFT JOIN REG r ON a.REG_ID = r.REG_ID
        LEFT JOIN HANDLAEGGARE h ON a.HAND_ID = h.HAND_ID
        LEFT JOIN DOSSIEPLAN d ON a.DOSS_NR = d.DOSS_NR
        LEFT JOIN ENHET e ON a.ENHT_KOD = e.ENHT_KOD
        ORDER BY a.REGDAT DESC
    ''')

    return render_template('cases/index.html', cases=cases)


@cases_bp.route('/case/<int:dnr>')
@login_required
def view_case(dnr):
    # Get case details
    case = execute_query('''
        SELECT a.*, r.REG_NAMN, h.HAND_NAMN, d.NAMN as DOSS_NAMN, e.ENHT_NAMN
        FROM AERENDE a
        LEFT JOIN REG r ON a.REG_ID = r.REG_ID
        LEFT JOIN HANDLAEGGARE h ON a.HAND_ID = h.HAND_ID
        LEFT JOIN DOSSIEPLAN d ON a.DOSS_NR = d.DOSS_NR
        LEFT JOIN ENHET e ON a.ENHT_KOD = e.ENHT_KOD
        WHERE a.DNR = ?
    ''', [dnr], one=True)

    if not case:
        flash('Ärendet hittades inte.', 'danger')
        return redirect(url_for('cases.index'))

    # Get case notes
    notes = execute_query('''
        SELECT n.*, h.HAND_NAMN
        FROM AERENDE_ANT n
        LEFT JOIN HANDLAEGGARE h ON n.HAND_ID = h.HAND_ID
        WHERE n.DNR = ?
        ORDER BY n.DATUMIN DESC, n.LNR DESC
    ''', [dnr])

    # Get log entries
    logs = execute_query('''
        SELECT l.*, r.REG_NAMN
        FROM LOG l
        LEFT JOIN REG r ON l.REG_ID = r.REG_ID
        WHERE l.DNR = ?
        ORDER BY l.LOGDAT DESC
    ''', [dnr])

    return render_template('cases/view.html', case=case, notes=notes, logs=logs)


@cases_bp.route('/case/new', methods=['GET', 'POST'])
@login_required
def new_case():
    # Get data for dropdown lists
    registries = execute_query('SELECT * FROM REG ORDER BY REG_NAMN')
    dossiers = execute_query('SELECT * FROM DOSSIEPLAN ORDER BY NAMN')
    handlers = execute_query('SELECT * FROM HANDLAEGGARE ORDER BY HAND_NAMN')
    units = execute_query('SELECT * FROM ENHET ORDER BY ENHT_NAMN')

    if request.method == 'POST':
        # Get form data
        reg_id = request.form.get('reg_id')
        in_ut = request.form.get('in_ut')
        doss_nr = request.form.get('doss_nr') or None
        hand_id = request.form.get('hand_id') or None
        enht_kod = request.form.get('enht_kod') or None
        inkupp = request.form.get('inkupp') or None
        regdat = request.form.get('regdat') or datetime.date.today().isoformat()
        avsdat = request.form.get('avsdat') or None
        stat = request.form.get('stat')
        atext = request.form.get('atext')
        motpart_bet = request.form.get('motpart_bet')
        fran_till = request.form.get('fran_till')

        try:
            # Insert new case
            dnr = execute_query('''
                INSERT INTO AERENDE (
                    REG_ID, IN_UT, DOSS_NR, HAND_ID, ENHT_KOD, 
                    INKUPP, REGDAT, AVSDAT, STAT, ATEXT, 
                    MOTPART_BET, FRAN_TILL
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', [
                reg_id, in_ut, doss_nr, hand_id, enht_kod,
                inkupp, regdat, avsdat, stat, atext,
                motpart_bet, fran_till
            ], commit=True)

            # Add log entry
            execute_query('''
                INSERT INTO LOG (DNR, REG_ID, LOGDAT, LOGFLT)
                VALUES (?, ?, ?, ?)
            ''', [
                dnr, reg_id, datetime.date.today().isoformat(),
                f'Nytt ärende skapat av {current_user.username}'
            ], commit=True)

            flash('Ärendet har skapats.', 'success')
            return redirect(url_for('cases.view_case', dnr=dnr))

        except Exception as e:
            flash(f'Ett fel inträffade: {str(e)}', 'danger')

    return render_template(
        'cases/create.html',
        registries=registries,
        dossiers=dossiers,
        handlers=handlers,
        units=units,
        today=datetime.date.today().isoformat()
    )


@cases_bp.route('/case/<int:dnr>/edit', methods=['GET', 'POST'])
@login_required
def edit_case(dnr):
    # Get case details
    case = execute_query('SELECT * FROM AERENDE WHERE DNR = ?', [dnr], one=True)

    if not case:
        flash('Ärendet hittades inte.', 'danger')
        return redirect(url_for('cases.index'))

    # Get data for dropdown lists
    registries = execute_query('SELECT * FROM REG ORDER BY REG_NAMN')
    dossiers = execute_query('SELECT * FROM DOSSIEPLAN ORDER BY NAMN')
    handlers = execute_query('SELECT * FROM HANDLAEGGARE ORDER BY HAND_NAMN')
    units = execute_query('SELECT * FROM ENHET ORDER BY ENHT_NAMN')

    if request.method == 'POST':
        # Get form data
        reg_id = request.form.get('reg_id')
        in_ut = request.form.get('in_ut')
        doss_nr = request.form.get('doss_nr') or None
        hand_id = request.form.get('hand_id') or None
        enht_kod = request.form.get('enht_kod') or None
        inkupp = request.form.get('inkupp') or None
        regdat = request.form.get('regdat') or None
        avsdat = request.form.get('avsdat') or None
        stat = request.form.get('stat')
        atext = request.form.get('atext')
        motpart_bet = request.form.get('motpart_bet')
        fran_till = request.form.get('fran_till')

        try:
            # Update the case
            execute_query('''
                UPDATE AERENDE SET
                    REG_ID = ?, IN_UT = ?, DOSS_NR = ?, HAND_ID = ?, ENHT_KOD = ?,
                    INKUPP = ?, REGDAT = ?, AVSDAT = ?, STAT = ?, ATEXT = ?,
                    MOTPART_BET = ?, FRAN_TILL = ?
                WHERE DNR = ?
            ''', [
                reg_id, in_ut, doss_nr, hand_id, enht_kod,
                inkupp, regdat, avsdat, stat, atext,
                motpart_bet, fran_till, dnr
            ], commit=True)

            current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            execute_query('''
                INSERT INTO LOG (DNR, REG_ID, LOGDAT, LOGFLT)
                VALUES (?, ?, ?, ?)
            ''', [
                dnr, reg_id, current_time,
                f'Ärende uppdaterat av {current_user.username}'
            ], commit=True)

            flash('Ärendet har uppdaterats.', 'success')
            return redirect(url_for('cases.view_case', dnr=dnr))

        except Exception as e:
            flash(f'Ett fel inträffade: {str(e)}', 'danger')

    return render_template(
        'cases/edit.html',
        case=case,
        registries=registries,
        dossiers=dossiers,
        handlers=handlers,
        units=units
    )


@cases_bp.route('/case/<int:dnr>/note', methods=['POST'])
@login_required
def add_note(dnr):
    # Check if case exists
    case = execute_query('SELECT * FROM AERENDE WHERE DNR = ?', [dnr], one=True)

    if not case:
        flash('Ärendet hittades inte.', 'danger')
        return redirect(url_for('cases.index'))

    # Get form data
    in_ut = request.form.get('in_ut')
    ant_text = request.form.get('ant_text')
    reg_id = case['REG_ID']
    datumin = datetime.date.today().isoformat()
    hand_id = request.form.get('hand_id') or None
    avsmot = request.form.get('avsmot') or None

    try:
        # Get next LNR (line number) for this case
        last_note = execute_query(
            'SELECT MAX(LNR) as max_lnr FROM AERENDE_ANT WHERE DNR = ?',
            [dnr],
            one=True
        )
        lnr = 1 if not last_note or last_note['max_lnr'] is None else last_note['max_lnr'] + 1

        # Insert note
        execute_query('''
            INSERT INTO AERENDE_ANT (
                DNR, LNR, IN_UT, ANT_TEXT, REG_ID,
                DATUMIN, HAND_ID, AVSMOT
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', [
            dnr, lnr, in_ut, ant_text, reg_id,
            datumin, hand_id, avsmot
        ], commit=True)

        current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        execute_query('''
            INSERT INTO LOG (DNR, REG_ID, LOGDAT, LOGFLT)
            VALUES (?, ?, ?, ?)
        ''', [
            dnr, reg_id, current_time,
            f'Ny anteckning tillagd av {current_user.username}'
        ], commit=True)

        flash('Anteckning har lagts till.', 'success')
    except Exception as e:
        flash(f'Ett fel inträffade: {str(e)}', 'danger')

    return redirect(url_for('cases.view_case', dnr=dnr))