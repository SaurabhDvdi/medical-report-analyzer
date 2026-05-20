import sys, os, traceback
POPPLER_PATH = r"C:\poppler\poppler-26.02.0\Library\bin"
if os.path.isdir(POPPLER_PATH):
    os.environ["PATH"] = POPPLER_PATH + os.pathsep + os.environ.get("PATH", "")
    print(f"✅ Poppler path set")
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from datetime import datetime
from database import SessionLocal
from models import Report, LabValue, ReportCategory
from services.ocr_service import OCRService
from services.nlp_service import NLPService
from services.extractor import Extractor
from services.normalizer import Normalizer
from services.report_parser import ReportParser

db          = SessionLocal()
ocr_service = OCRService()
nlp_service = NLPService()
extractor   = Extractor()
normalizer  = Normalizer()
report_parser = ReportParser()


def process_one(report):
    print(f"\n{'='*60}")
    print(f"Processing report {report.id}: {report.file_path}")

    if not os.path.exists(report.file_path):
        print(f"  ❌ File not found — marking failed")
        report.ocr_status = "failed"
        db.commit()
        return

    # ── OCR ──────────────────────────────────────────────────────────────────
    print("  ⏳ Running OCR...")
    lines = ocr_service.extract_text(report.file_path)   # returns List[str]
    print(f"  ✅ {len(lines)} lines extracted")
    if not lines:
        report.ocr_status = "failed"
        db.commit()
        return

    report.extracted_text = "\n".join(lines)
    db.commit()

    # ── NLP ──────────────────────────────────────────────────────────────────
    try:
        report.ai_summary = nlp_service.generate_summary(lines)
        db.commit()
        print("  ✅ NLP summary done")
    except Exception as e:
        print(f"  ⚠️  NLP skipped: {e}")

    # ── Extract → Normalise → Parse ──────────────────────────────────────────
    print("  ⏳ Running extractor...")
    extracted_data = extractor.extract(lines)          # pass list directly
    print(f"  ✅ Extractor raw output keys: {list(extracted_data.keys()) if isinstance(extracted_data, dict) else type(extracted_data)}")

    normalized_data = normalizer.normalize(extracted_data)
    print(f"  ✅ Normaliser output keys: {list(normalized_data.keys()) if isinstance(normalized_data, dict) else type(normalized_data)}")

    # Save report_date
    report_info = normalized_data.get("report_info", {})
    if report_info.get("report_date"):
        try:
            report.report_date = datetime.fromisoformat(report_info["report_date"]).date()
            db.commit()
        except Exception:
            pass

    parsed_data = report_parser.parse(normalized_data)
    print(f"  ✅ Parser output keys: {list(parsed_data.keys()) if isinstance(parsed_data, dict) else type(parsed_data)}")
    print(f"  raw_tests sample: {normalized_data.get('raw_tests', [])[:3]}")
    print(f"  test_results sample: {parsed_data.get('test_results', [])[:3]}")

    # ── Category ─────────────────────────────────────────────────────────────
    if parsed_data.get("category"):
        cat_name = parsed_data["category"]
        cat = db.query(ReportCategory).filter(ReportCategory.name == cat_name).first()
        if not cat:
            cat = ReportCategory(name=cat_name, description=f"Auto: {cat_name}")
            db.add(cat)
            db.commit()
        report.category_id = cat.id
        db.commit()

    # ── Save LabValues ────────────────────────────────────────────────────────
    lab_value_list = (
        parsed_data.get("test_results")
        or parsed_data.get("lab_values")
        or parsed_data.get("results")
        or normalized_data.get("raw_tests")
        or normalized_data.get("lab_values")
        or extracted_data.get("raw_tests")
        or []
    )

    print(f"  ⏳ Lab values found: {len(lab_value_list)}")

    # Show raw items so we can debug key names if needed
    for i, item in enumerate(lab_value_list[:3]):
        print(f"     Sample [{i}]: {item}")

    # test_results contains panels → each panel has a measurements list
    SKIP_WORDS = {
        'name', 'registration on', 'approved on', 'printed on',
        'process at', 'page', 'good control', 'borderline high',
        'high', 'low', 'desirable', 'normal', 'optimal'
    }

    saved = 0
    for panel in lab_value_list:
        if not isinstance(panel, dict):
            continue
        measurements = panel.get('measurements', [])
        for item in measurements:
            if not isinstance(item, dict):
                continue

            param_name = item.get('test_description')
            value      = item.get('result')
            unit       = item.get('unit')

            if not param_name or value is None:
                continue
            if unit is None:                              # skip metadata rows
                continue
            if param_name.lower().strip() in SKIP_WORDS: # skip label rows
                continue
            if len(param_name) > 60:                     # skip long note rows
                continue

            status      = item.get('status', 'Unknown')
            is_abnormal = status.lower() in ('high', 'low', 'abnormal', 'critical')

            lv = LabValue(
                report_id       = report.id,
                parameter_name  = str(param_name).strip(),
                value           = value,
                unit            = str(unit).strip(),
                reference_range = str(item.get('ref_range') or '').strip(),
                is_abnormal     = is_abnormal,
            )
            db.add(lv)
            saved += 1

    report.ocr_status = "completed"
    db.commit()
    print(f"  ✅ Saved {saved} LabValue rows — status: completed")


# ── Main ──────────────────────────────────────────────────────────────────────
stuck = db.query(Report).filter(
    Report.ocr_status.in_(["processing", "pending", "failed"])
).all()

print(f"Found {len(stuck)} report(s) to reprocess")

for report in stuck:
    try:
        process_one(report)
    except Exception as e:
        print(f"  ❌ CRASH on report {report.id}: {e}")
        traceback.print_exc()
        db.rollback()
        try:
            r = db.query(Report).filter(Report.id == report.id).first()
            if r:
                r.ocr_status = "failed"
                db.commit()
        except Exception:
            pass

db.close()
print(f"\n{'='*60}")
print("Done. Run: python debug_check.py  to verify.")
print(f"{'='*60}\n")


# Reset command (if you want to reset all again):
# python -c "
# import sys; sys.path.append('.')
# from database import SessionLocal
# from models import Report
# db = SessionLocal()
# db.query(Report).update({'ocr_status': 'pending'})
# db.commit()
# db.close()
# print('Reset done')
# "
