"""
email_congress.py — Send "For Sale" documentary to congressional offices.

REQUIREMENTS:
  - You must use a Gmail APP PASSWORD, NOT your regular Gmail password.
  - To generate one: Google Account > Security > 2-Step Verification > App Passwords
  - Create an app password for "Mail" and use that 16-character code here.
  - Regular passwords will be rejected by Gmail SMTP.

USAGE:
  python email_congress.py                 # live send
  python email_congress.py --dry-run       # print what would be sent, no emails sent
"""

import smtplib
import sys
import time
import getpass
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

SMTP_HOST = "smtp.gmail.com"
SMTP_PORT = 587
DELAY_BETWEEN_SENDS = 2  # seconds

SUBJECT = "Free Documentary on Money in Politics — Sourced from Your Own Congressional Records"

BODY = """\
Dear Member of Congress,

I am writing to share "For Sale," a free, open-source interactive documentary \
that traces the influence of money on American governance — from war profiteering \
to cryptocurrency PAC spending to presidential pardons.

The documentary is sourced entirely from public records including:
  • C-SPAN hearing transcripts from Senate Banking and House Financial Services \
Committee hearings
  • Department of Justice press releases and court filings
  • SEC and CFTC enforcement actions and filings
  • FEC campaign finance disclosures
  • Congressional Research Service reports

It includes direct quotes from congressional hearings and is presented without \
editorial bias — the public record speaks for itself.

You can view it here: https://samplerdan-byte.github.io/for-sale-documentary/

The full source code is available at: \
https://github.com/samplerdan-byte/for-sale-documentary

This documentary is free, has no paywall, contains no advertising, and is \
published as open-source software. It was created as a public service.

Respectfully,
A Concerned Citizen
"""

# ---------------------------------------------------------------------------
# Congressional email addresses
#
# House members: firstname.lastname@mail.house.gov
# Senators:      firstname_lastname@senator.senate.gov  (most common pattern)
#                Some use @{lastname}.senate.gov subdomains — noted inline.
#
# NOTE: Congressional offices change email formats periodically. If a message
# bounces, check the member's official website for their current contact form
# or updated address.
# ---------------------------------------------------------------------------

CONGRESSIONAL_EMAILS = [

    # ------------------------------------------------------------------
    # Senate Banking, Housing & Urban Affairs Committee
    # ------------------------------------------------------------------

    # Democrats
    "sherrod_brown@senator.senate.gov",          # Sherrod Brown (OH)
    "elizabeth_warren@warren.senate.gov",         # Elizabeth Warren (MA) — uses subdomain
    "kirsten_gillibrand@gillibrand.senate.gov",   # Kirsten Gillibrand (NY) — uses subdomain
    "mark_warner@warner.senate.gov",              # Mark Warner (VA) — uses subdomain
    "bob_menendez@menendez.senate.gov",           # Bob Menendez (NJ) — uses subdomain
    "jack_reed@reed.senate.gov",                  # Jack Reed (RI) — uses subdomain
    "raphael_warnock@warnock.senate.gov",         # Raphael Warnock (GA)
    "jon_tester@tester.senate.gov",               # Jon Tester (MT) — uses subdomain
    "tina_smith@smith.senate.gov",                # Tina Smith (MN)
    "catherine_cortez_masto@cortez-masto.senate.gov",  # Catherine Cortez Masto (NV)
    "chris_van_hollen@vanhollen.senate.gov",      # Chris Van Hollen (MD)

    # Republicans
    "tim_scott@scott.senate.gov",                 # Tim Scott (SC) — uses subdomain
    "cynthia_lummis@lummis.senate.gov",           # Cynthia Lummis (WY)
    "bill_hagerty@hagerty.senate.gov",            # Bill Hagerty (TN)
    "jd_vance@vance.senate.gov",                  # JD Vance (OH)
    "john_kennedy@kennedy.senate.gov",            # John Kennedy (LA) — uses subdomain
    "mike_rounds@rounds.senate.gov",              # Mike Rounds (SD)
    "thom_tillis@tillis.senate.gov",              # Thom Tillis (NC) — uses subdomain
    "jerry_moran@moran.senate.gov",               # Jerry Moran (KS) — uses subdomain
    "kevin_cramer@cramer.senate.gov",             # Kevin Cramer (ND)
    "steve_daines@daines.senate.gov",             # Steve Daines (MT)
    "katie_britt@britt.senate.gov",               # Katie Britt (AL)

    # ------------------------------------------------------------------
    # House Financial Services Committee
    # ------------------------------------------------------------------

    # Republicans
    "patrick.mchenry@mail.house.gov",             # Patrick McHenry (NC-10)
    "frank.lucas@mail.house.gov",                 # Frank Lucas (OK-03)
    "ann.wagner@mail.house.gov",                  # Ann Wagner (MO-02)
    "andy.barr@mail.house.gov",                   # Andy Barr (KY-06)
    "bill.huizenga@mail.house.gov",               # Bill Huizenga (MI-04)
    "french.hill@mail.house.gov",                 # French Hill (AR-02)
    "blaine.luetkemeyer@mail.house.gov",          # Blaine Luetkemeyer (MO-03)
    "bill.posey@mail.house.gov",                  # Bill Posey (FL-08)
    "warren.davidson@mail.house.gov",             # Warren Davidson (OH-08)
    "bryan.steil@mail.house.gov",                 # Bryan Steil (WI-01)

    # Democrats
    "maxine.waters@mail.house.gov",               # Maxine Waters (CA-43)
    "brad.sherman@mail.house.gov",                # Brad Sherman (CA-32)
    "al.green@mail.house.gov",                    # Al Green (TX-09)
    "ritchie.torres@mail.house.gov",              # Ritchie Torres (NY-15)
    "ayanna.pressley@mail.house.gov",             # Ayanna Pressley (MA-07)
    "rashida.tlaib@mail.house.gov",               # Rashida Tlaib (MI-12)
    "alexandria.ocasio-cortez@mail.house.gov",    # Alexandria Ocasio-Cortez (NY-14)
    "nikema.williams@mail.house.gov",             # Nikema Williams (GA-05)
    "wiley.nickel@mail.house.gov",                # Wiley Nickel (NC-13)

    # ------------------------------------------------------------------
    # Senate Judiciary Committee
    # (relevant for pardon powers / Supreme Court)
    # ------------------------------------------------------------------

    # Democrats
    "dick_durbin@durbin.senate.gov",              # Dick Durbin (IL) — uses subdomain
    "sheldon_whitehouse@whitehouse.senate.gov",   # Sheldon Whitehouse (RI) — uses subdomain
    "amy_klobuchar@klobuchar.senate.gov",         # Amy Klobuchar (MN) — uses subdomain
    "chris_coons@coons.senate.gov",               # Chris Coons (DE)
    "richard_blumenthal@blumenthal.senate.gov",   # Richard Blumenthal (CT) — uses subdomain
    "alex_padilla@padilla.senate.gov",            # Alex Padilla (CA)
    "jon_ossoff@ossoff.senate.gov",               # Jon Ossoff (GA)
    "peter_welch@welch.senate.gov",               # Peter Welch (VT)

    # Republicans
    "lindsey_graham@lgraham.senate.gov",          # Lindsey Graham (SC) — uses subdomain
    "chuck_grassley@grassley.senate.gov",         # Chuck Grassley (IA) — uses subdomain
    "ted_cruz@cruz.senate.gov",                   # Ted Cruz (TX) — uses subdomain
    "josh_hawley@hawley.senate.gov",              # Josh Hawley (MO)
    "tom_cotton@cotton.senate.gov",               # Tom Cotton (AR) — uses subdomain
    "john_cornyn@cornyn.senate.gov",              # John Cornyn (TX) — uses subdomain
    "mike_lee@lee.senate.gov",                    # Mike Lee (UT) — uses subdomain
    "marsha_blackburn@blackburn.senate.gov",      # Marsha Blackburn (TN) — uses subdomain

    # ------------------------------------------------------------------
    # House Oversight Committee
    # ------------------------------------------------------------------

    # Republicans
    "james.comer@mail.house.gov",                 # James Comer (KY-01)
    "byron.donalds@mail.house.gov",               # Byron Donalds (FL-19)
    "lauren.boebert@mail.house.gov",              # Lauren Boebert (CO-03)
    "paul.gosar@mail.house.gov",                  # Paul Gosar (AZ-09)
    "scott.perry@mail.house.gov",                 # Scott Perry (PA-10)

    # Democrats
    "jamie.raskin@mail.house.gov",                # Jamie Raskin (MD-08)
    "jared.moskowitz@mail.house.gov",             # Jared Moskowitz (FL-23)
    "kweisi.mfume@mail.house.gov",                # Kweisi Mfume (MD-07)
    "katie.porter@mail.house.gov",                # Katie Porter (CA-47)

]

# ---------------------------------------------------------------------------
# Core send logic
# ---------------------------------------------------------------------------

def build_message(sender: str, recipient: str) -> MIMEMultipart:
    msg = MIMEMultipart("alternative")
    msg["Subject"] = SUBJECT
    msg["From"] = sender
    msg["To"] = recipient
    msg.attach(MIMEText(BODY, "plain"))
    return msg


def send_emails(sender: str, app_password: str, dry_run: bool = False) -> None:
    total = len(CONGRESSIONAL_EMAILS)
    sent = 0
    failed = 0
    skipped = 0

    print(f"\n{'DRY RUN — ' if dry_run else ''}Preparing to send to {total} addresses.\n")

    if not dry_run:
        try:
            server = smtplib.SMTP(SMTP_HOST, SMTP_PORT)
            server.ehlo()
            server.starttls()
            server.login(sender, app_password)
            print("SMTP connection established.\n")
        except smtplib.SMTPAuthenticationError:
            print(
                "ERROR: Gmail rejected the login. Make sure you are using an App Password,\n"
                "not your regular Gmail password. Generate one at:\n"
                "  Google Account > Security > 2-Step Verification > App Passwords\n"
            )
            sys.exit(1)
        except Exception as exc:
            print(f"ERROR: Could not connect to Gmail SMTP: {exc}")
            sys.exit(1)

    for idx, recipient in enumerate(CONGRESSIONAL_EMAILS, start=1):
        label = f"[{idx:>3}/{total}]"

        if dry_run:
            print(f"{label} DRY RUN — would send to: {recipient}")
            skipped += 1
            continue

        try:
            msg = build_message(sender, recipient)
            server.sendmail(sender, recipient, msg.as_string())
            print(f"{label} Sent    -> {recipient}")
            sent += 1
        except Exception as exc:
            print(f"{label} FAILED  -> {recipient}  ({exc})")
            failed += 1

        if idx < total:
            time.sleep(DELAY_BETWEEN_SENDS)

    if not dry_run:
        try:
            server.quit()
        except Exception:
            pass

    # Summary
    print("\n" + "=" * 50)
    if dry_run:
        print(f"DRY RUN complete. {skipped} emails would have been sent.")
    else:
        print(f"Done.  Sent: {sent}   Failed: {failed}   Total: {total}")
    print("=" * 50 + "\n")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main() -> None:
    dry_run = "--dry-run" in sys.argv

    print("=" * 50)
    print("  For Sale Documentary — Congressional Mailer")
    print("=" * 50)

    if dry_run:
        print("\nDRY RUN MODE — no emails will actually be sent.\n")
        sender = "example@gmail.com"
        app_password = "not-needed-in-dry-run"
    else:
        print(
            "\nYou need a Gmail App Password (NOT your regular password).\n"
            "Generate one at: Google Account > Security > 2-Step Verification > App Passwords\n"
        )
        sender = input("Your Gmail address: ").strip()
        app_password = getpass.getpass("App password (input hidden): ").strip()

        if not sender or not app_password:
            print("ERROR: Gmail address and app password are required.")
            sys.exit(1)

    send_emails(sender, app_password, dry_run=dry_run)


if __name__ == "__main__":
    main()
