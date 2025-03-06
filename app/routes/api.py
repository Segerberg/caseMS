from flask import Blueprint, jsonify, current_app, g
from flask_login import login_required
import sqlite3
import datetime

api_bp = Blueprint('api', __name__, url_prefix='/api')


def get_db():
    if 'db' not in g:
        g.db = sqlite3.connect('case_management.db')
        g.db.row_factory = sqlite3.Row
    return g.db


def execute_query(query, args=(), one=False):
    db = get_db()
    cursor = db.execute(query, args)

    if one:
        result = cursor.fetchone()
        return result and dict(result)  # Convert Row to dict if result exists

    return [dict(row) for row in cursor.fetchall()]  # Convert all rows to dicts


@api_bp.teardown_request
def close_db(exception):
    db = g.pop('db', None)
    if db is not None:
        db.close()


@api_bp.route('/cases', methods=['GET'])
@login_required
def get_cases():
    """API endpoint to get all cases in JSON format"""
    cases = execute_query('''
        SELECT a.DNR, a.REG_ID, a.IN_UT, a.DOSS_NR, a.HAND_ID, a.ENHT_KOD,
               a.REGDAT, a.STAT, a.ATEXT, r.REG_NAMN, h.HAND_NAMN,
               d.NAMN as DOSS_NAMN, e.ENHT_NAMN
        FROM AERENDE a
        LEFT JOIN REG r ON a.REG_ID = r.REG_ID
        LEFT JOIN HANDLAEGGARE h ON a.HAND_ID = h.HAND_ID
        LEFT JOIN DOSSIEPLAN d ON a.DOSS_NR = d.DOSS_NR
        LEFT JOIN ENHET e ON a.ENHT_KOD = e.ENHT_KOD
        ORDER BY a.REGDAT DESC
    ''')

    return jsonify({
        'status': 'success',
        'count': len(cases),
        'cases': cases
    })


@api_bp.route('/case/<int:dnr>', methods=['GET'])
@login_required
def get_case(dnr):
    """API endpoint to get a single case by DNR in JSON format"""
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
        return jsonify({
            'status': 'error',
            'message': f'Case with DNR {dnr} not found'
        }), 404

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

    return jsonify({
        'status': 'success',
        'case': case,
        'notes': notes,
        'logs': logs
    })