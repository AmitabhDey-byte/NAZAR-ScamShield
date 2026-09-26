"""One-time cleanup for exact records created by NAZAR's retired demo seeder."""
from pathlib import Path
import sqlite3

db_path = Path(__file__).resolve().parents[1] / "nazar.db"
with sqlite3.connect(db_path) as connection:
    demo_message = "Your electricity connection will be disconnected tonight. Pay ₹4980 immediately at ramesh123@oksbi using https://electric-bill-secure.xyz"
    demo_analysis_ids = [row[0] for row in connection.execute("SELECT id FROM analysis_requests WHERE input_text = ?", (demo_message,))]
    if demo_analysis_ids:
        placeholders = ",".join("?" for _ in demo_analysis_ids)
        demo_session_ids = [row[0] for row in connection.execute(f"SELECT id FROM honeypot_sessions WHERE analysis_id IN ({placeholders})", demo_analysis_ids)]
        if demo_session_ids:
            session_placeholders = ",".join("?" for _ in demo_session_ids)
            connection.execute(f"DELETE FROM honeypot_messages WHERE session_id IN ({session_placeholders})", demo_session_ids)
            connection.execute(f"DELETE FROM honeypot_sessions WHERE id IN ({session_placeholders})", demo_session_ids)
        connection.execute(f"DELETE FROM analysis_requests WHERE id IN ({placeholders})", demo_analysis_ids)
    connection.execute("DELETE FROM campaign_indicators WHERE campaign_id IN ('campaign-17', 'campaign-23')")
    connection.execute("DELETE FROM threat_edges WHERE source_id LIKE 'ind-%' OR target_id LIKE 'ind-%'")
    connection.execute("DELETE FROM campaigns WHERE id IN ('campaign-17', 'campaign-23')")
    connection.execute("DELETE FROM threat_indicators WHERE id LIKE 'ind-%'")
    connection.execute("""
        DELETE FROM scam_reports WHERE
        (phone_number = '+91 98765 43210' AND upi_id = 'ramesh123@oksbi' AND url = 'https://electric-bill-secure.xyz') OR
        (phone_number = '+91 91234 56780' AND upi_id = 'ramesh123@oksbi' AND message = 'Outstanding power bill. Pay immediately') OR
        (upi_id = 'kycdesk@okaxis' AND url = 'https://sbi-kyc-secure.top')
    """)
    connection.execute("DELETE FROM scam_reports WHERE COALESCE(phone_number, '') = '' AND COALESCE(upi_id, '') = '' AND COALESCE(url, '') = '' AND TRIM(message) = ''")
    connection.commit()
    print("Removed retired demo campaigns, indicators, and reports.")
