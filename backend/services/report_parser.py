import re
from typing import Dict, List
from sqlalchemy.orm import Session
from models import LabValue, ReportCategory

class ReportParser:
    """Parse medical report text and extract structured data"""
    
    def __init__(self):
        # Common lab parameter patterns
        self.parameter_patterns = {
            'Hemoglobin': r'(?i)hemoglobin|hb\s*:?\s*(\d+\.?\d*)',
            'RBC': r'(?i)rbc|red\s*blood\s*cell|erythrocyte\s*:?\s*(\d+\.?\d*)',
            'WBC': r'(?i)wbc|white\s*blood\s*cell|leucocyte\s*:?\s*(\d+\.?\d*)',
            'Platelet': r'(?i)platelet|plt\s*:?\s*(\d+\.?\d*)',
            'Glucose': r'(?i)glucose|blood\s*sugar|fbs|rbs\s*:?\s*(\d+\.?\d*)',
            'Creatinine': r'(?i)creatinine\s*:?\s*(\d+\.?\d*)',
            'Urea': r'(?i)urea|bun\s*:?\s*(\d+\.?\d*)',
            'Cholesterol': r'(?i)cholesterol|total\s*cholesterol\s*:?\s*(\d+\.?\d*)',
            'HDL': r'(?i)hdl|high\s*density\s*lipoprotein\s*:?\s*(\d+\.?\d*)',
            'LDL': r'(?i)ldl|low\s*density\s*lipoprotein\s*:?\s*(\d+\.?\d*)',
            'Triglycerides': r'(?i)triglyceride\s*:?\s*(\d+\.?\d*)',
            'ALT': r'(?i)alt|sgot\s*:?\s*(\d+\.?\d*)',
            'AST': r'(?i)ast|sgpt\s*:?\s*(\d+\.?\d*)',
            'Bilirubin': r'(?i)bilirubin\s*:?\s*(\d+\.?\d*)',
            'TSH': r'(?i)tsh|thyroid\s*stimulating\s*hormone\s*:?\s*(\d+\.?\d*)',
            'T3': r'(?i)t3|triiodothyronine\s*:?\s*(\d+\.?\d*)',
            'T4': r'(?i)t4|thyroxine\s*:?\s*(\d+\.?\d*)',
        }
        
        # Reference ranges (can be enhanced with more data)
        self.reference_ranges = {
            'Hemoglobin': '12.0-17.5',
            'RBC': '4.5-5.5',
            'WBC': '4.0-11.0',
            'Platelet': '150-450',
            'Glucose': '70-100',
            'Creatinine': '0.6-1.2',
            'Urea': '7-20',
            'Cholesterol': '<200',
            'HDL': '>40',
            'LDL': '<100',
            'Triglycerides': '<150',
            'ALT': '7-56',
            'AST': '10-40',
            'Bilirubin': '0.1-1.2',
            'TSH': '0.4-4.0',
            'T3': '80-200',
            'T4': '4.5-12.0',
        }
        
        # Units
        self.units = {
            'Hemoglobin': 'g/dL',
            'RBC': 'million/µL',
            'WBC': 'thousand/µL',
            'Platelet': 'thousand/µL',
            'Glucose': 'mg/dL',
            'Creatinine': 'mg/dL',
            'Urea': 'mg/dL',
            'Cholesterol': 'mg/dL',
            'HDL': 'mg/dL',
            'LDL': 'mg/dL',
            'Triglycerides': 'mg/dL',
            'ALT': 'U/L',
            'AST': 'U/L',
            'Bilirubin': 'mg/dL',
            'TSH': 'mIU/L',
            'T3': 'ng/dL',
            'T4': 'µg/dL',
        }
        
        # Report category keywords
        self.category_keywords = {
            'Blood Test': ['cbc', 'complete blood count', 'hemoglobin', 'rbc', 'wbc'],
            'Lipid Profile': ['cholesterol', 'hdl', 'ldl', 'triglyceride', 'lipid'],
            'Liver Function': ['alt', 'ast', 'bilirubin', 'liver', 'sgot', 'sgpt'],
            'Kidney Function': ['creatinine', 'urea', 'bun', 'kidney', 'renal'],
            'Thyroid Function': ['tsh', 't3', 't4', 'thyroid'],
            'Diabetes': ['glucose', 'blood sugar', 'fbs', 'rbs', 'hba1c', 'diabetes'],
        }
    
    def parse_report(self, text: str, report_id: int, db: Session) -> Dict:
        """Parse report text and extract lab values"""
        if not text:
            return {}
        
        text_lower = text.lower()
        detected_category = None
        max_matches = 0
        
        # Detect category
        for category, keywords in self.category_keywords.items():
            matches = sum(1 for keyword in keywords if keyword in text_lower)
            if matches > max_matches:
                max_matches = matches
                detected_category = category
        
        # Extract lab values
        lab_values = []
        for param_name, pattern in self.parameter_patterns.items():
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                try:
                    value_str = match.group(1) if match.groups() else match.group(0)
                    # Extract numeric value
                    value_match = re.search(r'(\d+\.?\d*)', value_str)
                    if value_match:
                        value = float(value_match.group(1))
                        
                        # Get reference range
                        ref_range = self.reference_ranges.get(param_name, 'N/A')
                        unit = self.units.get(param_name, '')
                        
                        # Check if abnormal
                        is_abnormal = self._check_abnormal(param_name, value, ref_range)
                        
                        # Create lab value
                        lab_value = LabValue(
                            report_id=report_id,
                            parameter_name=param_name,
                            value=value,
                            unit=unit,
                            reference_range=ref_range,
                            is_abnormal=is_abnormal
                        )
                        lab_values.append(lab_value)
                except Exception as e:
                    print(f"Error parsing {param_name}: {str(e)}")
                    continue
        
        # Save to database
        for lv in lab_values:
            db.add(lv)
        db.commit()
        
        return {
            'category': detected_category,
            'lab_values_count': len(lab_values)
        }
    
    def _check_abnormal(self, param_name: str, value: float, ref_range: str) -> bool:
        """Check if value is outside reference range"""
        if ref_range == 'N/A':
            return False
        
        # Parse reference range
        if '-' in ref_range:
            # Range format: "12.0-17.5"
            parts = ref_range.split('-')
            try:
                lower = float(parts[0].strip())
                upper = float(parts[1].strip())
                return value < lower or value > upper
            except:
                return False
        elif ref_range.startswith('<'):
            # Less than format: "<200"
            try:
                threshold = float(ref_range[1:].strip())
                return value >= threshold
            except:
                return False
        elif ref_range.startswith('>'):
            # Greater than format: ">40"
            try:
                threshold = float(ref_range[1:].strip())
                return value <= threshold
            except:
                return False
        
        return False

