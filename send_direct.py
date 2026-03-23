"""
Direct SMTP delivery to House of Representatives mail servers.
Senate does not accept inbound SMTP — they use web forms only.

No email account needed — connects directly to House mail servers.
"""

import smtplib
import sys
import time
import socket
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

SENDER = "forsaledoc@forsale-documentary.org"
SENDER_NAME = "For Sale Documentary"

# House MX servers (from nslookup)
HOUSE_MX = [
    "mxa-0018d802.gslb.pphosted.com",
    "mxb-0018d802.gslb.pphosted.com",
]

SUBJECT = "Free Documentary on Money in Politics - Sourced from Congressional Records"

BODY_HTML = """\
<html><body style="font-family: Georgia, serif; line-height: 1.6; color: #222; max-width: 600px;">
<p>Dear Member of Congress,</p>

<p>I am writing to share <strong>"For Sale,"</strong> a free, open-source interactive documentary
that traces the influence of money on American governance &mdash; from war profiteering
to cryptocurrency PAC spending to presidential pardons.</p>

<p>The documentary is sourced entirely from public records including:</p>
<ul>
<li>C-SPAN hearing transcripts from Senate Banking and House Financial Services</li>
<li>Department of Justice press releases and court filings</li>
<li>SEC and CFTC enforcement actions</li>
<li>FEC campaign finance disclosures</li>
</ul>

<p>It includes direct quotes from congressional hearings and is presented
without editorial bias &mdash; the public record speaks for itself.</p>

<p><strong>View it here:</strong>
<a href="https://samplerdan-byte.github.io/for-sale-documentary/">
https://samplerdan-byte.github.io/for-sale-documentary/</a></p>

<p><strong>Source code:</strong>
<a href="https://github.com/samplerdan-byte/for-sale-documentary">
https://github.com/samplerdan-byte/for-sale-documentary</a></p>

<p>This documentary is free, contains no advertising, and is published as
open-source software. It was created as a public service.</p>

<p>Respectfully,<br>A Concerned Citizen</p>
</body></html>
"""

BODY_TEXT = """Dear Member of Congress,

I am writing to share "For Sale," a free, open-source interactive documentary
that traces the influence of money on American governance - from war profiteering
to cryptocurrency PAC spending to presidential pardons.

The documentary is sourced entirely from public records including:
- C-SPAN hearing transcripts from Senate Banking and House Financial Services
- Department of Justice press releases and court filings
- SEC and CFTC enforcement actions
- FEC campaign finance disclosures

It includes direct quotes from congressional hearings and is presented
without editorial bias - the public record speaks for itself.

View it here: https://samplerdan-byte.github.io/for-sale-documentary/
Source code: https://github.com/samplerdan-byte/for-sale-documentary

This documentary is free, contains no advertising, and is published as
open-source software. It was created as a public service.

Respectfully,
A Concerned Citizen
"""

# House Financial Services + House Oversight committee members
# All use: firstname.lastname@mail.house.gov
HOUSE_RECIPIENTS = [
    # House Financial Services Committee
    "maxine.waters@mail.house.gov",
    "brad.sherman@mail.house.gov",
    "al.green@mail.house.gov",
    "ann.wagner@mail.house.gov",
    "andy.barr@mail.house.gov",
    "bill.huizenga@mail.house.gov",
    "french.hill@mail.house.gov",
    "warren.davidson@mail.house.gov",
    "bryan.steil@mail.house.gov",
    "ritchie.torres@mail.house.gov",
    "ayanna.pressley@mail.house.gov",
    "rashida.tlaib@mail.house.gov",
    "alexandria.ocasio-cortez@mail.house.gov",
    "nikema.williams@mail.house.gov",
    "wiley.nickel@mail.house.gov",
    # House Oversight Committee
    "jamie.raskin@mail.house.gov",
    "byron.donalds@mail.house.gov",
    "scott.perry@mail.house.gov",
    "jared.moskowitz@mail.house.gov",
    "kweisi.mfume@mail.house.gov",
    # House Judiciary
    "jerry.nadler@mail.house.gov",
    "jim.jordan@mail.house.gov",
    "sheila.jackson.lee@mail.house.gov",
    "zoe.lofgren@mail.house.gov",
    "hank.johnson@mail.house.gov",
    "eric.swalwell@mail.house.gov",
    "ted.lieu@mail.house.gov",
    "pramila.jayapal@mail.house.gov",
]


def send_email(recipient, dry_run=False):
    """Send email directly to House mail server."""
    if dry_run:
        print(f"  [DRY RUN] Would send to: {recipient}")
        return True

    msg = MIMEMultipart('alternative')
    msg['From'] = f"{SENDER_NAME} <{SENDER}>"
    msg['To'] = recipient
    msg['Subject'] = SUBJECT

    msg.attach(MIMEText(BODY_TEXT, 'plain'))
    msg.attach(MIMEText(BODY_HTML, 'html'))

    for mx in HOUSE_MX:
        try:
            with smtplib.SMTP(mx, 25, timeout=30) as smtp:
                smtp.ehlo('forsale-documentary.org')
                try:
                    smtp.starttls()
                    smtp.ehlo('forsale-documentary.org')
                except:
                    pass
                smtp.sendmail(SENDER, recipient, msg.as_string())
                print(f"  SENT: {recipient} (via {mx})")
                return True
        except smtplib.SMTPRecipientsRefused as e:
            print(f"  REJECTED: {recipient} - {e}")
            return False
        except Exception as e:
            err = str(e)
            if len(err) > 100:
                err = err[:100] + "..."
            print(f"  Failed via {mx}: {err}")
            continue

    print(f"  FAILED: All MX servers rejected {recipient}")
    return False


def main():
    dry_run = '--dry-run' in sys.argv

    print("=" * 60)
    print("FOR SALE - Congressional Email Campaign")
    print("=" * 60)
    print(f"Recipients: {len(HOUSE_RECIPIENTS)} House members")
    print(f"Mode: {'DRY RUN' if dry_run else 'LIVE SEND'}")
    print(f"From: {SENDER}")
    print(f"MX Servers: {', '.join(HOUSE_MX)}")
    print("=" * 60)
    print()
    print("NOTE: Senate uses web forms only (no SMTP).")
    print("Senate contact forms are listed in promotion_kit_2026-03-20.md")
    print()

    if not dry_run:
        confirm = input("Type 'SEND' to confirm: ").strip()
        if confirm != 'SEND':
            print("Aborted.")
            return

    sent = 0
    failed = 0

    for i, recipient in enumerate(HOUSE_RECIPIENTS, 1):
        print(f"\n[{i}/{len(HOUSE_RECIPIENTS)}] {recipient}")
        if send_email(recipient, dry_run):
            sent += 1
        else:
            failed += 1

        if not dry_run and i < len(HOUSE_RECIPIENTS):
            time.sleep(3)

    print("\n" + "=" * 60)
    print(f"DONE. Sent: {sent}  Failed: {failed}  Total: {len(HOUSE_RECIPIENTS)}")
    print("=" * 60)


if __name__ == '__main__':
    main()
