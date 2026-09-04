"""
Controlled Medical Parameter Ontology for Medical Report Analyzer.
Maps canonical lab parameter names to aliases, OCR variants, acceptable/canonical units,
sections, and value-domain min/max plausibility constraints.
"""

from typing import Dict, Any, List, Optional

LAB_ONTOLOGY: Dict[str, Dict[str, Any]] = {
    # ----------------------------------------------------
    # CBC / HAEMATOLOGY
    # ----------------------------------------------------
    "RBC": {
        "canonical_name": "RBC",
        "category": "HAEMATOLOGY",
        "aliases": ["RBC", "RED BLOOD CELL", "RED BLOOD CELLS", "RED BLOOD CELL COUNT", "R.B.C", "RBC COUNT"],
        "ocr_variants": ["RBC", "R.B.C", "RB C", "R8C"],
        "acceptable_units": ["M", "million/uL", "million/µL", "10^6/uL", "10^6/µL", "x10^6/ul", "x10^6/µl", "10*6/ul", "/cumm", "million/cmm", "million/cumm"],
        "canonical_unit": "million/µL",
        "sections": ["HAEMATOLOGY", "HEMATOLOGY", "CBC", "COMPLETE BLOOD COUNT"],
        "value_constraints": {"min": 0.5, "max": 12.0}
    },
    "WBC": {
        "canonical_name": "WBC",
        "category": "HAEMATOLOGY",
        "aliases": ["WBC", "WHITE BLOOD CELL", "WHITE BLOOD CELLS", "WHITE BLOOD CELL COUNT", "TOTAL LEUKOCYTE COUNT", "TLC", "WBC COUNT", "TOTAL WBC COUNT"],
        "ocr_variants": ["WBC", "W.B.C", "TLC", "T.L.C"],
        "acceptable_units": ["10^3/uL", "10^3/µL", "x10^3/ul", "/cumm", "/cmm", "cells/cumm", "cells/cmm", "thou/uL", "k/uL"],
        "canonical_unit": "10^3/µL",
        "sections": ["HAEMATOLOGY", "HEMATOLOGY", "CBC", "COMPLETE BLOOD COUNT"],
        "value_constraints": {"min": 0.1, "max": 250000.0}
    },
    "TLC": {
        "canonical_name": "TLC",
        "category": "HAEMATOLOGY",
        "aliases": ["TLC", "TOTAL LEUKOCYTE COUNT", "TOTAL LEUCOCYTE COUNT"],
        "ocr_variants": ["TLC", "T.L.C", "1LC"],
        "acceptable_units": ["10^3/uL", "10^3/µL", "x10^3/ul", "/cumm", "cells/cumm", "thou/uL", "k/uL"],
        "canonical_unit": "10^3/µL",
        "sections": ["HAEMATOLOGY", "HEMATOLOGY", "CBC", "COMPLETE BLOOD COUNT"],
        "value_constraints": {"min": 0.1, "max": 250.0}
    },
    "HGB": {
        "canonical_name": "Haemoglobin",
        "category": "HAEMATOLOGY",
        "aliases": ["HGB", "HB", "HEMOGLOBIN", "HAEMOGLOBIN"],
        "ocr_variants": ["HGB", "HB", "H.B", "HG B"],
        "acceptable_units": ["g/dL", "gm/dL", "g/L", "gm%"],
        "canonical_unit": "g/dL",
        "sections": ["HAEMATOLOGY", "HEMATOLOGY", "CBC", "COMPLETE BLOOD COUNT"],
        "value_constraints": {"min": 1.0, "max": 30.0}
    },
    "HCT": {
        "canonical_name": "HCT",
        "category": "HAEMATOLOGY",
        "aliases": ["HCT", "HEMATOCRIT", "HAEMATOCRIT", "PACKED CELL VOLUME", "PCV"],
        "ocr_variants": ["HCT", "H.C.T", "PCV", "P.C.V"],
        "acceptable_units": ["%", "vol%"],
        "canonical_unit": "%",
        "sections": ["HAEMATOLOGY", "HEMATOLOGY", "CBC", "COMPLETE BLOOD COUNT"],
        "value_constraints": {"min": 5.0, "max": 75.0}
    },
    "MCV": {
        "canonical_name": "MCV",
        "category": "HAEMATOLOGY",
        "aliases": ["MCV", "MEAN CORPUSCULAR VOLUME", "MEAN CELL VOLUME"],
        "ocr_variants": ["MCV", "M.C.V"],
        "acceptable_units": ["fL", "fl"],
        "canonical_unit": "fL",
        "sections": ["HAEMATOLOGY", "HEMATOLOGY", "CBC", "COMPLETE BLOOD COUNT"],
        "value_constraints": {"min": 30.0, "max": 150.0}
    },
    "MCH": {
        "canonical_name": "MCH",
        "category": "HAEMATOLOGY",
        "aliases": ["MCH", "MEAN CORPUSCULAR HEMOGLOBIN", "MEAN CELL HEMOGLOBIN"],
        "ocr_variants": ["MCH", "M.C.H"],
        "acceptable_units": ["pg"],
        "canonical_unit": "pg",
        "sections": ["HAEMATOLOGY", "HEMATOLOGY", "CBC", "COMPLETE BLOOD COUNT"],
        "value_constraints": {"min": 10.0, "max": 60.0}
    },
    "MCHC": {
        "canonical_name": "MCHC",
        "category": "HAEMATOLOGY",
        "aliases": ["MCHC", "MEAN CORPUSCULAR HEMOGLOBIN CONCENTRATION", "MEAN CELL HEMOGLOBIN CONCENTRATION"],
        "ocr_variants": ["MCHC", "M.C.H.C"],
        "acceptable_units": ["g/dL", "gm/dL", "%"],
        "canonical_unit": "g/dL",
        "sections": ["HAEMATOLOGY", "HEMATOLOGY", "CBC", "COMPLETE BLOOD COUNT"],
        "value_constraints": {"min": 15.0, "max": 50.0}
    },
    "RDW-SD": {
        "canonical_name": "RDW-SD",
        "category": "HAEMATOLOGY",
        "aliases": ["RDW-SD", "RDW SD", "RED CELL DISTRIBUTION WIDTH - SD"],
        "ocr_variants": ["RDW-SD", "RDW SD"],
        "acceptable_units": ["fL", "fl"],
        "canonical_unit": "fL",
        "sections": ["HAEMATOLOGY", "HEMATOLOGY", "CBC", "COMPLETE BLOOD COUNT"],
        "value_constraints": {"min": 10.0, "max": 150.0}
    },
    "RDW-CV": {
        "canonical_name": "RDW-CV",
        "category": "HAEMATOLOGY",
        "aliases": ["RDW-CV", "RDW CV", "RED CELL DISTRIBUTION WIDTH - CV", "RDW"],
        "ocr_variants": ["RDW-CV", "RDW CV", "RDW"],
        "acceptable_units": ["%"],
        "canonical_unit": "%",
        "sections": ["HAEMATOLOGY", "HEMATOLOGY", "CBC", "COMPLETE BLOOD COUNT"],
        "value_constraints": {"min": 5.0, "max": 50.0}
    },
    "PLT": {
        "canonical_name": "Platelet Count",
        "category": "HAEMATOLOGY",
        "aliases": ["PLT", "PLATELET", "PLATELET COUNT", "PLATELETS"],
        "ocr_variants": ["PLT", "PLATELET", "PLATELETS"],
        "acceptable_units": ["10^3/uL", "10^3/µL", "thou/uL", "lakhs/cumm", "lakh/cumm", "/cumm", "/cmm", "cells/cumm", "cells/cmm", "k/uL"],
        "canonical_unit": "10^3/µL",
        "sections": ["HAEMATOLOGY", "HEMATOLOGY", "CBC", "COMPLETE BLOOD COUNT"],
        "value_constraints": {"min": 5.0, "max": 2000000.0}
    },
    "PDW": {
        "canonical_name": "PDW",
        "category": "HAEMATOLOGY",
        "aliases": ["PDW", "PLATELET DISTRIBUTION WIDTH"],
        "ocr_variants": ["PDW"],
        "acceptable_units": ["fL", "fl", "%"],
        "canonical_unit": "fL",
        "sections": ["HAEMATOLOGY", "HEMATOLOGY", "CBC", "COMPLETE BLOOD COUNT"],
        "value_constraints": {"min": 1.0, "max": 40.0}
    },
    "MPV": {
        "canonical_name": "MPV",
        "category": "HAEMATOLOGY",
        "aliases": ["MPV", "MEAN PLATELET VOLUME"],
        "ocr_variants": ["MPV"],
        "acceptable_units": ["fL", "fl"],
        "canonical_unit": "fL",
        "sections": ["HAEMATOLOGY", "HEMATOLOGY", "CBC", "COMPLETE BLOOD COUNT"],
        "value_constraints": {"min": 2.0, "max": 30.0}
    },
    "P-LCR": {
        "canonical_name": "P-LCR",
        "category": "HAEMATOLOGY",
        "aliases": ["P-LCR", "PLCR", "PLATELET LARGE CELL RATIO"],
        "ocr_variants": ["P-LCR", "PLCR"],
        "acceptable_units": ["%"],
        "canonical_unit": "%",
        "sections": ["HAEMATOLOGY", "HEMATOLOGY", "CBC", "COMPLETE BLOOD COUNT"],
        "value_constraints": {"min": 1.0, "max": 90.0}
    },
    "PCT": {
        "canonical_name": "PCT",
        "category": "HAEMATOLOGY",
        "aliases": ["PCT", "PLATELETCRIT"],
        "ocr_variants": ["PCT"],
        "acceptable_units": ["%"],
        "canonical_unit": "%",
        "sections": ["HAEMATOLOGY", "HEMATOLOGY", "CBC", "COMPLETE BLOOD COUNT"],
        "value_constraints": {"min": 0.01, "max": 5.0}
    },
    "NEUT#": {
        "canonical_name": "Neutrophils (Absolute)",
        "category": "HAEMATOLOGY",
        "aliases": ["NEUT#", "NEUTROPHILS ABSOLUTE", "ABSOLUTE NEUTROPHIL COUNT", "ANC"],
        "ocr_variants": ["NEUT#", "NEUT #", "ANC"],
        "acceptable_units": ["10^3/uL", "10^3/µL", "/cumm", "thou/uL"],
        "canonical_unit": "10^3/µL",
        "sections": ["HAEMATOLOGY", "HEMATOLOGY", "CBC", "COMPLETE BLOOD COUNT"],
        "value_constraints": {"min": 0.0, "max": 100.0}
    },
    "LYMPH#": {
        "canonical_name": "Lymphocytes (Absolute)",
        "category": "HAEMATOLOGY",
        "aliases": ["LYMPH#", "LYMPHOCYTES ABSOLUTE", "ABSOLUTE LYMPHOCYTE COUNT", "ALC"],
        "ocr_variants": ["LYMPH#", "LYMPH #", "ALC"],
        "acceptable_units": ["10^3/uL", "10^3/µL", "/cumm", "thou/uL"],
        "canonical_unit": "10^3/µL",
        "sections": ["HAEMATOLOGY", "HEMATOLOGY", "CBC", "COMPLETE BLOOD COUNT"],
        "value_constraints": {"min": 0.0, "max": 100.0}
    },
    "MONO#": {
        "canonical_name": "Monocytes (Absolute)",
        "category": "HAEMATOLOGY",
        "aliases": ["MONO#", "MONOCYTES ABSOLUTE", "ABSOLUTE MONOCYTE COUNT", "AMC"],
        "ocr_variants": ["MONO#", "MONO #", "AMC"],
        "acceptable_units": ["10^3/uL", "10^3/µL", "/cumm", "thou/uL"],
        "canonical_unit": "10^3/µL",
        "sections": ["HAEMATOLOGY", "HEMATOLOGY", "CBC", "COMPLETE BLOOD COUNT"],
        "value_constraints": {"min": 0.0, "max": 50.0}
    },
    "EO#": {
        "canonical_name": "Eosinophils (Absolute)",
        "category": "HAEMATOLOGY",
        "aliases": ["EO#", "EOSINOPHILS ABSOLUTE", "ABSOLUTE EOSINOPHIL COUNT", "AEC"],
        "ocr_variants": ["EO#", "EOS#", "EO #", "AEC"],
        "acceptable_units": ["10^3/uL", "10^3/µL", "/cumm", "thou/uL"],
        "canonical_unit": "10^3/µL",
        "sections": ["HAEMATOLOGY", "HEMATOLOGY", "CBC", "COMPLETE BLOOD COUNT"],
        "value_constraints": {"min": 0.0, "max": 50.0}
    },
    "BASO#": {
        "canonical_name": "Basophils (Absolute)",
        "category": "HAEMATOLOGY",
        "aliases": ["BASO#", "BASOPHILS ABSOLUTE", "ABSOLUTE BASOPHIL COUNT", "ABC"],
        "ocr_variants": ["BASO#", "BASO #", "ABC"],
        "acceptable_units": ["10^3/uL", "10^3/µL", "/cumm", "thou/uL"],
        "canonical_unit": "10^3/µL",
        "sections": ["HAEMATOLOGY", "HEMATOLOGY", "CBC", "COMPLETE BLOOD COUNT"],
        "value_constraints": {"min": 0.0, "max": 20.0}
    },
    "NEUT%": {
        "canonical_name": "Neutrophils (%)",
        "category": "HAEMATOLOGY",
        "aliases": ["NEUT%", "NEUTROPHILS", "NEUTROPHILS %", "NEUTROPHIL PERCENTAGE"],
        "ocr_variants": ["NEUT%", "NEUTROPHILS"],
        "acceptable_units": ["%"],
        "canonical_unit": "%",
        "sections": ["HAEMATOLOGY", "HEMATOLOGY", "CBC", "COMPLETE BLOOD COUNT"],
        "value_constraints": {"min": 0.0, "max": 100.0}
    },
    "LYMPH%": {
        "canonical_name": "Lymphocytes (%)",
        "category": "HAEMATOLOGY",
        "aliases": ["LYMPH%", "LYMPHOCYTES", "LYMPHOCYTES %", "LYMPHOCYTE PERCENTAGE"],
        "ocr_variants": ["LYMPH%", "LYMPHOCYTES"],
        "acceptable_units": ["%"],
        "canonical_unit": "%",
        "sections": ["HAEMATOLOGY", "HEMATOLOGY", "CBC", "COMPLETE BLOOD COUNT"],
        "value_constraints": {"min": 0.0, "max": 100.0}
    },
    "MONO%": {
        "canonical_name": "Monocytes (%)",
        "category": "HAEMATOLOGY",
        "aliases": ["MONO%", "MONOCYTES", "MONOCYTES %", "MONOCYTE PERCENTAGE"],
        "ocr_variants": ["MONO%", "MONOCYTES"],
        "acceptable_units": ["%"],
        "canonical_unit": "%",
        "sections": ["HAEMATOLOGY", "HEMATOLOGY", "CBC", "COMPLETE BLOOD COUNT"],
        "value_constraints": {"min": 0.0, "max": 100.0}
    },
    "EO%": {
        "canonical_name": "Eosinophils (%)",
        "category": "HAEMATOLOGY",
        "aliases": ["EO%", "EOSINOPHILS", "EOSINOPHILS %", "EOSINOPHIL PERCENTAGE"],
        "ocr_variants": ["EO%", "EOSINOPHILS"],
        "acceptable_units": ["%"],
        "canonical_unit": "%",
        "sections": ["HAEMATOLOGY", "HEMATOLOGY", "CBC", "COMPLETE BLOOD COUNT"],
        "value_constraints": {"min": 0.0, "max": 100.0}
    },
    "BASO%": {
        "canonical_name": "Basophils (%)",
        "category": "HAEMATOLOGY",
        "aliases": ["BASO%", "BASOPHILS", "BASOPHILS %", "BASOPHIL PERCENTAGE"],
        "ocr_variants": ["BASO%", "BASOPHILS"],
        "acceptable_units": ["%"],
        "canonical_unit": "%",
        "sections": ["HAEMATOLOGY", "HEMATOLOGY", "CBC", "COMPLETE BLOOD COUNT"],
        "value_constraints": {"min": 0.0, "max": 100.0}
    },

    # ----------------------------------------------------
    # BLOOD GLUCOSE / DIABETES
    # ----------------------------------------------------
    "Fasting Blood Sugar": {
        "canonical_name": "Fasting Blood Sugar",
        "category": "BIOCHEMISTRY",
        "aliases": ["FASTING BLOOD SUGAR", "FASTING GLUCOSE", "FBS", "GLUCOSE FASTING", "BLOOD SUGAR FASTING"],
        "ocr_variants": ["FBS", "F.B.S"],
        "acceptable_units": ["mg/dL", "mg/dl", "mmol/L"],
        "canonical_unit": "mg/dL",
        "sections": ["BIOCHEMISTRY", "BIO CHEMISTRY", "DIABETES", "PATHOLOGY"],
        "value_constraints": {"min": 10.0, "max": 1000.0}
    },
    "Random Blood Sugar": {
        "canonical_name": "Random Blood Sugar",
        "category": "BIOCHEMISTRY",
        "aliases": ["RANDOM BLOOD SUGAR", "RANDOM GLUCOSE", "RBS", "GLUCOSE RANDOM", "BLOOD SUGAR RANDOM"],
        "ocr_variants": ["RBS", "R.B.S"],
        "acceptable_units": ["mg/dL", "mg/dl", "mmol/L"],
        "canonical_unit": "mg/dL",
        "sections": ["BIOCHEMISTRY", "BIO CHEMISTRY", "DIABETES", "PATHOLOGY"],
        "value_constraints": {"min": 10.0, "max": 1000.0}
    },
    "Post Prandial Blood Sugar": {
        "canonical_name": "Post Prandial Blood Sugar",
        "category": "BIOCHEMISTRY",
        "aliases": ["POST PRANDIAL BLOOD SUGAR", "POST PRANDIAL GLUCOSE", "PPBS", "PP GLUCOSE", "BLOOD SUGAR PP"],
        "ocr_variants": ["PPBS", "P.P.B.S"],
        "acceptable_units": ["mg/dL", "mg/dl", "mmol/L"],
        "canonical_unit": "mg/dL",
        "sections": ["BIOCHEMISTRY", "BIO CHEMISTRY", "DIABETES", "PATHOLOGY"],
        "value_constraints": {"min": 10.0, "max": 1000.0}
    },
    "HbA1c": {
        "canonical_name": "HbA1c",
        "category": "BIOCHEMISTRY",
        "aliases": ["HBA1C", "GLYCATED HEMOGLOBIN", "GLYCOSYLATED HEMOGLOBIN", "A1C"],
        "ocr_variants": ["HBA1C", "HB A1C", "A1C"],
        "acceptable_units": ["%", "mmol/mol"],
        "canonical_unit": "%",
        "sections": ["BIOCHEMISTRY", "BIO CHEMISTRY", "DIABETES", "HAEMATOLOGY"],
        "value_constraints": {"min": 2.0, "max": 25.0}
    },

    # ----------------------------------------------------
    # THYROID FUNCTION
    # ----------------------------------------------------
    "TSH": {
        "canonical_name": "TSH",
        "category": "THYROID",
        "aliases": ["TSH", "THYROID STIMULATING HORMONE", "THYROTROPIN"],
        "ocr_variants": ["TSH", "T5H", "ISH", "T.S.H"],
        "acceptable_units": ["µIU/mL", "uIU/mL", "mIU/L", "plUImL", "uIU/ml"],
        "canonical_unit": "µIU/mL",
        "sections": ["THYROID", "SEROLOGY", "ENDOCRINOLOGY", "BIOCHEMISTRY"],
        "value_constraints": {"min": 0.001, "max": 200.0}
    },
    "T3": {
        "canonical_name": "T3",
        "category": "THYROID",
        "aliases": ["T3", "TOTAL T3", "TRIIODOTHYRONINE"],
        "ocr_variants": ["T3", "T-3"],
        "acceptable_units": ["ng/dL", "ng/dl", "nmol/L"],
        "canonical_unit": "ng/dL",
        "sections": ["THYROID", "SEROLOGY", "ENDOCRINOLOGY"],
        "value_constraints": {"min": 10.0, "max": 1000.0}
    },
    "T4": {
        "canonical_name": "T4",
        "category": "THYROID",
        "aliases": ["T4", "TOTAL T4", "THYROXINE"],
        "ocr_variants": ["T4", "T-4"],
        "acceptable_units": ["µg/dL", "ug/dL", "nmol/L"],
        "canonical_unit": "µg/dL",
        "sections": ["THYROID", "SEROLOGY", "ENDOCRINOLOGY"],
        "value_constraints": {"min": 0.5, "max": 50.0}
    },
    "Free T3": {
        "canonical_name": "Free T3",
        "category": "THYROID",
        "aliases": ["FREE T3", "FT3"],
        "ocr_variants": ["FT3", "F T3"],
        "acceptable_units": ["pg/mL", "pg/ml", "pmol/L"],
        "canonical_unit": "pg/mL",
        "sections": ["THYROID", "SEROLOGY"],
        "value_constraints": {"min": 0.1, "max": 50.0}
    },
    "Free T4": {
        "canonical_name": "Free T4",
        "category": "THYROID",
        "aliases": ["FREE T4", "FT4"],
        "ocr_variants": ["FT4", "F T4"],
        "acceptable_units": ["ng/dL", "ng/dl", "pmol/L"],
        "canonical_unit": "ng/dL",
        "sections": ["THYROID", "SEROLOGY"],
        "value_constraints": {"min": 0.1, "max": 20.0}
    },

    # ----------------------------------------------------
    # INFLAMMATION
    # ----------------------------------------------------
    "ESR": {
        "canonical_name": "ESR",
        "category": "HAEMATOLOGY",
        "aliases": ["ESR", "ERYTHROCYTE SEDIMENTATION RATE"],
        "ocr_variants": ["ESR", "E.S.R"],
        "acceptable_units": ["mm", "mm/hr", "mm/1st hr"],
        "canonical_unit": "mm/hr",
        "sections": ["HAEMATOLOGY", "HEMATOLOGY", "PATHOLOGY"],
        "value_constraints": {"min": 0.0, "max": 200.0}
    },
    "CRP": {
        "canonical_name": "CRP",
        "category": "BIOCHEMISTRY",
        "aliases": ["CRP", "C-REACTIVE PROTEIN", "CRP (QUANTITATIVE)", "C REACTIVE PROTEIN"],
        "ocr_variants": ["CRP", "C.R.P"],
        "acceptable_units": ["mg/L", "mg/l", "mg/dL", "mgIL"],
        "canonical_unit": "mg/L",
        "sections": ["BIOCHEMISTRY", "SEROLOGY", "PATHOLOGY"],
        "value_constraints": {"min": 0.01, "max": 500.0}
    },

    # ----------------------------------------------------
    # LIPID PROFILE
    # ----------------------------------------------------
    "Total Cholesterol": {
        "canonical_name": "Total Cholesterol",
        "category": "LIPID PROFILE",
        "aliases": ["CHOLESTEROL", "TOTAL CHOLESTEROL", "SERUM CHOLESTEROL"],
        "ocr_variants": ["CHOLESTEROL"],
        "acceptable_units": ["mg/dL", "mg/dl", "mmol/L"],
        "canonical_unit": "mg/dL",
        "sections": ["LIPID PROFILE", "BIOCHEMISTRY"],
        "value_constraints": {"min": 20.0, "max": 1000.0}
    },
    "Triglycerides": {
        "canonical_name": "Triglycerides",
        "category": "LIPID PROFILE",
        "aliases": ["TRIGLYCERIDES", "SERUM TRIGLYCERIDES", "TRIG"],
        "ocr_variants": ["TRIGLYCERIDES", "TRIG"],
        "acceptable_units": ["mg/dL", "mg/dl", "mmol/L"],
        "canonical_unit": "mg/dL",
        "sections": ["LIPID PROFILE", "BIOCHEMISTRY"],
        "value_constraints": {"min": 10.0, "max": 3000.0}
    },
    "HDL Cholesterol": {
        "canonical_name": "HDL Cholesterol",
        "category": "LIPID PROFILE",
        "aliases": ["HDL", "HDL CHOLESTEROL", "HIGH DENSITY LIPOPROTEIN"],
        "ocr_variants": ["HDL", "H.D.L"],
        "acceptable_units": ["mg/dL", "mg/dl", "mmol/L"],
        "canonical_unit": "mg/dL",
        "sections": ["LIPID PROFILE", "BIOCHEMISTRY"],
        "value_constraints": {"min": 5.0, "max": 200.0}
    },
    "LDL Cholesterol": {
        "canonical_name": "LDL Cholesterol",
        "category": "LIPID PROFILE",
        "aliases": ["LDL", "LDL CHOLESTEROL", "LOW DENSITY LIPOPROTEIN"],
        "ocr_variants": ["LDL", "L.D.L"],
        "acceptable_units": ["mg/dL", "mg/dl", "mmol/L"],
        "canonical_unit": "mg/dL",
        "sections": ["LIPID PROFILE", "BIOCHEMISTRY"],
        "value_constraints": {"min": 5.0, "max": 500.0}
    },
    "VLDL Cholesterol": {
        "canonical_name": "VLDL Cholesterol",
        "category": "LIPID PROFILE",
        "aliases": ["VLDL", "VLDL CHOLESTEROL", "VERY LOW DENSITY LIPOPROTEIN"],
        "ocr_variants": ["VLDL"],
        "acceptable_units": ["mg/dL", "mg/dl", "mmol/L"],
        "canonical_unit": "mg/dL",
        "sections": ["LIPID PROFILE", "BIOCHEMISTRY"],
        "value_constraints": {"min": 1.0, "max": 200.0}
    },

    # ----------------------------------------------------
    # LIVER & KIDNEY FUNCTION
    # ----------------------------------------------------
    "Bilirubin Total": {
        "canonical_name": "Bilirubin Total",
        "category": "LIVER FUNCTION",
        "aliases": ["TOTAL BILIRUBIN", "BILIRUBIN TOTAL", "BILIRUBIN (TOTAL)"],
        "ocr_variants": ["BILIRUBIN TOTAL"],
        "acceptable_units": ["mg/dL", "mg/dl", "µmol/L"],
        "canonical_unit": "mg/dL",
        "sections": ["LIVER FUNCTION TEST", "LFT", "BIOCHEMISTRY"],
        "value_constraints": {"min": 0.05, "max": 50.0}
    },
    "SGOT": {
        "canonical_name": "SGOT",
        "category": "LIVER FUNCTION",
        "aliases": ["SGOT", "AST", "ASPARTATE AMINOTRANSFERASE", "SGOT / AST"],
        "ocr_variants": ["SGOT", "AST"],
        "acceptable_units": ["U/L", "IU/L", "u/l"],
        "canonical_unit": "U/L",
        "sections": ["LIVER FUNCTION TEST", "LFT", "BIOCHEMISTRY"],
        "value_constraints": {"min": 1.0, "max": 5000.0}
    },
    "SGPT": {
        "canonical_name": "SGPT",
        "category": "LIVER FUNCTION",
        "aliases": ["SGPT", "ALT", "ALANINE AMINOTRANSFERASE", "SGPT / ALT"],
        "ocr_variants": ["SGPT", "ALT"],
        "acceptable_units": ["U/L", "IU/L", "u/l"],
        "canonical_unit": "U/L",
        "sections": ["LIVER FUNCTION TEST", "LFT", "BIOCHEMISTRY"],
        "value_constraints": {"min": 1.0, "max": 5000.0}
    },
    "Urea": {
        "canonical_name": "Urea",
        "category": "KIDNEY FUNCTION",
        "aliases": ["UREA", "BLOOD UREA", "SERUM UREA", "BUN"],
        "ocr_variants": ["UREA", "BUN"],
        "acceptable_units": ["mg/dL", "mg/dl", "mmol/L"],
        "canonical_unit": "mg/dL",
        "sections": ["KIDNEY FUNCTION TEST", "KFT", "RFT", "BIOCHEMISTRY"],
        "value_constraints": {"min": 1.0, "max": 400.0}
    },
    "Creatinine": {
        "canonical_name": "Creatinine",
        "category": "KIDNEY FUNCTION",
        "aliases": ["CREATININE", "SERUM CREATININE"],
        "ocr_variants": ["CREATININE"],
        "acceptable_units": ["mg/dL", "mg/dl", "µmol/L"],
        "canonical_unit": "mg/dL",
        "sections": ["KIDNEY FUNCTION TEST", "KFT", "RFT", "BIOCHEMISTRY"],
        "value_constraints": {"min": 0.1, "max": 30.0}
    },
    "Uric Acid": {
        "canonical_name": "Uric Acid",
        "category": "KIDNEY FUNCTION",
        "aliases": ["URIC ACID", "SERUM URIC ACID"],
        "ocr_variants": ["URIC ACID"],
        "acceptable_units": ["mg/dL", "mg/dl", "µmol/L"],
        "canonical_unit": "mg/dL",
        "sections": ["KIDNEY FUNCTION TEST", "KFT", "BIOCHEMISTRY"],
        "value_constraints": {"min": 0.5, "max": 25.0}
    }
}


def find_ontology_match(param_candidate: str) -> Optional[Dict[str, Any]]:
    """
    Search ontology for an exact canonical key match first, then aliases, then OCR variants.
    Returns dict with canonical_name, category, definition, and match_type if found.
    """
    if not param_candidate:
        return None

    clean = param_candidate.strip().upper()

    # Pass 1: Direct canonical key or canonical_name match
    for key, spec in LAB_ONTOLOGY.items():
        if clean == key.upper() or clean == spec["canonical_name"].upper():
            return {
                "key": key,
                "canonical_name": spec["canonical_name"],
                "category": spec["category"],
                "spec": spec,
                "match_type": "EXACT"
            }

    # Pass 2: Aliases match
    for key, spec in LAB_ONTOLOGY.items():
        for alias in spec.get("aliases", []):
            if clean == alias.upper():
                return {
                    "key": key,
                    "canonical_name": spec["canonical_name"],
                    "category": spec["category"],
                    "spec": spec,
                    "match_type": "ALIAS"
                }

    # Pass 3: OCR variants match
    for key, spec in LAB_ONTOLOGY.items():
        for variant in spec.get("ocr_variants", []):
            if clean == variant.upper():
                return {
                    "key": key,
                    "canonical_name": spec["canonical_name"],
                    "category": spec["category"],
                    "spec": spec,
                    "match_type": "OCR_VARIANT"
                }

    return None
