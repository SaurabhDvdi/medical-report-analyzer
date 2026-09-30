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
        "aliases": ["RBC", "RBC'S", "RBCS", "RED BLOOD CELL", "RED BLOOD CELLS", "RED BLOOD CELL COUNT", "R.B.C", "RBC COUNT"],
        "ocr_variants": ["RBC", "R.B.C", "RB C", "R8C"],
        "acceptable_units": ["M", "million/uL", "million/µL", "10^6/uL", "10^6/µL", "x10^6/ul", "x10^6/µl", "10*6/ul", "/cumm", "million/cmm", "million/cumm", "mil/cmm", "mil/cumm"],
        "canonical_unit": "million/µL",
        "sections": ["HAEMATOLOGY", "HEMATOLOGY", "CBC", "COMPLETE BLOOD COUNT", "COMPLETE BLOOD PICTURE", "PATHOLOGY"],
        "value_constraints": {"min": 0.5, "max": 12.0}
    },
    "WBC": {
        "canonical_name": "WBC",
        "category": "HAEMATOLOGY",
        "aliases": ["WBC", "WBC'S", "WBCS", "WHITE BLOOD CELL", "WHITE BLOOD CELLS", "WHITE BLOOD CELL COUNT", "TOTAL LEUKOCYTE COUNT", "TLC", "WBC COUNT", "TOTAL WBC COUNT"],
        "ocr_variants": ["WBC", "W.B.C", "TLC", "T.L.C"],
        "acceptable_units": ["10^3/uL", "10^3/µL", "x10^3/ul", "/cumm", "/cmm", "cells/cumm", "cells/cmm", "thou/uL", "k/uL"],
        "canonical_unit": "10^3/µL",
        "sections": ["HAEMATOLOGY", "HEMATOLOGY", "CBC", "COMPLETE BLOOD COUNT", "COMPLETE BLOOD PICTURE", "PATHOLOGY"],
        "value_constraints": {"min": 0.1, "max": 250000.0}
    },
    "TLC": {
        "canonical_name": "TLC",
        "category": "HAEMATOLOGY",
        "aliases": ["TLC", "TOTAL LEUKOCYTE COUNT", "TOTAL LEUCOCYTE COUNT"],
        "ocr_variants": ["TLC", "T.L.C", "1LC"],
        "acceptable_units": ["10^3/uL", "10^3/µL", "x10^3/ul", "/cumm", "cells/cumm", "thou/uL", "k/uL"],
        "canonical_unit": "10^3/µL",
        "sections": ["HAEMATOLOGY", "HEMATOLOGY", "CBC", "COMPLETE BLOOD COUNT", "COMPLETE BLOOD PICTURE", "PATHOLOGY"],
        "value_constraints": {"min": 0.1, "max": 250.0}
    },
    "HGB": {
        "canonical_name": "Haemoglobin",
        "category": "HAEMATOLOGY",
        "aliases": ["HGB", "HB", "HEMOGLOBIN", "HAEMOGLOBIN"],
        "ocr_variants": ["HGB", "HB", "H.B", "HG B"],
        "acceptable_units": ["g/dL", "gm/dL", "g/L", "gm%", "gms", "gm", "gms/dL", "gms/dl"],
        "canonical_unit": "g/dL",
        "sections": ["HAEMATOLOGY", "HEMATOLOGY", "CBC", "COMPLETE BLOOD COUNT", "COMPLETE BLOOD PICTURE", "PATHOLOGY"],
        "value_constraints": {"min": 1.0, "max": 30.0}
    },
    "HCT": {
        "canonical_name": "HCT",
        "category": "HAEMATOLOGY",
        "aliases": ["HCT", "HEMATOCRIT", "HAEMATOCRIT", "PACKED CELL VOLUME", "PCV"],
        "ocr_variants": ["HCT", "H.C.T", "PCV", "P.C.V"],
        "acceptable_units": ["%", "vol%"],
        "canonical_unit": "%",
        "sections": ["HAEMATOLOGY", "HEMATOLOGY", "CBC", "COMPLETE BLOOD COUNT", "COMPLETE BLOOD PICTURE", "PATHOLOGY"],
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
        "acceptable_units": ["g/dL", "gm/dL", "%", "gms/dL", "gms/dl", "g/dl"],
        "canonical_unit": "g/dL",
        "sections": ["HAEMATOLOGY", "HEMATOLOGY", "CBC", "COMPLETE BLOOD COUNT", "COMPLETE BLOOD PICTURE", "PATHOLOGY"],
        "value_constraints": {"min": 15.0, "max": 50.0}
    },
    "RDW-SD": {
        "canonical_name": "RDW-SD",
        "category": "HAEMATOLOGY",
        "aliases": ["RDW-SD", "RDW SD", "RED CELL DISTRIBUTION WIDTH - SD"],
        "ocr_variants": ["RDW-SD", "RDW SD"],
        "acceptable_units": ["fL", "fl"],
        "canonical_unit": "fL",
        "sections": ["HAEMATOLOGY", "HEMATOLOGY", "CBC", "COMPLETE BLOOD COUNT", "COMPLETE BLOOD PICTURE", "PATHOLOGY"],
        "value_constraints": {"min": 10.0, "max": 150.0}
    },
    "RDW-CV": {
        "canonical_name": "RDW-CV",
        "category": "HAEMATOLOGY",
        "aliases": ["RDW-CV", "RDW CV", "RED CELL DISTRIBUTION WIDTH - CV", "RDW"],
        "ocr_variants": ["RDW-CV", "RDW CV", "RDW"],
        "acceptable_units": ["%"],
        "canonical_unit": "%",
        "sections": ["HAEMATOLOGY", "HEMATOLOGY", "CBC", "COMPLETE BLOOD COUNT", "COMPLETE BLOOD PICTURE", "PATHOLOGY"],
        "value_constraints": {"min": 5.0, "max": 50.0}
    },
    "PLT": {
        "canonical_name": "Platelet Count",
        "category": "HAEMATOLOGY",
        "aliases": ["PLT", "PLATELET", "PLATELET COUNT", "PLATELETS"],
        "ocr_variants": ["PLT", "PLATELET", "PLATELETS"],
        "acceptable_units": ["10^3/uL", "10^3/µL", "thou/uL", "lakhs/cumm", "lakh/cumm", "/cumm", "/cmm", "cells/cumm", "cells/cmm", "k/uL", "Lacs/cumm", "lacs/cumm", "lac/cumm"],
        "canonical_unit": "10^3/µL",
        "sections": ["HAEMATOLOGY", "HEMATOLOGY", "CBC", "COMPLETE BLOOD COUNT", "COMPLETE BLOOD PICTURE", "PATHOLOGY"],
        "value_constraints": {"min": 0.1, "max": 2000000.0}
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
        "aliases": ["CRP", "C-REACTIVE PROTEIN", "CRP (QUANTITATIVE)", "CRP-QUANTITATIVE", "CRP QUANTITATIVE", "C REACTIVE PROTEIN", "HS-CRP", "HSCRP", "C-REACTIVE PROTEIN (CRP)"],
        "ocr_variants": ["CRP", "CRP-QUANTITATIVE", "C.R.P"],
        "acceptable_units": ["mg/L", "mg/l", "mg/dL", "mgIL", "mg/dl"],
        "canonical_unit": "mg/L",
        "sections": ["BIOCHEMISTRY", "SEROLOGY", "PATHOLOGY", "INFLAMMATION", "IMMUNOLOGY"],
        "value_constraints": {"min": 0.01, "max": 1000.0}
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
    },
    # ----------------------------------------------------
    # SEROLOGY / INFECTIOUS DISEASE
    # ----------------------------------------------------
    "MALARIAL PARASITE": {
        "canonical_name": "MALARIAL PARASITE",
        "category": "SEROLOGY",
        "aliases": ["MALARIAL PARASITE", "MP", "MALARIA", "MALARIAL PARASITES", "MP ( MALARIAL PARASITE )", "MALARIAL PARASITE (MP)", "MP (MALARIAL PARASITE)"],
        "ocr_variants": ["MALARIAL PARASITE", "MP"],
        "acceptable_units": ["", None],
        "canonical_unit": "",
        "sections": ["SEROLOGY", "PATHOLOGY", "HAEMATOLOGY"],
        "acceptable_qualitative": ["POSITIVE", "NEGATIVE", "NIL", "ABSENT", "NOT SEEN", "SEEN"],
        "value_constraints": {"min": 0.0, "max": 100000.0}
    },
    "NS1": {
        "canonical_name": "NS1",
        "category": "SEROLOGY",
        "aliases": ["NS1", "NS1 AG", "NS1 ANTIGEN", "DENGUE NS1", "DENGUE NS1 AG", "NS1 ( ANTIGEN)", "NS1 (ANTIGEN)", "DENGUE VIRUS NS1"],
        "ocr_variants": ["NS1", "NS1 AG"],
        "acceptable_units": ["", None],
        "canonical_unit": "",
        "sections": ["SEROLOGY", "PATHOLOGY"],
        "acceptable_qualitative": ["POSITIVE", "NEGATIVE", "REACTIVE", "NON-REACTIVE"],
        "value_constraints": {"min": 0.0, "max": 100000.0}
    },
    "SALMONELLA TYPHI IGM": {
        "canonical_name": "SALMONELLA TYPHI IGM",
        "category": "SEROLOGY",
        "aliases": ["SALMONELLA TYPHI IGM", "TYPHIDOT IGM", "S. TYPHI IGM", "WIDAL IGM", "SALMONELLA TYPHI - IGM"],
        "ocr_variants": ["SALMONELLA TYPHI IGM"],
        "acceptable_units": ["", None],
        "canonical_unit": "",
        "sections": ["SEROLOGY", "PATHOLOGY"],
        "acceptable_qualitative": ["POSITIVE", "NEGATIVE", "REACTIVE", "NON-REACTIVE"],
        "value_constraints": {"min": 0.0, "max": 100000.0}
    },
    "SALMONELLA TYPHI IGG": {
        "canonical_name": "SALMONELLA TYPHI IGG",
        "category": "SEROLOGY",
        "aliases": ["SALMONELLA TYPHI IGG", "TYPHIDOT IGG", "S. TYPHI IGG", "WIDAL IGG", "SALMONELLA TYPHI - IGG"],
        "ocr_variants": ["SALMONELLA TYPHI IGG"],
        "acceptable_units": ["", None],
        "canonical_unit": "",
        "sections": ["SEROLOGY", "PATHOLOGY"],
        "acceptable_qualitative": ["POSITIVE", "NEGATIVE", "REACTIVE", "NON-REACTIVE"],
        "value_constraints": {"min": 0.0, "max": 100000.0}
    },
    # ----------------------------------------------------
    # CLINICAL PATHOLOGY / URINALYSIS
    # ----------------------------------------------------
    "Urine pH": {
        "canonical_name": "Urine pH",
        "category": "CLINICAL PATHOLOGY",
        "aliases": ["PH", "URINE PH", "REACTION", "PH ( STRIP )", "PH (STRIP)", "URINE REACTION"],
        "ocr_variants": ["PH", "P.H"],
        "acceptable_units": ["", None],
        "canonical_unit": "",
        "sections": ["CLINICAL PATHOLOGY", "URINALYSIS", "URINE ANALYSIS", "PATHOLOGY", "CUE"],
        "value_constraints": {"min": 3.0, "max": 10.0}
    },
    "Specific Gravity": {
        "canonical_name": "Specific Gravity",
        "category": "CLINICAL PATHOLOGY",
        "aliases": ["SPECIFIC GRAVITY", "SP. GRAVITY", "SP GRAVITY", "SG", "SPECIFIC GRAVITY ( STRIP )", "SPECIFIC GRAVITY (STRIP)"],
        "ocr_variants": ["SPECIFIC GRAVITY", "SP GRAVITY"],
        "acceptable_units": ["", None],
        "canonical_unit": "",
        "sections": ["CLINICAL PATHOLOGY", "URINALYSIS", "URINE ANALYSIS", "PATHOLOGY", "CUE"],
        "value_constraints": {"min": 1.000, "max": 1.060}
    },
    "Urine Protein": {
        "canonical_name": "Protein",
        "category": "CLINICAL PATHOLOGY",
        "aliases": ["PROTEIN", "URINE PROTEIN", "ALBUMIN", "PROTEIN ( STRIP )", "PROTEIN (STRIP)", "URINE ALBUMIN"],
        "ocr_variants": ["PROTEIN", "ALBUMIN"],
        "acceptable_units": ["", None, "mg/dL", "mg/dl"],
        "canonical_unit": "",
        "sections": ["CLINICAL PATHOLOGY", "URINALYSIS", "URINE ANALYSIS", "PATHOLOGY", "CUE"],
        "acceptable_qualitative": ["NIL", "NEGATIVE", "ABSENT", "TRACE", "1+", "2+", "3+", "4+", "POSITIVE", "PRESENT"],
        "value_constraints": {"min": 0.0, "max": 10000.0}
    },
    "Urine Sugar": {
        "canonical_name": "Sugar",
        "category": "CLINICAL PATHOLOGY",
        "aliases": ["SUGAR", "GLUCOSE", "URINE GLUCOSE", "URINE SUGAR", "SUGAR ( STRIP )", "SUGAR (STRIP)"],
        "ocr_variants": ["SUGAR", "GLUCOSE"],
        "acceptable_units": ["", None, "mg/dL", "mg/dl"],
        "canonical_unit": "",
        "sections": ["CLINICAL PATHOLOGY", "URINALYSIS", "URINE ANALYSIS", "PATHOLOGY", "CUE"],
        "acceptable_qualitative": ["NIL", "NEGATIVE", "ABSENT", "TRACE", "1+", "2+", "3+", "4+", "POSITIVE", "PRESENT"],
        "value_constraints": {"min": 0.0, "max": 10000.0}
    },
    "Urine Ketones": {
        "canonical_name": "Ketones",
        "category": "CLINICAL PATHOLOGY",
        "aliases": ["KETONES", "KETONE BODIES", "ACETONE", "KETONES ( STRIP )", "KETONES (STRIP)"],
        "ocr_variants": ["KETONES"],
        "acceptable_units": ["", None],
        "canonical_unit": "",
        "sections": ["CLINICAL PATHOLOGY", "URINALYSIS", "URINE ANALYSIS", "PATHOLOGY", "CUE"],
        "acceptable_qualitative": ["NIL", "NEGATIVE", "ABSENT", "TRACE", "POSITIVE", "PRESENT"],
        "value_constraints": {"min": 0.0, "max": 1000.0}
    },
    "Urine Bilirubin": {
        "canonical_name": "Bilirubin (Urine)",
        "category": "CLINICAL PATHOLOGY",
        "aliases": ["BILIRUBIN (URINE)", "URINE BILIRUBIN", "BILE SALTS", "BILIRUBIN ( STRIP )", "BILIRUBIN (STRIP)"],
        "ocr_variants": ["BILIRUBIN"],
        "acceptable_units": ["", None],
        "canonical_unit": "",
        "sections": ["CLINICAL PATHOLOGY", "URINALYSIS", "URINE ANALYSIS", "PATHOLOGY", "CUE"],
        "acceptable_qualitative": ["NIL", "NEGATIVE", "ABSENT", "POSITIVE", "PRESENT"],
        "value_constraints": {"min": 0.0, "max": 100.0}
    },
    "Urobilinogen": {
        "canonical_name": "Urobilinogen",
        "category": "CLINICAL PATHOLOGY",
        "aliases": ["UROBILINOGEN", "URINE UROBILINOGEN", "UROBILINOGEN ( STRIP )", "UROBILINOGEN (STRIP)"],
        "ocr_variants": ["UROBILINOGEN"],
        "acceptable_units": ["", None, "mg/dL", "mg/dl", "EU/dL"],
        "canonical_unit": "",
        "sections": ["CLINICAL PATHOLOGY", "URINALYSIS", "URINE ANALYSIS", "PATHOLOGY", "CUE"],
        "acceptable_qualitative": ["NIL", "NEGATIVE", "ABSENT", "NORMAL", "POSITIVE", "PRESENT"],
        "value_constraints": {"min": 0.0, "max": 50.0}
    },
    "Urine Blood": {
        "canonical_name": "Blood (Urine)",
        "category": "CLINICAL PATHOLOGY",
        "aliases": ["BLOOD", "URINE BLOOD", "OCCULT BLOOD", "BLOOD ( STRIP )", "BLOOD (STRIP)"],
        "ocr_variants": ["BLOOD"],
        "acceptable_units": ["", None],
        "canonical_unit": "",
        "sections": ["CLINICAL PATHOLOGY", "URINALYSIS", "URINE ANALYSIS", "PATHOLOGY", "CUE"],
        "acceptable_qualitative": ["NIL", "NEGATIVE", "ABSENT", "POSITIVE", "PRESENT", "TRACE"],
        "value_constraints": {"min": 0.0, "max": 1000.0}
    },
    "Urine Leucocytes": {
        "canonical_name": "Leucocytes",
        "category": "CLINICAL PATHOLOGY",
        "aliases": ["LEUCOCYTES", "LEUKOCYTES", "URINE LEUCOCYTES", "LEUCOCYTES ( STRIP )", "LEUCOCYTES (STRIP)"],
        "ocr_variants": ["LEUCOCYTES", "LEUKOCYTES"],
        "acceptable_units": ["", None],
        "canonical_unit": "",
        "sections": ["CLINICAL PATHOLOGY", "URINALYSIS", "URINE ANALYSIS", "PATHOLOGY", "CUE"],
        "acceptable_qualitative": ["NIL", "NEGATIVE", "ABSENT", "POSITIVE", "PRESENT", "TRACE"],
        "value_constraints": {"min": 0.0, "max": 1000.0}
    },
    "Urine Nitrite": {
        "canonical_name": "Nitrite",
        "category": "CLINICAL PATHOLOGY",
        "aliases": ["NITRITE", "URINE NITRITE", "NITRITE ( STRIP )", "NITRITE (STRIP)"],
        "ocr_variants": ["NITRITE"],
        "acceptable_units": ["", None],
        "canonical_unit": "",
        "sections": ["CLINICAL PATHOLOGY", "URINALYSIS", "URINE ANALYSIS", "PATHOLOGY", "CUE"],
        "acceptable_qualitative": ["NIL", "NEGATIVE", "ABSENT", "POSITIVE", "PRESENT"],
        "value_constraints": {"min": 0.0, "max": 100.0}
    },
    "Pus cells": {
        "canonical_name": "Pus cells",
        "category": "CLINICAL PATHOLOGY",
        "aliases": ["PUS CELLS", "PUS CELL", "PUS CELLS ( MICROSCOPY )", "PUS CELLS (MICROSCOPY)", "WBCS (MICROSCOPIC)"],
        "ocr_variants": ["PUS CELLS", "PUS CELL"],
        "acceptable_units": ["/HPF", "HPF", "/hpf", "hpf", "/cumm", ""],
        "canonical_unit": "/HPF",
        "sections": ["CLINICAL PATHOLOGY", "URINALYSIS", "URINE ANALYSIS", "PATHOLOGY", "CUE"],
        "acceptable_qualitative": ["NIL", "NEGATIVE", "ABSENT", "OCCASIONAL"],
        "value_constraints": {"min": 0.0, "max": 500.0}
    },
    "Epithelial Cells": {
        "canonical_name": "Epithelial Cells",
        "category": "CLINICAL PATHOLOGY",
        "aliases": ["EPITHELIAL CELLS", "EPITHELIAL CELL", "EPITHELIAL CELLS ( MICROSCOPY )", "EPITHELIAL CELLS (MICROSCOPY)"],
        "ocr_variants": ["EPITHELIAL CELLS", "EPITHELIAL CELL"],
        "acceptable_units": ["/HPF", "HPF", "/hpf", "hpf", "/cumm", ""],
        "canonical_unit": "/HPF",
        "sections": ["CLINICAL PATHOLOGY", "URINALYSIS", "URINE ANALYSIS", "PATHOLOGY", "CUE"],
        "acceptable_qualitative": ["NIL", "NEGATIVE", "ABSENT", "OCCASIONAL"],
        "value_constraints": {"min": 0.0, "max": 500.0}
    },
    "Casts": {
        "canonical_name": "Casts",
        "category": "CLINICAL PATHOLOGY",
        "aliases": ["CASTS", "CASTS ( MICROSCOPY )", "CASTS (MICROSCOPY)", "URINARY CASTS"],
        "ocr_variants": ["CASTS"],
        "acceptable_units": ["", None, "/HPF", "HPF", "/LPF", "LPF"],
        "canonical_unit": "",
        "sections": ["CLINICAL PATHOLOGY", "URINALYSIS", "URINE ANALYSIS", "PATHOLOGY", "CUE"],
        "acceptable_qualitative": ["NIL", "NEGATIVE", "ABSENT", "NOT SEEN", "NONE"],
        "value_constraints": {"min": 0.0, "max": 500.0}
    },
    "Crystals": {
        "canonical_name": "Crystals",
        "category": "CLINICAL PATHOLOGY",
        "aliases": ["CRYSTALS", "CRYSTALS ( MICROSCOPY )", "CRYSTALS (MICROSCOPY)", "URINARY CRYSTALS"],
        "ocr_variants": ["CRYSTALS"],
        "acceptable_units": ["", None, "/HPF", "HPF"],
        "canonical_unit": "",
        "sections": ["CLINICAL PATHOLOGY", "URINALYSIS", "URINE ANALYSIS", "PATHOLOGY", "CUE"],
        "acceptable_qualitative": ["NIL", "NEGATIVE", "ABSENT", "NOT SEEN", "NONE"],
        "value_constraints": {"min": 0.0, "max": 500.0}
    },
    "Colour": {
        "canonical_name": "Colour",
        "category": "CLINICAL PATHOLOGY",
        "aliases": ["COLOUR", "COLOR", "COLOUR ( MANUAL )", "COLOR ( MANUAL )"],
        "ocr_variants": ["COLOUR", "COLOR"],
        "acceptable_units": ["", None],
        "canonical_unit": "",
        "sections": ["CLINICAL PATHOLOGY", "URINALYSIS", "URINE ANALYSIS", "PATHOLOGY", "CUE"],
        "acceptable_qualitative": ["PALE YELLOW", "YELLOW", "STRAW", "AMBER", "CLEAR", "RED", "NORMAL"],
        "value_constraints": {"min": 0.0, "max": 100.0}
    },
    "Appearance": {
        "canonical_name": "Appearance",
        "category": "CLINICAL PATHOLOGY",
        "aliases": ["APPEARANCE", "APPEARANCE ( MANUAL )"],
        "ocr_variants": ["APPEARANCE"],
        "acceptable_units": ["", None],
        "canonical_unit": "",
        "sections": ["CLINICAL PATHOLOGY", "URINALYSIS", "URINE ANALYSIS", "PATHOLOGY", "CUE"],
        "acceptable_qualitative": ["CLEAR", "HAZY", "TURBID", "SLIGHTLY HAZY", "NORMAL"],
        "value_constraints": {"min": 0.0, "max": 100.0}
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

    # Pass 4: Strip parenthetical method or description e.g. "HEMOGLOBIN ( SLS method )" -> "HEMOGLOBIN"
    import re
    stripped = re.sub(r"\s*\([^\)]*\)\s*$", "", clean).strip()
    if stripped and stripped != clean:
        m = find_ontology_match(stripped)
        if m:
            return m

    # Pass 5: Strip trailing 'S or 's
    if clean.endswith("'S"):
        m = find_ontology_match(clean[:-2])
        if m:
            return m

    return None
