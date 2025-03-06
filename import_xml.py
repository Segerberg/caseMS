#!/usr/bin/env python3
"""
XML Case Importer for Case Management System

This script imports case data from XML files into the case management database.
Usage: python import_xml.py <file1.xml> [file2.xml] [file3.xml] ...
"""

import sys
import os
import argparse
import xml.etree.ElementTree as ET
import sqlite3
import datetime
from typing import List, Dict, Any, Optional


def get_db_connection() -> sqlite3.Connection:
    """Connect to the SQLite database."""
    conn = sqlite3.connect('case_management.db')
    conn.row_factory = sqlite3.Row
    return conn


def parse_xml_file(file_path: str) -> Dict[str, Any]:
    """
    Parse an XML file and extract case information.

    Args:
        file_path: Path to the XML file

    Returns:
        Dictionary containing case data
    """
    try:
        tree = ET.parse(file_path)
        root = tree.getroot()

        # Find the first AErende (case) element
        ns = {'xsi': 'http://www.w3.org/2001/XMLSchema-instance'}
        case_element = root.find('.//AErende')

        if case_element is None:
            print(f"No case found in {file_path}")
            return {}

        # Extract case data
        case_data = {
            'dnr': int(case_element.findtext('Diarienummer', '0')),
            'in_ut': map_direction(case_element.findtext('Riktning', '')),
            'atext': case_element.findtext('AErendemening', ''),
            'stat': map_status(case_element.findtext('Status', '')),
            'inkupp': parse_date(case_element.findtext('Inkomst_uppraettat_datum', '')),
            'regdat': parse_date(case_element.findtext('Registreringsdatum', '')),
            'avsdat': parse_date(case_element.findtext('Avslutsdatum', '')),
            'motpart_bet': case_element.findtext('Motpartens_beteckning', ''),
            'fran_till': case_element.findtext('Fraan_till', ''),

            # These will need lookup or creation
            'reg_id': None,  # Will be set based on registrator
            'doss_nr': None,  # Will be extracted from Diarieplan/Dossiernummer
            'hand_id': None,  # Will be set based on handlaeggare name
            'enht_kod': None,  # Will be set based on Enhet ID

            # Additional data for lookups
            'registrator': case_element.findtext('Registrator', ''),
            'handlaeggare': case_element.findtext('Handlaeggare', ''),
            'enhet_name': None,
            'dossier_name': None,
        }

        # Extract dossier information
        diarieplan = case_element.find('Diarieplan')
        if diarieplan is not None:
            case_data['doss_nr'] = int(diarieplan.findtext('Dossiernummer', '0'))
            case_data['dossier_name'] = diarieplan.findtext('Rubrik', '')

        # Extract unit information
        enhet = case_element.find('Enhet')
        if enhet is not None:
            case_data['enht_kod'] = enhet.get('ID', '')
            case_data['enhet_name'] = enhet.text

        # Extract notes (händelser)
        notes = []
        for idx, haendelse in enumerate(case_element.findall('.//Haendelse')):
            note = {
                'dnr': case_data['dnr'],
                'lnr': int(haendelse.findtext('Loepnummer', str(idx + 1))),
                'in_ut': map_direction(haendelse.findtext('Riktning', '')),
                'ant_text': haendelse.findtext('Haendelsetext', ''),
                'reg_id': None,  # Will be set based on registrator
                'datumin': parse_date(haendelse.findtext('Inkommandedatum', '')),
                'datumut': parse_date(haendelse.findtext('Utgaaendedatum', '')),
                'anmkal': '',  # Not in XML
                'hand_id': None,  # Will be set based on handlaeggare
                'avsmot': haendelse.findtext('Motpart', ''),

                # Additional data for lookups
                'registrator': haendelse.findtext('Registrator', ''),
                'handlaeggare': haendelse.findtext('Handlaeggare', ''),
            }
            notes.append(note)

        # Extract logs
        logs = []
        for logg in case_element.findall('.//Logg'):
            log = {
                'dnr': case_data['dnr'],
                'reg_id': None,  # Will be set based on registrator
                'logdat': parse_datetime(logg.findtext('AEndringsdatum', '')),
                'logflt': f"Ändring av {logg.findtext('Faeltnamn', '')}",

                # Additional data for lookups
                'registrator': logg.findtext('Registrator', ''),
            }
            logs.append(log)

        return {
            'case': case_data,
            'notes': notes,
            'logs': logs
        }

    except Exception as e:
        print(f"Error parsing {file_path}: {str(e)}")
        return {}


def map_direction(direction: str) -> str:
    """Map XML direction values to database values."""
    direction_map = {
        'I': 'IN',
        'U': 'UT',
        '': 'INTERN'
    }
    return direction_map.get(direction, 'INTERN')


def map_status(status: str) -> str:
    """Map XML status values to database values."""
    status_map = {
        'Ö': 'Pågående',
        'A': 'Avslutad',
        '': 'Ny'
    }
    return status_map.get(status, 'Ny')


def parse_date(date_str: str) -> Optional[str]:
    """Parse date string to database format YYYY-MM-DD."""
    if not date_str:
        return None

    try:
        # Try to parse YYYY-MM-DD format
        return date_str
    except:
        # If that fails, return None
        return None


def parse_datetime(datetime_str: str) -> Optional[str]:
    """Parse datetime string to date format YYYY-MM-DD."""
    if not datetime_str:
        return None

    try:
        # Extract just the date part from YYYY-MM-DDThh:mm:ss
        return datetime_str.split('T')[0]
    except:
        return None


def get_or_create_registry(conn: sqlite3.Connection, registrator: str) -> str:
    """Get or create registry ID for the registrator."""
    cur = conn.cursor()

    # Check if we have a registry for this registrator
    cur.execute("SELECT REG_ID FROM REG WHERE REG_NAMN LIKE ?", (f"%{registrator}%",))
    result = cur.fetchone()

    if result:
        return result[0]

    # Create a new registry
    reg_id = f"R{str(registrator).upper()[0:3]}"

    # Check if the reg_id already exists
    cur.execute("SELECT COUNT(*) FROM REG WHERE REG_ID = ?", (reg_id,))
    count = cur.fetchone()[0]

    if count > 0:
        # Find an available ID by adding a number
        for i in range(1, 100):
            new_reg_id = f"{reg_id}{i}"
            cur.execute("SELECT COUNT(*) FROM REG WHERE REG_ID = ?", (new_reg_id,))
            if cur.fetchone()[0] == 0:
                reg_id = new_reg_id
                break

    # Insert the new registry
    cur.execute("INSERT INTO REG (REG_ID, REG_NAMN) VALUES (?, ?)",
                (reg_id, f"{registrator}"))
    conn.commit()

    return reg_id


def get_or_create_dossier(conn: sqlite3.Connection, doss_nr: int, name: Optional[str]) -> int:
    """Get or create dossier with the given number."""
    if not doss_nr:
        return None

    cur = conn.cursor()

    # Check if dossier exists
    cur.execute("SELECT COUNT(*) FROM DOSSIEPLAN WHERE DOSS_NR = ?", (doss_nr,))
    count = cur.fetchone()[0]

    if count == 0 and name:
        # Create new dossier
        cur.execute("INSERT INTO DOSSIEPLAN (DOSS_NR, NAMN) VALUES (?, ?)",
                    (doss_nr, name))
        conn.commit()

    return doss_nr


def get_or_create_handler(conn: sqlite3.Connection, handler_name: str) -> Optional[str]:
    """Get or create handler with the given name."""
    if not handler_name:
        return None

    cur = conn.cursor()

    # Check if handler exists (exact match or similar)
    cur.execute("SELECT HAND_ID FROM HANDLAEGGARE WHERE HAND_NAMN = ? OR HAND_NAMN LIKE ?",
                (handler_name, f"%{handler_name}%"))
    result = cur.fetchone()

    if result:
        return result[0]

    # Create a new handler
    hand_id = f"H{len(handler_name.split()[-1])}{len(handler_name.split()[0])}"

    # Check if the hand_id already exists
    cur.execute("SELECT COUNT(*) FROM HANDLAEGGARE WHERE HAND_ID = ?", (hand_id,))
    count = cur.fetchone()[0]

    if count > 0:
        # Find an available ID by adding a number
        for i in range(1, 100):
            new_hand_id = f"{hand_id}{i}"
            cur.execute("SELECT COUNT(*) FROM HANDLAEGGARE WHERE HAND_ID = ?", (new_hand_id,))
            if cur.fetchone()[0] == 0:
                hand_id = new_hand_id
                break

    # Insert the new handler
    cur.execute("INSERT INTO HANDLAEGGARE (HAND_ID, HAND_NAMN) VALUES (?, ?)",
                (hand_id, handler_name))
    conn.commit()

    return hand_id


def get_or_create_unit(conn: sqlite3.Connection, unit_code: str, unit_name: Optional[str]) -> Optional[str]:
    """Get or create unit with the given code."""
    if not unit_code:
        return None

    cur = conn.cursor()

    # Check if unit exists
    cur.execute("SELECT COUNT(*) FROM ENHET WHERE ENHT_KOD = ?", (unit_code,))
    count = cur.fetchone()[0]

    if count == 0 and unit_name:
        # Create new unit
        cur.execute("INSERT INTO ENHET (ENHT_KOD, ENHT_NAMN) VALUES (?, ?)",
                    (unit_code, unit_name))
        conn.commit()

    return unit_code


def import_case(conn: sqlite3.Connection, case_data: Dict[str, Any]) -> bool:
    """Import a case into the database."""
    # Extract data
    case = case_data.get('case', {})
    notes = case_data.get('notes', [])
    logs = case_data.get('logs', [])

    if not case:
        return False

    try:
        cur = conn.cursor()

        # Get or create related entities
        reg_id = get_or_create_registry(conn, case['registrator'])
        doss_nr = get_or_create_dossier(conn, case.get('doss_nr'), case.get('dossier_name'))
        hand_id = get_or_create_handler(conn, case.get('handlaeggare'))
        enht_kod = get_or_create_unit(conn, case.get('enht_kod'), case.get('enhet_name'))

        # Update case with related entity IDs
        case['reg_id'] = reg_id
        case['doss_nr'] = doss_nr
        case['hand_id'] = hand_id
        case['enht_kod'] = enht_kod

        # Check if case already exists
        cur.execute("SELECT COUNT(*) FROM AERENDE WHERE DNR = ?", (case['dnr'],))
        case_exists = cur.fetchone()[0] > 0

        if case_exists:
            print(f"Case {case['dnr']} already exists in the database.")
            return False

        # Insert case
        cur.execute("""
            INSERT INTO AERENDE (
                DNR, REG_ID, IN_UT, DOSS_NR, HAND_ID, ENHT_KOD,
                INKUPP, REGDAT, AVSDAT, STAT, ATEXT,
                MOTPART_BET, FRAN_TILL
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            case['dnr'], case['reg_id'], case['in_ut'], case['doss_nr'],
            case['hand_id'], case['enht_kod'], case['inkupp'], case['regdat'],
            case['avsdat'], case['stat'], case['atext'],
            case['motpart_bet'], case['fran_till']
        ))

        # Import notes
        for note in notes:
            note['reg_id'] = reg_id
            note['hand_id'] = get_or_create_handler(conn, note.get('handlaeggare')) or hand_id

            cur.execute("""
                INSERT INTO AERENDE_ANT (
                    DNR, LNR, IN_UT, ANT_TEXT, REG_ID,
                    DATUMIN, DATUMUT, ANMKAL, HAND_ID, AVSMOT
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                note['dnr'], note['lnr'], note['in_ut'], note['ant_text'],
                note['reg_id'], note['datumin'], note['datumut'],
                note.get('anmkal', ''), note['hand_id'], note.get('avsmot', '')
            ))

        # Import logs
        for log in logs:
            log['reg_id'] = reg_id

            cur.execute("""
                INSERT INTO LOG (DNR, REG_ID, LOGDAT, LOGFLT)
                VALUES (?, ?, ?, ?)
            """, (
                log['dnr'], log['reg_id'], log['logdat'], log['logflt']
            ))

        conn.commit()
        return True

    except Exception as e:
        conn.rollback()
        print(f"Error importing case {case.get('dnr', 'unknown')}: {str(e)}")
        return False


def main():
    parser = argparse.ArgumentParser(description='Import case data from XML files into the database.')
    parser.add_argument('files', metavar='file', type=str, nargs='+',
                        help='XML files to import')
    parser.add_argument('--dry-run', action='store_true',
                        help='Parse XML but do not insert into database')

    args = parser.parse_args()

    if not args.files:
        print("No files specified. Use python import_xml.py <file1.xml> [file2.xml] ...")
        return

    # Connect to database
    conn = get_db_connection() if not args.dry_run else None

    # Process each file
    successful_imports = 0
    for file_path in args.files:
        print(f"Processing {file_path}...")

        if not os.path.isfile(file_path):
            print(f"File not found: {file_path}")
            continue

        case_data = parse_xml_file(file_path)

        if not case_data:
            print(f"No valid case data found in {file_path}")
            continue

        if args.dry_run:
            print(f"Dry run - would import case {case_data.get('case', {}).get('dnr', 'unknown')}")
            successful_imports += 1
        else:
            if import_case(conn, case_data):
                print(f"Successfully imported case {case_data.get('case', {}).get('dnr', 'unknown')}")
                successful_imports += 1
            else:
                print(f"Failed to import {file_path}")

    if conn:
        conn.close()

    print(f"Import completed. Successfully imported {successful_imports} of {len(args.files)} files.")


if __name__ == "__main__":
    main()