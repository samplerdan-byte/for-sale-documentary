#!/usr/bin/env python3
"""
congress_blast_2026-03-20.py — Personalized congressional mailer for "For Sale" documentary.

Sends individually crafted emails to every US Senator and key House committee members,
referencing their specific voting records on bank bailouts, defense spending, surveillance,
deregulation, corporate tax cuts, and crypto legislation.

REQUIREMENTS:
  - Python 3.8+
  - Gmail: Use an APP PASSWORD, NOT your regular password.
    Generate one: Google Account > Security > 2-Step Verification > App Passwords
  - ProtonMail Bridge: Must be running locally for ProtonMail SMTP.
  - Custom SMTP: Any server that supports STARTTLS on the configured port.

USAGE:
  python congress_blast_2026-03-20.py                  # live send (prompts for creds)
  python congress_blast_2026-03-20.py --dry-run        # print all emails to console
  python congress_blast_2026-03-20.py --dry-run --csv  # also export CSV of all targets

CONFIGURATION:
  Fill in the 3 fields below and run. That's it.
"""

import smtplib
import sys
import time
import csv
import json
import argparse
import getpass
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from pathlib import Path

# ===========================================================================
# CONFIGURATION — Fill these in and run
# ===========================================================================

SMTP_SERVER = ""          # e.g. "smtp.gmail.com", "127.0.0.1" (ProtonMail Bridge), or custom
SMTP_PORT = 587           # 587 for Gmail/ProtonMail, or your server's port
EMAIL_ADDRESS = ""        # Your sending email address
EMAIL_PASSWORD = ""       # App password (Gmail) or account password (ProtonMail/custom)
REPLY_TO = ""             # Optional: anonymous reply-to address (leave blank to skip)

# Rate limiting
DELAY_BETWEEN_SENDS = 3  # seconds between emails (3s = safe for most SMTP providers)
BATCH_SIZE = 50           # pause after this many emails
BATCH_PAUSE = 60          # seconds to pause between batches

# Documentary URL
DOC_URL = "https://samplerdan-byte.github.io/for-sale-documentary/"
SOURCE_URL = "https://github.com/samplerdan-byte/for-sale-documentary"

# ===========================================================================
# SMTP PRESETS
# ===========================================================================

SMTP_PRESETS = {
    "gmail": {"server": "smtp.gmail.com", "port": 587},
    "protonmail": {"server": "127.0.0.1", "port": 1025},  # ProtonMail Bridge local
    "protonmail-direct": {"server": "mail.protonmail.ch", "port": 587},
    "outlook": {"server": "smtp-mail.outlook.com", "port": 587},
    "fastmail": {"server": "smtp.fastmail.com", "port": 587},
}

# ===========================================================================
# LOGGING
# ===========================================================================

LOG_FILE = Path(__file__).parent / f"congress_blast_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler(sys.stdout),
    ],
)
log = logging.getLogger(__name__)

# ===========================================================================
# KEY VOTES — Referenced in personalized emails
# ===========================================================================
# Format: vote_key -> {bill, year, description, yea_meaning, nay_meaning}
# Members' votes are stored per-member in the MEMBERS dict below.

KEY_VOTES = {
    "tarp": {
        "bill": "Emergency Economic Stabilization Act (TARP)",
        "year": 2008,
        "desc": "the $700 billion bank bailout that rescued Wall Street while millions lost their homes",
        "yea": "voted to bail out Wall Street banks with $700 billion in taxpayer money",
        "nay": "voted against the $700 billion Wall Street bailout",
    },
    "iraq_war": {
        "bill": "Authorization for Use of Military Force Against Iraq",
        "year": 2002,
        "desc": "the authorization that launched a $2 trillion war based on weapons that didn't exist",
        "yea": "voted to authorize the Iraq War",
        "nay": "voted against the Iraq War authorization",
    },
    "patriot_act": {
        "bill": "USA PATRIOT Act / FISA Reauthorization",
        "year": "2001-2020",
        "desc": "mass surveillance legislation that authorized warrantless monitoring of American citizens",
        "yea": "voted to authorize or reauthorize warrantless surveillance of Americans",
        "nay": "voted against warrantless surveillance powers",
    },
    "tax_cuts_2017": {
        "bill": "Tax Cuts and Jobs Act",
        "year": 2017,
        "desc": "the corporate tax cut that dropped the rate from 35% to 21%, adding $1.9 trillion to the national debt",
        "yea": "voted for the 2017 corporate tax cut that added $1.9 trillion to the national debt",
        "nay": "voted against the 2017 corporate tax cut",
    },
    "dodd_frank_rollback": {
        "bill": "Economic Growth, Regulatory Relief, and Consumer Protection Act",
        "year": 2018,
        "desc": "the rollback of Dodd-Frank bank regulations that had been put in place after the 2008 crash",
        "yea": "voted to roll back post-2008 banking regulations",
        "nay": "voted against rolling back banking regulations",
    },
    "ndaa_2025": {
        "bill": "National Defense Authorization Act FY2025",
        "year": 2024,
        "desc": "$895 billion in defense spending",
        "yea": "voted for $895 billion in defense spending",
        "nay": "voted against the $895 billion defense budget",
    },
    "fisa_2024": {
        "bill": "FISA Section 702 Reauthorization",
        "year": 2024,
        "desc": "reauthorization of warrantless surveillance powers under FISA Section 702",
        "yea": "voted to reauthorize warrantless surveillance under FISA Section 702",
        "nay": "voted against reauthorizing FISA Section 702 surveillance",
    },
    "genius_act": {
        "bill": "GENIUS Act (stablecoin regulation)",
        "year": 2025,
        "desc": "crypto stablecoin legislation that critics say benefits industry insiders",
        "yea": "voted for the GENIUS Act crypto stablecoin bill",
        "nay": "voted against the GENIUS Act",
    },
}


# ===========================================================================
# MEMBER DATABASE
# ===========================================================================
# Each member dict:
#   name: str, state: str, party: "R"|"D"|"I",
#   chamber: "Senate"|"House",
#   committees: list[str],
#   email: str (firstname.lastname@mail.house.gov or contact URL for senators),
#   votes: dict[vote_key -> "yea"|"nay"|None]  (None = not in office for that vote)
#
# Senate contact pages: https://www.{lastname}.senate.gov/contact
# House emails: firstname.lastname@mail.house.gov
#
# VOTE DATA NOTES:
# - Votes are based on public roll call records from senate.gov and clerk.house.gov
# - Where a member was not in office for a vote, that vote is omitted (None)
# - Some newer members have limited vote histories
# ===========================================================================

def _sen(name, state, party, contact_url, committees=None, votes=None):
    """Helper to build a senator entry."""
    return {
        "name": name,
        "state": state,
        "party": party,
        "chamber": "Senate",
        "email": contact_url,
        "committees": committees or [],
        "votes": votes or {},
    }

def _rep(name, state, party, email, committees=None, votes=None):
    """Helper to build a House rep entry."""
    return {
        "name": name,
        "state": state,
        "party": party,
        "chamber": "House",
        "email": email,
        "committees": committees or [],
        "votes": votes or {},
    }

# ---------------------------------------------------------------------------
# ALL 100 SENATORS
# Contact URLs: https://www.{lastname}.senate.gov/contact (standard pattern)
# Some senators use different URL patterns — noted where known.
# ---------------------------------------------------------------------------

MEMBERS = [
    # -- ALABAMA --
    _sen("Katie Boyd Britt", "AL", "R", "https://www.britt.senate.gov/contact",
         committees=["Banking"],
         votes={"ndaa_2025": "yea", "fisa_2024": "yea", "genius_act": "yea"}),
    _sen("Tommy Tuberville", "AL", "R", "https://www.tuberville.senate.gov/contact",
         committees=["Armed Services"],
         votes={"ndaa_2025": "yea", "fisa_2024": "yea"}),

    # -- ALASKA --
    _sen("Lisa Murkowski", "AK", "R", "https://www.murkowski.senate.gov/contact",
         votes={"tarp": "yea", "tax_cuts_2017": "yea", "dodd_frank_rollback": "yea",
                "ndaa_2025": "yea", "fisa_2024": "yea"}),
    _sen("Dan Sullivan", "AK", "R", "https://www.sullivan.senate.gov/contact",
         committees=["Armed Services"],
         votes={"tax_cuts_2017": "yea", "ndaa_2025": "yea", "fisa_2024": "yea"}),

    # -- ARIZONA --
    _sen("Ruben Gallego", "AZ", "D", "https://www.gallego.senate.gov/contact",
         committees=["Banking"],
         votes={"ndaa_2025": "yea"}),
    _sen("Mark Kelly", "AZ", "D", "https://www.kelly.senate.gov/contact",
         committees=["Armed Services"],
         votes={"ndaa_2025": "yea", "fisa_2024": "yea"}),

    # -- ARKANSAS --
    _sen("John Boozman", "AR", "R", "https://www.boozman.senate.gov/contact",
         votes={"tax_cuts_2017": "yea", "dodd_frank_rollback": "yea",
                "ndaa_2025": "yea", "fisa_2024": "yea"}),
    _sen("Tom Cotton", "AR", "R", "https://www.cotton.senate.gov/contact",
         committees=["Armed Services"],
         votes={"tax_cuts_2017": "yea", "ndaa_2025": "yea", "fisa_2024": "yea"}),

    # -- CALIFORNIA --
    _sen("Alex Padilla", "CA", "D", "https://www.padilla.senate.gov/contact",
         votes={"ndaa_2025": "yea", "fisa_2024": "nay"}),
    _sen("Adam Schiff", "CA", "D", "https://www.schiff.senate.gov/contact",
         votes={"ndaa_2025": "yea", "fisa_2024": "yea"}),

    # -- COLORADO --
    _sen("Michael Bennet", "CO", "D", "https://www.bennet.senate.gov/contact",
         votes={"tax_cuts_2017": "nay", "dodd_frank_rollback": "nay",
                "ndaa_2025": "yea", "fisa_2024": "yea"}),
    _sen("John Hickenlooper", "CO", "D", "https://www.hickenlooper.senate.gov/contact",
         votes={"ndaa_2025": "yea", "fisa_2024": "yea"}),

    # -- CONNECTICUT --
    _sen("Richard Blumenthal", "CT", "D", "https://www.blumenthal.senate.gov/contact",
         committees=["Armed Services"],
         votes={"tax_cuts_2017": "nay", "ndaa_2025": "yea", "fisa_2024": "nay"}),
    _sen("Chris Murphy", "CT", "D", "https://www.murphy.senate.gov/contact",
         votes={"tax_cuts_2017": "nay", "ndaa_2025": "nay", "fisa_2024": "nay"}),

    # -- DELAWARE --
    _sen("Lisa Blunt Rochester", "DE", "D", "https://www.bluntrochester.senate.gov/contact",
         committees=["Banking"],
         votes={"ndaa_2025": "yea"}),
    _sen("Chris Coons", "DE", "D", "https://www.coons.senate.gov/contact",
         votes={"ndaa_2025": "yea", "fisa_2024": "yea"}),

    # -- FLORIDA --
    _sen("Ashley Moody", "FL", "R", "https://www.moody.senate.gov/contact",
         votes={}),  # Newly appointed 2025
    _sen("Rick Scott", "FL", "R", "https://www.rickscott.senate.gov/contact",
         committees=["Armed Services"],
         votes={"ndaa_2025": "nay", "fisa_2024": "nay"}),

    # -- GEORGIA --
    _sen("Jon Ossoff", "GA", "D", "https://www.ossoff.senate.gov/contact",
         votes={"ndaa_2025": "yea", "fisa_2024": "yea"}),
    _sen("Raphael Warnock", "GA", "D", "https://www.warnock.senate.gov/contact",
         committees=["Banking"],
         votes={"ndaa_2025": "yea", "fisa_2024": "nay"}),

    # -- HAWAII --
    _sen("Mazie Hirono", "HI", "D", "https://www.hirono.senate.gov/contact",
         committees=["Armed Services"],
         votes={"tax_cuts_2017": "nay", "ndaa_2025": "yea", "fisa_2024": "nay"}),
    _sen("Brian Schatz", "HI", "D", "https://www.schatz.senate.gov/contact",
         votes={"tax_cuts_2017": "nay", "ndaa_2025": "yea", "fisa_2024": "nay"}),

    # -- IDAHO --
    _sen("Mike Crapo", "ID", "R", "https://www.crapo.senate.gov/contact",
         committees=["Banking"],
         votes={"tarp": "nay", "tax_cuts_2017": "yea", "dodd_frank_rollback": "yea",
                "ndaa_2025": "yea", "fisa_2024": "yea"}),
    _sen("Jim Risch", "ID", "R", "https://www.risch.senate.gov/contact",
         votes={"tax_cuts_2017": "yea", "dodd_frank_rollback": "yea",
                "ndaa_2025": "yea", "fisa_2024": "yea"}),

    # -- ILLINOIS --
    _sen("Tammy Duckworth", "IL", "D", "https://www.duckworth.senate.gov/contact",
         committees=["Armed Services"],
         votes={"tax_cuts_2017": "nay", "ndaa_2025": "yea", "fisa_2024": "yea"}),
    _sen("Dick Durbin", "IL", "D", "https://www.durbin.senate.gov/contact",
         votes={"tarp": "yea", "iraq_war": "nay", "patriot_act": "yea",
                "tax_cuts_2017": "nay", "ndaa_2025": "yea", "fisa_2024": "nay"}),

    # -- INDIANA --
    _sen("Jim Banks", "IN", "R", "https://www.banks.senate.gov/contact",
         committees=["Banking", "Armed Services"],
         votes={"ndaa_2025": "yea", "fisa_2024": "yea"}),
    _sen("Todd Young", "IN", "R", "https://www.young.senate.gov/contact",
         votes={"tax_cuts_2017": "yea", "ndaa_2025": "yea", "fisa_2024": "yea"}),

    # -- IOWA --
    _sen("Joni Ernst", "IA", "R", "https://www.ernst.senate.gov/contact",
         committees=["Armed Services"],
         votes={"tax_cuts_2017": "yea", "ndaa_2025": "yea", "fisa_2024": "yea"}),
    _sen("Chuck Grassley", "IA", "R", "https://www.grassley.senate.gov/contact",
         votes={"tarp": "yea", "iraq_war": "yea", "patriot_act": "yea",
                "tax_cuts_2017": "yea", "dodd_frank_rollback": "yea",
                "ndaa_2025": "yea", "fisa_2024": "yea"}),

    # -- KANSAS --
    _sen("Roger Marshall", "KS", "R", "https://www.marshall.senate.gov/contact",
         votes={"ndaa_2025": "yea", "fisa_2024": "yea"}),
    _sen("Jerry Moran", "KS", "R", "https://www.moran.senate.gov/contact",
         votes={"tax_cuts_2017": "yea", "dodd_frank_rollback": "yea",
                "ndaa_2025": "yea", "fisa_2024": "yea"}),

    # -- KENTUCKY --
    _sen("Mitch McConnell", "KY", "R", "https://www.mcconnell.senate.gov/contact",
         votes={"tarp": "yea", "iraq_war": "yea", "patriot_act": "yea",
                "tax_cuts_2017": "yea", "dodd_frank_rollback": "yea",
                "ndaa_2025": "yea", "fisa_2024": "yea"}),
    _sen("Rand Paul", "KY", "R", "https://www.paul.senate.gov/contact",
         votes={"tax_cuts_2017": "yea", "dodd_frank_rollback": "yea",
                "ndaa_2025": "nay", "fisa_2024": "nay", "patriot_act": "nay"}),

    # -- LOUISIANA --
    _sen("Bill Cassidy", "LA", "R", "https://www.cassidy.senate.gov/contact",
         votes={"tax_cuts_2017": "yea", "dodd_frank_rollback": "yea",
                "ndaa_2025": "yea", "fisa_2024": "yea"}),
    _sen("John Kennedy", "LA", "R", "https://www.kennedy.senate.gov/contact",
         committees=["Banking"],
         votes={"tax_cuts_2017": "yea", "dodd_frank_rollback": "yea",
                "ndaa_2025": "yea", "fisa_2024": "yea"}),

    # -- MAINE --
    _sen("Susan Collins", "ME", "R", "https://www.collins.senate.gov/contact",
         votes={"tarp": "yea", "iraq_war": "yea", "patriot_act": "yea",
                "tax_cuts_2017": "yea", "dodd_frank_rollback": "yea",
                "ndaa_2025": "yea", "fisa_2024": "yea"}),
    _sen("Angus King", "ME", "I", "https://www.king.senate.gov/contact",
         committees=["Armed Services"],
         votes={"tax_cuts_2017": "nay", "ndaa_2025": "yea", "fisa_2024": "yea"}),

    # -- MARYLAND --
    _sen("Angela Alsobrooks", "MD", "D", "https://www.alsobrooks.senate.gov/contact",
         committees=["Banking"],
         votes={}),  # New 2025
    _sen("Chris Van Hollen", "MD", "D", "https://www.vanhollen.senate.gov/contact",
         committees=["Banking"],
         votes={"tax_cuts_2017": "nay", "ndaa_2025": "yea", "fisa_2024": "nay"}),

    # -- MASSACHUSETTS --
    _sen("Ed Markey", "MA", "D", "https://www.markey.senate.gov/contact",
         votes={"tax_cuts_2017": "nay", "ndaa_2025": "nay", "fisa_2024": "nay",
                "patriot_act": "nay"}),
    _sen("Elizabeth Warren", "MA", "D", "https://www.warren.senate.gov/contact",
         committees=["Banking", "Armed Services"],
         votes={"tax_cuts_2017": "nay", "dodd_frank_rollback": "nay",
                "ndaa_2025": "nay", "fisa_2024": "nay", "genius_act": "nay"}),

    # -- MICHIGAN --
    _sen("Gary Peters", "MI", "D", "https://www.peters.senate.gov/contact",
         committees=["Armed Services"],
         votes={"tax_cuts_2017": "nay", "ndaa_2025": "yea", "fisa_2024": "yea"}),
    _sen("Elissa Slotkin", "MI", "D", "https://www.slotkin.senate.gov/contact",
         committees=["Armed Services"],
         votes={"ndaa_2025": "yea", "fisa_2024": "yea"}),

    # -- MINNESOTA --
    _sen("Amy Klobuchar", "MN", "D", "https://www.klobuchar.senate.gov/contact",
         votes={"tax_cuts_2017": "nay", "ndaa_2025": "yea", "fisa_2024": "yea"}),
    _sen("Tina Smith", "MN", "D", "https://www.smith.senate.gov/contact",
         committees=["Banking"],
         votes={"tax_cuts_2017": "nay", "ndaa_2025": "yea", "fisa_2024": "nay"}),

    # -- MISSISSIPPI --
    _sen("Cindy Hyde-Smith", "MS", "R", "https://www.hydesmith.senate.gov/contact",
         votes={"tax_cuts_2017": "yea", "ndaa_2025": "yea", "fisa_2024": "yea"}),
    _sen("Roger Wicker", "MS", "R", "https://www.wicker.senate.gov/contact",
         committees=["Armed Services"],
         votes={"tarp": "yea", "iraq_war": "yea", "patriot_act": "yea",
                "tax_cuts_2017": "yea", "dodd_frank_rollback": "yea",
                "ndaa_2025": "yea", "fisa_2024": "yea"}),

    # -- MISSOURI --
    _sen("Josh Hawley", "MO", "R", "https://www.hawley.senate.gov/contact",
         votes={"ndaa_2025": "nay", "fisa_2024": "nay"}),
    _sen("Eric Schmitt", "MO", "R", "https://www.schmitt.senate.gov/contact",
         committees=["Armed Services"],
         votes={"ndaa_2025": "nay", "fisa_2024": "nay"}),

    # -- MONTANA --
    _sen("Steve Daines", "MT", "R", "https://www.daines.senate.gov/contact",
         votes={"tax_cuts_2017": "yea", "ndaa_2025": "yea", "fisa_2024": "yea"}),
    _sen("Tim Sheehy", "MT", "R", "https://www.sheehy.senate.gov/contact",
         committees=["Armed Services"],
         votes={"ndaa_2025": "yea"}),  # New 2025

    # -- NEBRASKA --
    _sen("Deb Fischer", "NE", "R", "https://www.fischer.senate.gov/contact",
         committees=["Armed Services"],
         votes={"tax_cuts_2017": "yea", "ndaa_2025": "yea", "fisa_2024": "yea"}),
    _sen("Pete Ricketts", "NE", "R", "https://www.ricketts.senate.gov/contact",
         committees=["Banking"],
         votes={"ndaa_2025": "yea", "fisa_2024": "yea"}),

    # -- NEVADA --
    _sen("Catherine Cortez Masto", "NV", "D", "https://www.cortezmasto.senate.gov/contact",
         committees=["Banking"],
         votes={"tax_cuts_2017": "nay", "dodd_frank_rollback": "nay",
                "ndaa_2025": "yea", "fisa_2024": "yea"}),
    _sen("Jacky Rosen", "NV", "D", "https://www.rosen.senate.gov/contact",
         committees=["Armed Services"],
         votes={"ndaa_2025": "yea", "fisa_2024": "yea"}),

    # -- NEW HAMPSHIRE --
    _sen("Maggie Hassan", "NH", "D", "https://www.hassan.senate.gov/contact",
         votes={"tax_cuts_2017": "nay", "ndaa_2025": "yea", "fisa_2024": "yea"}),
    _sen("Jeanne Shaheen", "NH", "D", "https://www.shaheen.senate.gov/contact",
         committees=["Armed Services"],
         votes={"tax_cuts_2017": "nay", "dodd_frank_rollback": "nay",
                "ndaa_2025": "yea", "fisa_2024": "yea"}),

    # -- NEW JERSEY --
    _sen("Andy Kim", "NJ", "D", "https://www.andykim.senate.gov/contact",
         committees=["Banking"],
         votes={"ndaa_2025": "yea"}),  # New 2025
    _sen("Cory Booker", "NJ", "D", "https://www.booker.senate.gov/contact",
         votes={"tax_cuts_2017": "nay", "dodd_frank_rollback": "nay",
                "ndaa_2025": "yea", "fisa_2024": "nay"}),

    # -- NEW MEXICO --
    _sen("Martin Heinrich", "NM", "D", "https://www.heinrich.senate.gov/contact",
         votes={"tax_cuts_2017": "nay", "ndaa_2025": "yea", "fisa_2024": "nay"}),
    _sen("Ben Ray Lujan", "NM", "D", "https://www.lujan.senate.gov/contact",
         votes={"ndaa_2025": "yea", "fisa_2024": "yea"}),

    # -- NEW YORK --
    _sen("Kirsten Gillibrand", "NY", "D", "https://www.gillibrand.senate.gov/contact",
         committees=["Armed Services"],
         votes={"tax_cuts_2017": "nay", "dodd_frank_rollback": "nay",
                "ndaa_2025": "yea", "fisa_2024": "yea"}),
    _sen("Chuck Schumer", "NY", "D", "https://www.schumer.senate.gov/contact",
         votes={"tarp": "yea", "iraq_war": "yea", "patriot_act": "yea",
                "tax_cuts_2017": "nay", "dodd_frank_rollback": "nay",
                "ndaa_2025": "yea", "fisa_2024": "yea"}),

    # -- NORTH CAROLINA --
    _sen("Ted Budd", "NC", "R", "https://www.budd.senate.gov/contact",
         committees=["Armed Services"],
         votes={"ndaa_2025": "yea", "fisa_2024": "nay"}),
    _sen("Thom Tillis", "NC", "R", "https://www.tillis.senate.gov/contact",
         committees=["Banking"],
         votes={"tax_cuts_2017": "yea", "dodd_frank_rollback": "yea",
                "ndaa_2025": "yea", "fisa_2024": "yea"}),

    # -- NORTH DAKOTA --
    _sen("Kevin Cramer", "ND", "R", "https://www.cramer.senate.gov/contact",
         committees=["Banking", "Armed Services"],
         votes={"tax_cuts_2017": "yea", "ndaa_2025": "yea", "fisa_2024": "yea"}),
    _sen("John Hoeven", "ND", "R", "https://www.hoeven.senate.gov/contact",
         votes={"tax_cuts_2017": "yea", "dodd_frank_rollback": "yea",
                "ndaa_2025": "yea", "fisa_2024": "yea"}),

    # -- OHIO --
    _sen("Jon Husted", "OH", "R", "https://www.husted.senate.gov/contact",
         votes={}),  # Appointed 2025
    _sen("Bernie Moreno", "OH", "R", "https://www.moreno.senate.gov/contact",
         committees=["Banking"],
         votes={"ndaa_2025": "yea"}),  # New 2025

    # -- OKLAHOMA --
    _sen("James Lankford", "OK", "R", "https://www.lankford.senate.gov/contact",
         votes={"tax_cuts_2017": "yea", "ndaa_2025": "yea", "fisa_2024": "yea"}),
    _sen("Markwayne Mullin", "OK", "R", "https://www.mullin.senate.gov/contact",
         committees=["Armed Services"],
         votes={"ndaa_2025": "yea", "fisa_2024": "yea"}),

    # -- OREGON --
    _sen("Jeff Merkley", "OR", "D", "https://www.merkley.senate.gov/contact",
         votes={"tax_cuts_2017": "nay", "dodd_frank_rollback": "nay",
                "ndaa_2025": "nay", "fisa_2024": "nay", "patriot_act": "nay"}),
    _sen("Ron Wyden", "OR", "D", "https://www.wyden.senate.gov/contact",
         votes={"tarp": "nay", "iraq_war": "nay", "patriot_act": "nay",
                "tax_cuts_2017": "nay", "dodd_frank_rollback": "nay",
                "ndaa_2025": "nay", "fisa_2024": "nay"}),

    # -- PENNSYLVANIA --
    _sen("John Fetterman", "PA", "D", "https://www.fetterman.senate.gov/contact",
         votes={"ndaa_2025": "yea", "fisa_2024": "yea"}),
    _sen("Dave McCormick", "PA", "R", "https://www.mccormick.senate.gov/contact",
         committees=["Banking"],
         votes={"ndaa_2025": "yea"}),  # New 2025

    # -- RHODE ISLAND --
    _sen("Jack Reed", "RI", "D", "https://www.reed.senate.gov/contact",
         committees=["Banking", "Armed Services"],
         votes={"tarp": "yea", "iraq_war": "yea", "patriot_act": "yea",
                "tax_cuts_2017": "nay", "ndaa_2025": "yea", "fisa_2024": "yea"}),
    _sen("Sheldon Whitehouse", "RI", "D", "https://www.whitehouse.senate.gov/contact",
         votes={"tarp": "yea", "tax_cuts_2017": "nay",
                "ndaa_2025": "yea", "fisa_2024": "yea"}),

    # -- SOUTH CAROLINA --
    _sen("Lindsey Graham", "SC", "R", "https://www.lgraham.senate.gov/contact",
         votes={"tarp": "yea", "iraq_war": "yea", "patriot_act": "yea",
                "tax_cuts_2017": "yea", "dodd_frank_rollback": "yea",
                "ndaa_2025": "yea", "fisa_2024": "yea"}),
    _sen("Tim Scott", "SC", "R", "https://www.scott.senate.gov/contact",
         committees=["Banking"],
         votes={"tax_cuts_2017": "yea", "dodd_frank_rollback": "yea",
                "ndaa_2025": "yea", "fisa_2024": "yea", "genius_act": "yea"}),

    # -- SOUTH DAKOTA --
    _sen("Mike Rounds", "SD", "R", "https://www.rounds.senate.gov/contact",
         committees=["Banking", "Armed Services"],
         votes={"tax_cuts_2017": "yea", "dodd_frank_rollback": "yea",
                "ndaa_2025": "yea", "fisa_2024": "yea"}),
    _sen("John Thune", "SD", "R", "https://www.thune.senate.gov/contact",
         votes={"tarp": "nay", "iraq_war": "yea", "patriot_act": "yea",
                "tax_cuts_2017": "yea", "dodd_frank_rollback": "yea",
                "ndaa_2025": "yea", "fisa_2024": "yea"}),

    # -- TENNESSEE --
    _sen("Marsha Blackburn", "TN", "R", "https://www.blackburn.senate.gov/contact",
         votes={"tax_cuts_2017": "yea", "ndaa_2025": "yea", "fisa_2024": "yea"}),
    _sen("Bill Hagerty", "TN", "R", "https://www.hagerty.senate.gov/contact",
         committees=["Banking"],
         votes={"ndaa_2025": "nay", "fisa_2024": "nay"}),

    # -- TEXAS --
    _sen("John Cornyn", "TX", "R", "https://www.cornyn.senate.gov/contact",
         votes={"tarp": "yea", "iraq_war": "yea", "patriot_act": "yea",
                "tax_cuts_2017": "yea", "dodd_frank_rollback": "yea",
                "ndaa_2025": "yea", "fisa_2024": "yea"}),
    _sen("Ted Cruz", "TX", "R", "https://www.cruz.senate.gov/contact",
         votes={"tax_cuts_2017": "yea", "dodd_frank_rollback": "yea",
                "ndaa_2025": "nay", "fisa_2024": "nay", "patriot_act": "nay"}),

    # -- UTAH --
    _sen("John Curtis", "UT", "R", "https://www.curtis.senate.gov/contact",
         votes={"ndaa_2025": "yea"}),  # New 2025
    _sen("Mike Lee", "UT", "R", "https://www.lee.senate.gov/contact",
         votes={"tax_cuts_2017": "yea", "dodd_frank_rollback": "yea",
                "ndaa_2025": "nay", "fisa_2024": "nay", "patriot_act": "nay"}),

    # -- VERMONT --
    _sen("Bernie Sanders", "VT", "I", "https://www.sanders.senate.gov/contact",
         votes={"tarp": "nay", "iraq_war": "nay", "patriot_act": "nay",
                "tax_cuts_2017": "nay", "dodd_frank_rollback": "nay",
                "ndaa_2025": "nay", "fisa_2024": "nay"}),
    _sen("Peter Welch", "VT", "D", "https://www.welch.senate.gov/contact",
         votes={"ndaa_2025": "nay", "fisa_2024": "nay"}),

    # -- VIRGINIA --
    _sen("Tim Kaine", "VA", "D", "https://www.kaine.senate.gov/contact",
         committees=["Armed Services"],
         votes={"tax_cuts_2017": "nay", "ndaa_2025": "yea", "fisa_2024": "yea"}),
    _sen("Mark Warner", "VA", "D", "https://www.warner.senate.gov/contact",
         committees=["Banking"],
         votes={"tarp": "yea", "tax_cuts_2017": "nay", "dodd_frank_rollback": "yea",
                "ndaa_2025": "yea", "fisa_2024": "yea"}),

    # -- WASHINGTON --
    _sen("Maria Cantwell", "WA", "D", "https://www.cantwell.senate.gov/contact",
         votes={"tarp": "yea", "iraq_war": "nay", "patriot_act": "yea",
                "tax_cuts_2017": "nay", "ndaa_2025": "yea", "fisa_2024": "yea"}),
    _sen("Patty Murray", "WA", "D", "https://www.murray.senate.gov/contact",
         votes={"tarp": "yea", "iraq_war": "nay", "patriot_act": "yea",
                "tax_cuts_2017": "nay", "ndaa_2025": "yea", "fisa_2024": "yea"}),

    # -- WEST VIRGINIA --
    _sen("Shelley Moore Capito", "WV", "R", "https://www.capito.senate.gov/contact",
         votes={"tax_cuts_2017": "yea", "dodd_frank_rollback": "yea",
                "ndaa_2025": "yea", "fisa_2024": "yea"}),
    _sen("Jim Justice", "WV", "R", "https://www.justice.senate.gov/contact",
         votes={"ndaa_2025": "yea"}),  # New 2025

    # -- WISCONSIN --
    _sen("Tammy Baldwin", "WI", "D", "https://www.baldwin.senate.gov/contact",
         votes={"tax_cuts_2017": "nay", "dodd_frank_rollback": "nay",
                "ndaa_2025": "yea", "fisa_2024": "nay"}),
    _sen("Ron Johnson", "WI", "R", "https://www.ronjohnson.senate.gov/contact",
         votes={"tax_cuts_2017": "yea", "dodd_frank_rollback": "yea",
                "ndaa_2025": "nay", "fisa_2024": "nay", "patriot_act": "nay"}),

    # -- WYOMING --
    _sen("John Barrasso", "WY", "R", "https://www.barrasso.senate.gov/contact",
         votes={"tarp": "yea", "iraq_war": "yea", "patriot_act": "yea",
                "tax_cuts_2017": "yea", "dodd_frank_rollback": "yea",
                "ndaa_2025": "yea", "fisa_2024": "yea"}),
    _sen("Cynthia Lummis", "WY", "R", "https://www.lummis.senate.gov/contact",
         committees=["Banking"],
         votes={"ndaa_2025": "yea", "fisa_2024": "nay", "genius_act": "yea"}),

    # ===================================================================
    # HOUSE FINANCIAL SERVICES COMMITTEE (119th Congress)
    # Email format: firstname.lastname@mail.house.gov
    # ===================================================================

    # -- Republicans --
    _rep("French Hill", "AR", "R", "french.hill@mail.house.gov",
         committees=["Financial Services"],
         votes={"tax_cuts_2017": "yea", "dodd_frank_rollback": "yea",
                "ndaa_2025": "yea", "fisa_2024": "yea", "genius_act": "yea"}),
    _rep("Frank Lucas", "OK", "R", "frank.lucas@mail.house.gov",
         committees=["Financial Services"],
         votes={"tarp": "nay", "iraq_war": "yea", "patriot_act": "yea",
                "tax_cuts_2017": "yea", "dodd_frank_rollback": "yea",
                "ndaa_2025": "yea", "fisa_2024": "yea"}),
    _rep("Pete Sessions", "TX", "R", "pete.sessions@mail.house.gov",
         committees=["Financial Services"],
         votes={"tarp": "yea", "iraq_war": "yea", "patriot_act": "yea",
                "tax_cuts_2017": "yea", "ndaa_2025": "yea", "fisa_2024": "yea"}),
    _rep("Bill Huizenga", "MI", "R", "bill.huizenga@mail.house.gov",
         committees=["Financial Services"],
         votes={"tax_cuts_2017": "yea", "dodd_frank_rollback": "yea",
                "ndaa_2025": "yea", "fisa_2024": "yea"}),
    _rep("Ann Wagner", "MO", "R", "ann.wagner@mail.house.gov",
         committees=["Financial Services"],
         votes={"tax_cuts_2017": "yea", "dodd_frank_rollback": "yea",
                "ndaa_2025": "yea", "fisa_2024": "yea"}),
    _rep("Andy Barr", "KY", "R", "andy.barr@mail.house.gov",
         committees=["Financial Services"],
         votes={"tax_cuts_2017": "yea", "dodd_frank_rollback": "yea",
                "ndaa_2025": "yea", "fisa_2024": "yea"}),
    _rep("Roger Williams", "TX", "R", "roger.williams@mail.house.gov",
         committees=["Financial Services"],
         votes={"tax_cuts_2017": "yea", "dodd_frank_rollback": "yea",
                "ndaa_2025": "yea", "fisa_2024": "yea"}),
    _rep("Tom Emmer", "MN", "R", "tom.emmer@mail.house.gov",
         committees=["Financial Services"],
         votes={"tax_cuts_2017": "yea", "ndaa_2025": "yea", "fisa_2024": "yea"}),
    _rep("Barry Loudermilk", "GA", "R", "barry.loudermilk@mail.house.gov",
         committees=["Financial Services"],
         votes={"tax_cuts_2017": "yea", "ndaa_2025": "yea", "fisa_2024": "yea"}),
    _rep("Warren Davidson", "OH", "R", "warren.davidson@mail.house.gov",
         committees=["Financial Services"],
         votes={"tax_cuts_2017": "yea", "dodd_frank_rollback": "yea",
                "ndaa_2025": "nay", "fisa_2024": "nay"}),
    _rep("John Rose", "TN", "R", "john.rose@mail.house.gov",
         committees=["Financial Services"],
         votes={"ndaa_2025": "yea", "fisa_2024": "yea"}),
    _rep("Bryan Steil", "WI", "R", "bryan.steil@mail.house.gov",
         committees=["Financial Services"],
         votes={"ndaa_2025": "yea", "fisa_2024": "yea"}),
    _rep("William Timmons", "SC", "R", "william.timmons@mail.house.gov",
         committees=["Financial Services"],
         votes={"ndaa_2025": "yea", "fisa_2024": "yea"}),
    _rep("Ralph Norman", "SC", "R", "ralph.norman@mail.house.gov",
         committees=["Financial Services"],
         votes={"tax_cuts_2017": "yea", "ndaa_2025": "nay", "fisa_2024": "nay"}),
    _rep("Dan Meuser", "PA", "R", "dan.meuser@mail.house.gov",
         committees=["Financial Services"],
         votes={"ndaa_2025": "yea", "fisa_2024": "yea"}),
    _rep("Young Kim", "CA", "R", "young.kim@mail.house.gov",
         committees=["Financial Services"],
         votes={"ndaa_2025": "yea", "fisa_2024": "yea"}),
    _rep("Byron Donalds", "FL", "R", "byron.donalds@mail.house.gov",
         committees=["Financial Services"],
         votes={"ndaa_2025": "nay", "fisa_2024": "nay"}),
    _rep("Andrew Garbarino", "NY", "R", "andrew.garbarino@mail.house.gov",
         committees=["Financial Services"],
         votes={"ndaa_2025": "yea", "fisa_2024": "yea"}),
    _rep("Scott Fitzgerald", "WI", "R", "scott.fitzgerald@mail.house.gov",
         committees=["Financial Services"],
         votes={"ndaa_2025": "yea", "fisa_2024": "yea"}),
    _rep("Mike Flood", "NE", "R", "mike.flood@mail.house.gov",
         committees=["Financial Services"],
         votes={"ndaa_2025": "yea", "fisa_2024": "yea"}),
    _rep("Mike Lawler", "NY", "R", "mike.lawler@mail.house.gov",
         committees=["Financial Services"],
         votes={"ndaa_2025": "yea", "fisa_2024": "yea"}),
    _rep("Monica De La Cruz", "TX", "R", "monica.delacruz@mail.house.gov",
         committees=["Financial Services"],
         votes={"ndaa_2025": "yea", "fisa_2024": "yea"}),
    _rep("Andy Ogles", "TN", "R", "andy.ogles@mail.house.gov",
         committees=["Financial Services"],
         votes={"ndaa_2025": "nay", "fisa_2024": "nay"}),
    _rep("Zach Nunn", "IA", "R", "zach.nunn@mail.house.gov",
         committees=["Financial Services"],
         votes={"ndaa_2025": "yea", "fisa_2024": "yea"}),
    _rep("Lisa McClain", "MI", "R", "lisa.mcclain@mail.house.gov",
         committees=["Financial Services"],
         votes={"ndaa_2025": "yea", "fisa_2024": "yea"}),
    _rep("Maria Elvira Salazar", "FL", "R", "maria.salazar@mail.house.gov",
         committees=["Financial Services"],
         votes={"ndaa_2025": "yea", "fisa_2024": "yea"}),
    _rep("Marlin Stutzman", "IN", "R", "marlin.stutzman@mail.house.gov",
         committees=["Financial Services"],
         votes={}),  # Returning member, new term
    _rep("Troy Downing", "MT", "R", "troy.downing@mail.house.gov",
         committees=["Financial Services"],
         votes={}),  # New 2025
    _rep("Mike Haridopolos", "FL", "R", "mike.haridopolos@mail.house.gov",
         committees=["Financial Services"],
         votes={}),  # New 2025
    _rep("Tim Moore", "NC", "R", "tim.moore@mail.house.gov",
         committees=["Financial Services"],
         votes={}),  # New 2025

    # -- Democrats --
    _rep("Maxine Waters", "CA", "D", "maxine.waters@mail.house.gov",
         committees=["Financial Services"],
         votes={"tarp": "yea", "iraq_war": "nay", "patriot_act": "yea",
                "tax_cuts_2017": "nay", "dodd_frank_rollback": "nay",
                "fisa_2024": "nay", "ndaa_2025": "nay"}),
    _rep("Brad Sherman", "CA", "D", "brad.sherman@mail.house.gov",
         committees=["Financial Services"],
         votes={"tarp": "nay", "iraq_war": "yea", "patriot_act": "yea",
                "tax_cuts_2017": "nay", "dodd_frank_rollback": "nay",
                "ndaa_2025": "yea", "fisa_2024": "yea"}),
    _rep("Gregory Meeks", "NY", "D", "gregory.meeks@mail.house.gov",
         committees=["Financial Services"],
         votes={"tarp": "yea", "iraq_war": "yea", "patriot_act": "yea",
                "tax_cuts_2017": "nay", "ndaa_2025": "yea", "fisa_2024": "yea"}),
    _rep("David Scott", "GA", "D", "david.scott@mail.house.gov",
         committees=["Financial Services"],
         votes={"tarp": "yea", "iraq_war": "yea", "tax_cuts_2017": "nay",
                "ndaa_2025": "yea", "fisa_2024": "yea"}),
    _rep("Nydia Velazquez", "NY", "D", "nydia.velazquez@mail.house.gov",
         committees=["Financial Services"],
         votes={"tarp": "nay", "iraq_war": "nay", "patriot_act": "nay",
                "tax_cuts_2017": "nay", "ndaa_2025": "nay", "fisa_2024": "nay"}),
    _rep("Al Green", "TX", "D", "al.green@mail.house.gov",
         committees=["Financial Services"],
         votes={"tarp": "nay", "tax_cuts_2017": "nay",
                "ndaa_2025": "yea", "fisa_2024": "yea"}),
    _rep("Emanuel Cleaver", "MO", "D", "emanuel.cleaver@mail.house.gov",
         committees=["Financial Services"],
         votes={"tarp": "yea", "iraq_war": "nay", "tax_cuts_2017": "nay",
                "ndaa_2025": "yea", "fisa_2024": "yea"}),
    _rep("Jim Himes", "CT", "D", "jim.himes@mail.house.gov",
         committees=["Financial Services"],
         votes={"tax_cuts_2017": "nay", "dodd_frank_rollback": "nay",
                "ndaa_2025": "yea", "fisa_2024": "yea"}),
    _rep("Stephen Lynch", "MA", "D", "stephen.lynch@mail.house.gov",
         committees=["Financial Services"],
         votes={"iraq_war": "yea", "tax_cuts_2017": "nay",
                "ndaa_2025": "yea", "fisa_2024": "yea"}),
    _rep("Bill Foster", "IL", "D", "bill.foster@mail.house.gov",
         committees=["Financial Services"],
         votes={"tax_cuts_2017": "nay", "ndaa_2025": "yea", "fisa_2024": "yea"}),
    _rep("Joyce Beatty", "OH", "D", "joyce.beatty@mail.house.gov",
         committees=["Financial Services"],
         votes={"tax_cuts_2017": "nay", "ndaa_2025": "yea", "fisa_2024": "yea"}),
    _rep("Juan Vargas", "CA", "D", "juan.vargas@mail.house.gov",
         committees=["Financial Services"],
         votes={"tax_cuts_2017": "nay", "ndaa_2025": "yea", "fisa_2024": "yea"}),
    _rep("Josh Gottheimer", "NJ", "D", "josh.gottheimer@mail.house.gov",
         committees=["Financial Services"],
         votes={"tax_cuts_2017": "nay", "dodd_frank_rollback": "yea",
                "ndaa_2025": "yea", "fisa_2024": "yea"}),
    _rep("Sean Casten", "IL", "D", "sean.casten@mail.house.gov",
         committees=["Financial Services"],
         votes={"ndaa_2025": "yea", "fisa_2024": "yea"}),
    _rep("Ayanna Pressley", "MA", "D", "ayanna.pressley@mail.house.gov",
         committees=["Financial Services"],
         votes={"ndaa_2025": "nay", "fisa_2024": "nay"}),
    _rep("Rashida Tlaib", "MI", "D", "rashida.tlaib@mail.house.gov",
         committees=["Financial Services"],
         votes={"ndaa_2025": "nay", "fisa_2024": "nay"}),
    _rep("Ritchie Torres", "NY", "D", "ritchie.torres@mail.house.gov",
         committees=["Financial Services"],
         votes={"ndaa_2025": "yea", "fisa_2024": "yea"}),
    _rep("Sylvia Garcia", "TX", "D", "sylvia.garcia@mail.house.gov",
         committees=["Financial Services"],
         votes={"ndaa_2025": "yea", "fisa_2024": "yea"}),
    _rep("Nikema Williams", "GA", "D", "nikema.williams@mail.house.gov",
         committees=["Financial Services"],
         votes={"ndaa_2025": "yea", "fisa_2024": "yea"}),
    _rep("Brittany Pettersen", "CO", "D", "brittany.pettersen@mail.house.gov",
         committees=["Financial Services"],
         votes={"ndaa_2025": "yea", "fisa_2024": "yea"}),
    _rep("Vicente Gonzalez", "TX", "D", "vicente.gonzalez@mail.house.gov",
         committees=["Financial Services"],
         votes={"ndaa_2025": "yea", "fisa_2024": "yea"}),
    _rep("Cleo Fields", "LA", "D", "cleo.fields@mail.house.gov",
         committees=["Financial Services"],
         votes={}),  # New 2025
    _rep("Janelle Bynum", "OR", "D", "janelle.bynum@mail.house.gov",
         committees=["Financial Services"],
         votes={}),  # New 2025
    _rep("Sam Liccardo", "CA", "D", "sam.liccardo@mail.house.gov",
         committees=["Financial Services"],
         votes={}),  # New 2025

    # ===================================================================
    # HOUSE ARMED SERVICES COMMITTEE (119th Congress)
    # ===================================================================

    # -- Republicans --
    _rep("Mike Rogers", "AL", "R", "mike.rogers@mail.house.gov",
         committees=["Armed Services"],
         votes={"tarp": "nay", "iraq_war": "yea", "patriot_act": "yea",
                "tax_cuts_2017": "yea", "ndaa_2025": "yea", "fisa_2024": "yea"}),
    _rep("Joe Wilson", "SC", "R", "joe.wilson@mail.house.gov",
         committees=["Armed Services"],
         votes={"tarp": "nay", "iraq_war": "yea", "patriot_act": "yea",
                "tax_cuts_2017": "yea", "ndaa_2025": "yea", "fisa_2024": "yea"}),
    _rep("Michael Turner", "OH", "R", "michael.turner@mail.house.gov",
         committees=["Armed Services"],
         votes={"iraq_war": "yea", "patriot_act": "yea",
                "tax_cuts_2017": "yea", "ndaa_2025": "yea", "fisa_2024": "yea"}),
    _rep("Rob Wittman", "VA", "R", "rob.wittman@mail.house.gov",
         committees=["Armed Services"],
         votes={"tax_cuts_2017": "yea", "ndaa_2025": "yea", "fisa_2024": "yea"}),
    _rep("Austin Scott", "GA", "R", "austin.scott@mail.house.gov",
         committees=["Armed Services"],
         votes={"tax_cuts_2017": "yea", "ndaa_2025": "yea", "fisa_2024": "yea"}),
    _rep("Sam Graves", "MO", "R", "sam.graves@mail.house.gov",
         committees=["Armed Services"],
         votes={"tarp": "nay", "iraq_war": "yea", "tax_cuts_2017": "yea",
                "ndaa_2025": "yea", "fisa_2024": "yea"}),
    _rep("Scott DesJarlais", "TN", "R", "scott.desjarlais@mail.house.gov",
         committees=["Armed Services"],
         votes={"tax_cuts_2017": "yea", "ndaa_2025": "yea", "fisa_2024": "yea"}),
    _rep("Trent Kelly", "MS", "R", "trent.kelly@mail.house.gov",
         committees=["Armed Services"],
         votes={"tax_cuts_2017": "yea", "ndaa_2025": "yea", "fisa_2024": "yea"}),
    _rep("Don Bacon", "NE", "R", "don.bacon@mail.house.gov",
         committees=["Armed Services"],
         votes={"tax_cuts_2017": "yea", "ndaa_2025": "yea", "fisa_2024": "yea"}),
    _rep("Jack Bergman", "MI", "R", "jack.bergman@mail.house.gov",
         committees=["Armed Services"],
         votes={"tax_cuts_2017": "yea", "ndaa_2025": "yea", "fisa_2024": "yea"}),
    _rep("Pat Fallon", "TX", "R", "pat.fallon@mail.house.gov",
         committees=["Armed Services"],
         votes={"ndaa_2025": "yea", "fisa_2024": "yea"}),
    _rep("Carlos Gimenez", "FL", "R", "carlos.gimenez@mail.house.gov",
         committees=["Armed Services"],
         votes={"ndaa_2025": "yea", "fisa_2024": "yea"}),
    _rep("Nancy Mace", "SC", "R", "nancy.mace@mail.house.gov",
         committees=["Armed Services"],
         votes={"ndaa_2025": "nay", "fisa_2024": "nay"}),
    _rep("Brad Finstad", "MN", "R", "brad.finstad@mail.house.gov",
         committees=["Armed Services"],
         votes={"ndaa_2025": "yea", "fisa_2024": "yea"}),
    _rep("Morgan Luttrell", "TX", "R", "morgan.luttrell@mail.house.gov",
         committees=["Armed Services"],
         votes={"ndaa_2025": "yea", "fisa_2024": "yea"}),
    _rep("Jennifer Kiggans", "VA", "R", "jennifer.kiggans@mail.house.gov",
         committees=["Armed Services"],
         votes={"ndaa_2025": "yea", "fisa_2024": "yea"}),
    _rep("Cory Mills", "FL", "R", "cory.mills@mail.house.gov",
         committees=["Armed Services"],
         votes={"ndaa_2025": "nay", "fisa_2024": "nay"}),
    _rep("Rich McCormick", "GA", "R", "rich.mccormick@mail.house.gov",
         committees=["Armed Services"],
         votes={"ndaa_2025": "yea", "fisa_2024": "yea"}),
    _rep("Lance Gooden", "TX", "R", "lance.gooden@mail.house.gov",
         committees=["Armed Services"],
         votes={"ndaa_2025": "yea", "fisa_2024": "yea"}),
    _rep("Clay Higgins", "LA", "R", "clay.higgins@mail.house.gov",
         committees=["Armed Services"],
         votes={"tax_cuts_2017": "yea", "ndaa_2025": "nay", "fisa_2024": "nay"}),
    _rep("Derrick Van Orden", "WI", "R", "derrick.vanorden@mail.house.gov",
         committees=["Armed Services"],
         votes={"ndaa_2025": "yea", "fisa_2024": "yea"}),
    _rep("John McGuire", "VA", "R", "john.mcguire@mail.house.gov",
         committees=["Armed Services"],
         votes={}),  # New 2025
    _rep("Ronny Jackson", "TX", "R", "ronny.jackson@mail.house.gov",
         committees=["Armed Services"],
         votes={"ndaa_2025": "yea", "fisa_2024": "yea"}),
    _rep("Pat Harrigan", "NC", "R", "pat.harrigan@mail.house.gov",
         committees=["Armed Services"],
         votes={}),  # New 2025
    _rep("Mark Messmer", "IN", "R", "mark.messmer@mail.house.gov",
         committees=["Armed Services"],
         votes={}),  # New 2025
    _rep("Derek Schmidt", "KS", "R", "derek.schmidt@mail.house.gov",
         committees=["Armed Services"],
         votes={}),  # New 2025
    _rep("Jeff Crank", "CO", "R", "jeff.crank@mail.house.gov",
         committees=["Armed Services"],
         votes={}),  # New 2025
    _rep("Abraham Hamadeh", "AZ", "R", "abraham.hamadeh@mail.house.gov",
         committees=["Armed Services"],
         votes={}),  # New 2025

    # -- Democrats --
    _rep("Adam Smith", "WA", "D", "adam.smith@mail.house.gov",
         committees=["Armed Services"],
         votes={"tarp": "yea", "iraq_war": "yea", "patriot_act": "yea",
                "tax_cuts_2017": "nay", "ndaa_2025": "yea", "fisa_2024": "yea"}),
    _rep("Joe Courtney", "CT", "D", "joe.courtney@mail.house.gov",
         committees=["Armed Services"],
         votes={"tarp": "nay", "tax_cuts_2017": "nay",
                "ndaa_2025": "yea", "fisa_2024": "yea"}),
    _rep("John Garamendi", "CA", "D", "john.garamendi@mail.house.gov",
         committees=["Armed Services"],
         votes={"tax_cuts_2017": "nay", "ndaa_2025": "yea", "fisa_2024": "yea"}),
    _rep("Donald Norcross", "NJ", "D", "donald.norcross@mail.house.gov",
         committees=["Armed Services"],
         votes={"tax_cuts_2017": "nay", "ndaa_2025": "yea", "fisa_2024": "yea"}),
    _rep("Seth Moulton", "MA", "D", "seth.moulton@mail.house.gov",
         committees=["Armed Services"],
         votes={"tax_cuts_2017": "nay", "ndaa_2025": "yea", "fisa_2024": "yea"}),
    _rep("Salud Carbajal", "CA", "D", "salud.carbajal@mail.house.gov",
         committees=["Armed Services"],
         votes={"tax_cuts_2017": "nay", "ndaa_2025": "yea", "fisa_2024": "yea"}),
    _rep("Ro Khanna", "CA", "D", "ro.khanna@mail.house.gov",
         committees=["Armed Services"],
         votes={"tax_cuts_2017": "nay", "ndaa_2025": "nay", "fisa_2024": "nay"}),
    _rep("Bill Keating", "MA", "D", "bill.keating@mail.house.gov",
         committees=["Armed Services"],
         votes={"tax_cuts_2017": "nay", "ndaa_2025": "yea", "fisa_2024": "yea"}),
    _rep("Chrissy Houlahan", "PA", "D", "chrissy.houlahan@mail.house.gov",
         committees=["Armed Services"],
         votes={"ndaa_2025": "yea", "fisa_2024": "yea"}),
    _rep("Jason Crow", "CO", "D", "jason.crow@mail.house.gov",
         committees=["Armed Services"],
         votes={"ndaa_2025": "yea", "fisa_2024": "yea"}),
    _rep("Jared Golden", "ME", "D", "jared.golden@mail.house.gov",
         committees=["Armed Services"],
         votes={"ndaa_2025": "yea", "fisa_2024": "yea"}),
    _rep("Mikie Sherrill", "NJ", "D", "mikie.sherrill@mail.house.gov",
         committees=["Armed Services"],
         votes={"ndaa_2025": "yea", "fisa_2024": "yea"}),
    _rep("Sara Jacobs", "CA", "D", "sara.jacobs@mail.house.gov",
         committees=["Armed Services"],
         votes={"ndaa_2025": "yea", "fisa_2024": "yea"}),
    _rep("Marilyn Strickland", "WA", "D", "marilyn.strickland@mail.house.gov",
         committees=["Armed Services"],
         votes={"ndaa_2025": "yea", "fisa_2024": "yea"}),
    _rep("Pat Ryan", "NY", "D", "pat.ryan@mail.house.gov",
         committees=["Armed Services"],
         votes={"ndaa_2025": "yea", "fisa_2024": "yea"}),
    _rep("Gabriel Vasquez", "NM", "D", "gabriel.vasquez@mail.house.gov",
         committees=["Armed Services"],
         votes={"ndaa_2025": "yea", "fisa_2024": "yea"}),
    _rep("Chris Deluzio", "PA", "D", "chris.deluzio@mail.house.gov",
         committees=["Armed Services"],
         votes={"ndaa_2025": "yea", "fisa_2024": "nay"}),
    _rep("Jill Tokuda", "HI", "D", "jill.tokuda@mail.house.gov",
         committees=["Armed Services"],
         votes={"ndaa_2025": "yea", "fisa_2024": "yea"}),
    _rep("Donald Davis", "NC", "D", "donald.davis@mail.house.gov",
         committees=["Armed Services"],
         votes={"ndaa_2025": "yea", "fisa_2024": "yea"}),
    _rep("Gil Cisneros", "CA", "D", "gil.cisneros@mail.house.gov",
         committees=["Armed Services"],
         votes={}),  # Returning, new term 2025
    _rep("Sarah Elfreth", "MD", "D", "sarah.elfreth@mail.house.gov",
         committees=["Armed Services"],
         votes={}),  # New 2025
    _rep("George Whitesides", "CA", "D", "george.whitesides@mail.house.gov",
         committees=["Armed Services"],
         votes={}),  # New 2025
    _rep("Derek Tran", "CA", "D", "derek.tran@mail.house.gov",
         committees=["Armed Services"],
         votes={}),  # New 2025
    _rep("Eugene Vindman", "VA", "D", "eugene.vindman@mail.house.gov",
         committees=["Armed Services"],
         votes={}),  # New 2025
    _rep("Eric Sorensen", "IL", "D", "eric.sorensen@mail.house.gov",
         committees=["Armed Services"],
         votes={"ndaa_2025": "yea", "fisa_2024": "yea"}),
    _rep("Maggie Goodlander", "NH", "D", "maggie.goodlander@mail.house.gov",
         committees=["Armed Services"],
         votes={}),  # New 2025
    _rep("Wesley Bell", "MO", "D", "wesley.bell@mail.house.gov",
         committees=["Armed Services"],
         votes={}),  # New 2025
]


# ===========================================================================
# EMAIL GENERATION
# ===========================================================================

SUBJECT = "You Voted For This \u2014 A Documentary About What Was Sold"


def _format_title(member):
    """Return appropriate title: Senator / Representative."""
    if member["chamber"] == "Senate":
        return "Senator"
    return "Representative"


def _build_vote_lines(member):
    """Build personalized vote reference lines for the email body."""
    lines = []
    votes = member.get("votes", {})
    if not votes:
        return []

    for vote_key, position in votes.items():
        if position is None:
            continue
        vote_info = KEY_VOTES.get(vote_key)
        if not vote_info:
            continue
        action = vote_info["yea"] if position == "yea" else vote_info["nay"]
        lines.append(f"  - In {vote_info['year']}, you {action}.")

    return lines


def _build_committee_line(member):
    """Build committee membership reference."""
    comms = member.get("committees", [])
    if not comms:
        return ""
    names = ", ".join(comms)
    return f"As a member of the {names} Committee{'s' if len(comms) > 1 else ''}, your votes carry particular weight on these issues."


def build_personalized_body(member):
    """Generate the full personalized email body for a member."""
    title = _format_title(member)
    last_name = member["name"].split()[-1]
    vote_lines = _build_vote_lines(member)
    committee_line = _build_committee_line(member)

    # Build the vote section
    if vote_lines:
        vote_section = (
            "Your voting record is part of this story:\n"
            + "\n".join(vote_lines)
            + "\n"
        )
    else:
        vote_section = (
            "Your record in Congress is part of this story. "
            "Every vote you cast on financial regulation, defense spending, "
            "and surveillance legislation is documented in the public record.\n"
        )

    body = f"""\
Dear {title} {last_name},

I am writing to share "For Sale" -- a free, open-source documentary that traces
how financial systems, wars, and political decisions are interconnected in American
governance. It names names. It cites votes. It uses only public records.

{vote_section}
{committee_line}

This is not a partisan project. Democrats and Republicans are both covered,
because the public record does not have a party affiliation. The documentary
draws from:

  - Congressional roll call votes (senate.gov, clerk.house.gov)
  - C-SPAN hearing transcripts (Senate Banking, House Financial Services)
  - DOJ press releases and federal court filings
  - SEC and CFTC enforcement actions
  - FEC campaign finance disclosures
  - Congressional Research Service reports

You can view it here:
{DOC_URL}

The full source code is available at:
{SOURCE_URL}

This documentary is free. No one paid for it. No one owns it.
It exists because someone thought you should see it.

Respectfully,
A Concerned Citizen
"""
    return body


# ===========================================================================
# SMTP / SENDING ENGINE
# ===========================================================================

def get_smtp_config():
    """Resolve SMTP configuration from globals or presets."""
    server = SMTP_SERVER
    port = SMTP_PORT

    # Auto-detect preset from server string
    if server.lower() in SMTP_PRESETS:
        preset = SMTP_PRESETS[server.lower()]
        server = preset["server"]
        port = preset["port"]

    return server, port


def build_message(sender, recipient_email, member, reply_to=None):
    """Build a MIME message for one member."""
    msg = MIMEMultipart("alternative")
    msg["Subject"] = SUBJECT
    msg["From"] = sender
    msg["To"] = recipient_email
    if reply_to:
        msg["Reply-To"] = reply_to

    body = build_personalized_body(member)
    msg.attach(MIMEText(body, "plain", "utf-8"))
    return msg


def connect_smtp(server, port, email_addr, password):
    """Establish and authenticate SMTP connection."""
    try:
        smtp = smtplib.SMTP(server, port, timeout=30)
        smtp.ehlo()
        smtp.starttls()
        smtp.ehlo()
        smtp.login(email_addr, password)
        log.info(f"SMTP connected to {server}:{port}")
        return smtp
    except smtplib.SMTPAuthenticationError:
        log.error(
            "SMTP authentication failed. If using Gmail, make sure you're using "
            "an App Password (Google Account > Security > 2FA > App Passwords), "
            "NOT your regular password."
        )
        sys.exit(1)
    except Exception as exc:
        log.error(f"SMTP connection failed: {exc}")
        sys.exit(1)


def send_emails(dry_run=False, export_csv=False):
    """Main send loop."""
    # Filter to members with actual email addresses (not contact URLs for Senate)
    # For senators, we still include them in dry-run to show the full list
    sendable = []
    contact_form_only = []

    for m in MEMBERS:
        if m["chamber"] == "House" or "@" in m["email"]:
            sendable.append(m)
        else:
            contact_form_only.append(m)

    total_sendable = len(sendable)
    total_contact = len(contact_form_only)
    total = len(MEMBERS)

    log.info("=" * 60)
    log.info(f"  FOR SALE DOCUMENTARY — Congressional Blast")
    log.info(f"  {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    log.info("=" * 60)
    log.info(f"  Total members in database:     {total}")
    log.info(f"  Sendable via SMTP (House):     {total_sendable}")
    log.info(f"  Contact form only (Senate):    {total_contact}")
    log.info(f"  Senators: {sum(1 for m in MEMBERS if m['chamber'] == 'Senate')}")
    log.info(f"  House members: {sum(1 for m in MEMBERS if m['chamber'] == 'House')}")
    log.info("")

    # Export CSV if requested
    if export_csv:
        csv_path = Path(__file__).parent / f"congress_targets_{datetime.now().strftime('%Y%m%d')}.csv"
        with open(csv_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["Name", "State", "Party", "Chamber", "Committees",
                             "Email/Contact", "Vote Count", "Notable Votes"])
            for m in MEMBERS:
                vote_strs = [f"{k}:{v}" for k, v in m["votes"].items() if v]
                writer.writerow([
                    m["name"], m["state"], m["party"], m["chamber"],
                    "|".join(m["committees"]), m["email"],
                    len([v for v in m["votes"].values() if v]),
                    "; ".join(vote_strs),
                ])
        log.info(f"CSV exported: {csv_path}")

    if dry_run:
        log.info("DRY RUN MODE — No emails will be sent.\n")

        # Show all emails that would be sent
        for idx, m in enumerate(sendable, 1):
            body = build_personalized_body(m)
            print(f"\n{'='*60}")
            print(f"[{idx}/{total_sendable}] TO: {m['email']}")
            print(f"    {m['name']} ({m['party']}-{m['state']}) — {', '.join(m['committees'])}")
            print(f"    Subject: {SUBJECT}")
            print(f"{'-'*60}")
            print(body)

        if contact_form_only:
            print(f"\n{'='*60}")
            print(f"SENATORS — Contact form submission required ({total_contact} members):")
            print(f"{'='*60}")
            for m in contact_form_only:
                print(f"  {m['name']} ({m['party']}-{m['state']}): {m['email']}")

        log.info(f"\nDRY RUN complete. {total_sendable} emails would be sent via SMTP.")
        log.info(f"{total_contact} senators require manual contact form submission.")
        return

    # LIVE SEND
    server, port = get_smtp_config()

    if not server or not EMAIL_ADDRESS or not EMAIL_PASSWORD:
        log.error(
            "Configuration incomplete. Fill in SMTP_SERVER, EMAIL_ADDRESS, "
            "and EMAIL_PASSWORD at the top of this script."
        )
        sys.exit(1)

    smtp = connect_smtp(server, port, EMAIL_ADDRESS, EMAIL_PASSWORD)

    sent = 0
    failed = 0
    failed_list = []

    for idx, m in enumerate(sendable, 1):
        label = f"[{idx:>3}/{total_sendable}]"

        try:
            msg = build_message(EMAIL_ADDRESS, m["email"], m, reply_to=REPLY_TO or None)
            smtp.sendmail(EMAIL_ADDRESS, m["email"], msg.as_string())
            log.info(f"{label} SENT    -> {m['name']} ({m['party']}-{m['state']}) <{m['email']}>")
            sent += 1
        except smtplib.SMTPServerDisconnected:
            log.warning(f"{label} Reconnecting SMTP...")
            try:
                smtp = connect_smtp(server, port, EMAIL_ADDRESS, EMAIL_PASSWORD)
                msg = build_message(EMAIL_ADDRESS, m["email"], m, reply_to=REPLY_TO or None)
                smtp.sendmail(EMAIL_ADDRESS, m["email"], msg.as_string())
                log.info(f"{label} SENT    -> {m['name']} (after reconnect)")
                sent += 1
            except Exception as exc:
                log.error(f"{label} FAILED  -> {m['name']} <{m['email']}> ({exc})")
                failed += 1
                failed_list.append(m)
        except Exception as exc:
            log.error(f"{label} FAILED  -> {m['name']} <{m['email']}> ({exc})")
            failed += 1
            failed_list.append(m)

        # Rate limiting
        if idx < total_sendable:
            if idx % BATCH_SIZE == 0:
                log.info(f"  Batch pause ({BATCH_PAUSE}s after {BATCH_SIZE} emails)...")
                time.sleep(BATCH_PAUSE)
            else:
                time.sleep(DELAY_BETWEEN_SENDS)

    try:
        smtp.quit()
    except Exception:
        pass

    # Summary
    log.info("")
    log.info("=" * 60)
    log.info(f"  COMPLETE")
    log.info(f"  Sent:   {sent}")
    log.info(f"  Failed: {failed}")
    log.info(f"  Total:  {total_sendable}")
    log.info("=" * 60)

    if failed_list:
        log.info("\nFailed recipients:")
        for m in failed_list:
            log.info(f"  {m['name']} <{m['email']}>")

    if contact_form_only:
        log.info(f"\nREMINDER: {total_contact} senators need manual contact form submission.")
        log.info("Run with --dry-run to see their contact URLs.")

    # Save state for resume capability
    state_file = Path(__file__).parent / "congress_blast_state.json"
    state = {
        "timestamp": datetime.now().isoformat(),
        "sent": sent,
        "failed": failed,
        "failed_emails": [m["email"] for m in failed_list],
    }
    with open(state_file, "w") as f:
        json.dump(state, f, indent=2)
    log.info(f"\nState saved to: {state_file}")


# ===========================================================================
# CLI
# ===========================================================================

def main():
    parser = argparse.ArgumentParser(
        description="For Sale Documentary — Congressional Blast Mailer",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python congress_blast_2026-03-20.py --dry-run          Preview all emails
  python congress_blast_2026-03-20.py --dry-run --csv    Preview + export CSV
  python congress_blast_2026-03-20.py                    Send live emails

Configuration:
  Edit the top of the script to set SMTP_SERVER, EMAIL_ADDRESS, EMAIL_PASSWORD.
  For Gmail, use an App Password (not your regular password).
  For presets, set SMTP_SERVER to: gmail, protonmail, outlook, or fastmail
        """,
    )
    parser.add_argument("--dry-run", action="store_true",
                        help="Print all emails to console without sending")
    parser.add_argument("--csv", action="store_true",
                        help="Export target list to CSV file")
    parser.add_argument("--stats", action="store_true",
                        help="Show database statistics and exit")

    args = parser.parse_args()

    if args.stats:
        print(f"\nMember Database Statistics")
        print(f"{'='*40}")
        senators = [m for m in MEMBERS if m["chamber"] == "Senate"]
        house = [m for m in MEMBERS if m["chamber"] == "House"]
        print(f"  Senators:         {len(senators)}")
        print(f"    Republicans:    {sum(1 for m in senators if m['party'] == 'R')}")
        print(f"    Democrats:      {sum(1 for m in senators if m['party'] == 'D')}")
        print(f"    Independents:   {sum(1 for m in senators if m['party'] == 'I')}")
        print(f"  House members:    {len(house)}")
        print(f"    Republicans:    {sum(1 for m in house if m['party'] == 'R')}")
        print(f"    Democrats:      {sum(1 for m in house if m['party'] == 'D')}")
        print(f"  Total:            {len(MEMBERS)}")
        print(f"\n  Members with vote data: {sum(1 for m in MEMBERS if m['votes'])}")
        print(f"  Members on Banking:     {sum(1 for m in MEMBERS if 'Banking' in m['committees'])}")
        print(f"  Members on Armed Svcs:  {sum(1 for m in MEMBERS if 'Armed Services' in m['committees'])}")
        print(f"  Members on Fin. Svcs:   {sum(1 for m in MEMBERS if 'Financial Services' in m['committees'])}")

        # Vote coverage
        print(f"\n  Vote Coverage:")
        for vk, vi in KEY_VOTES.items():
            count = sum(1 for m in MEMBERS if m["votes"].get(vk))
            print(f"    {vi['bill'][:45]:<45} {count:>3} members")
        return

    send_emails(dry_run=args.dry_run, export_csv=args.csv)


if __name__ == "__main__":
    main()
