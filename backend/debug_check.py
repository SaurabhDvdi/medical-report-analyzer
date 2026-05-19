# ─────────────────────────────────────────────────────────────────────────────
# Run this from your backend directory to diagnose the empty data issue:
#   python debug_check.py
# ─────────────────────────────────────────────────────────────────────────────

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database import SessionLocal
from models import Report, LabValue, User

db = SessionLocal()

print("\n" + "="*60)
print("DIAGNOSTIC REPORT")
print("="*60)

# ── 1. All users ──────────────────────────────────────────────
users = db.query(User).all()
print(f"\n[1] Users in DB: {len(users)}")
for u in users:
    print(f"    id={u.id}  email={u.email}  role={u.role}")

# ── 2. All reports ────────────────────────────────────────────
reports = db.query(Report).all()
print(f"\n[2] Reports in DB: {len(reports)}")
for r in reports:
    print(f"    id={r.id}  user_id={r.user_id}  type={getattr(r,'report_type','N/A')}  "
          f"ocr_status={getattr(r,'ocr_status','N/A')}  "
          f"upload_date={getattr(r,'upload_date','N/A')}")

# ── 3. All lab values ─────────────────────────────────────────
lab_values = db.query(LabValue).all()
print(f"\n[3] LabValue rows in DB: {len(lab_values)}")
if lab_values:
    for lv in lab_values[:10]:   # show first 10
        print(f"    report_id={lv.report_id}  param={lv.parameter_name}  "
              f"value={lv.value}  unit={lv.unit}  abnormal={lv.is_abnormal}")
else:
    print("    *** NO LAB VALUES FOUND — this is the root cause ***")
    print("    Reports were uploaded but OCR/extraction did not populate LabValue.")

# ── 4. Report vs LabValue join check ─────────────────────────
print(f"\n[4] Reports that HAVE lab values:")
report_ids_with_labs = {lv.report_id for lv in lab_values}
for r in reports:
    has = r.id in report_ids_with_labs
    print(f"    report_id={r.id}  has_lab_values={has}  "
          f"ocr_status={getattr(r,'ocr_status','N/A')}")

# ── 5. Likely cause diagnosis ─────────────────────────────────
print("\n[5] Diagnosis:")
if len(reports) > 0 and len(lab_values) == 0:
    print("    CAUSE: OCR ran but the extractor.py / report_parser.py")
    print("    did not produce any LabValue rows.")
    print("    → Check ocr_status on each report above.")
    print("    → If ocr_status='completed' but no LabValues exist,")
    print("      the NLP/extraction step failed silently.")
    print("    → If ocr_status='pending' or 'failed', OCR itself failed.")
elif len(reports) == 0:
    print("    CAUSE: No reports found for any user.")
elif len(lab_values) > 0 and len(report_ids_with_labs) == 0:
    print("    CAUSE: LabValues exist but report_id foreign key is broken.")
else:
    print("    Data looks present. Check user_id filtering in endpoints.")

db.close()
print("\n" + "="*60 + "\n")