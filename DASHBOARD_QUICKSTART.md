# Medical Dashboard - Quick Start Guide

## 🚀 Getting Started

### Step 1: Start the Backend

```bash
cd backend
python main.py
```

Server runs at: `http://localhost:8000`

### Step 2: Start the Frontend

```bash
cd frontend
npm run dev
```

Dashboard runs at: `http://localhost:5173`

### Step 3: Access the Dashboard

1. **Register/Login** as a patient
2. **Upload medical reports** (Reports page)
3. **Navigate to Medical Dashboard**: `http://localhost:5173/medical-dashboard`

## 📊 What You'll See

### Dashboard Overview

```
┌─────────────────────────────────────────────┐
│  Health Dashboard                  [Refresh] │
│  Monitor your medical parameters...          │
│                                               │
│  🔍 Filter: [All Parameters ▼]  Clear       │
├─────────────────────────────────────────────┤
│                                               │
│  ┌──────────────  ┌──────────────  ┌──────────┐
│  │  HbA1c         │  Glucose       │ Platelets│
│  │  Latest: 7.2%  │  Latest: 145   │ 250K/μL  │
│  │  ↓ Decreasing  │  → Stable      │ ↑ Inc.   │
│  │  🟡 MEDIUM 85% │  🟢 LOW 90%    │ 🟡 MED   │
│  └──────────────  └──────────────  └──────────┘
│
│  ┌──────────────  ┌──────────────  ┌──────────┐
│  │  Cholesterol   │  Creatinine    │ Hemoglobin
│  │  Latest: 220   │  Latest: 1.1   │ 13.5 g/dL
│  │  ↓ Decreasing  │  → Stable      │ → Stable
│  │  🔴 HIGH 92%   │  🟢 LOW 88%    │ 🟢 LOW 95%
│  └──────────────  └──────────────  └──────────┘
│
└─────────────────────────────────────────────┘
```

### Detailed Parameter View

```
┌─────────────────────────────────────────────┐
│  HbA1c - Detailed analysis and insights [X] │
├─────────────────────────────────────────────┤
│                                               │
│  Latest: 7.2%  |  Average: 7.1%             │
│  Trend: Decreasing  |  Risk: 🟡 MEDIUM 85%  │
│                                               │
│  ┌─────────────────────────────────────────┐ │
│  │           HbA1c Trend (%)               │ │
│  │  8.0 ─────┐                             │ │
│  │      7.5 ─┼─────────┐                   │ │
│  │      7.2 ─┼─────────┼───────┐           │ │
│  │      7.0 ─┼─────────┼───────┼────◊      │ │
│  │           ├─────────┼───────┼─────      │ │
│  │        Jan    Feb    Mar   Apr           │ │
│  └─────────────────────────────────────────┘ │
│                                               │
│  📋 Summary                                   │
│  HbA1c is currently 7.2%. Trend is          │
│  decreasing and overall risk is medium.     │
│                                               │
│  📈 Trend Analysis                           │
│  Your HbA1c shows a positive downward       │
│  trend over the past 3 months.              │
│                                               │
│  ⚠️ Risk Assessment                          │
│  Medium risk requires continued monitoring   │
│  and adherence to treatment plan.           │
│                                               │
│  💡 Recommendation                           │
│  Continue current treatment plan. Schedule   │
│  follow-up in 3 months.                     │
│                                               │
└─────────────────────────────────────────────┘
```

## 🎯 Key Features

### 1. Parameter Cards

- **Click** any card to see details
- **Trend indicators**: ↑ Increasing, ↓ Decreasing, → Stable
- **Risk colors**: 🟢 Low, 🟡 Medium, 🔴 High

### 2. Filter Parameters

- Use dropdown to view specific parameter
- Data updates instantly
- Shows only available parameters from your reports

### 3. Detailed View

- **Metrics Grid**: Latest, Average, Trend, Risk
- **Interactive Chart**: Hover for details
- **Full Insights**: Summary, Trend, Risk, Recommendations

### 4. Refresh Data

- Click **Refresh** button to fetch latest data
- Auto-refreshes every 5 minutes
- Handles errors gracefully

## 📋 Data Requirements

For the dashboard to display data:

✅ **You need:**

1. User account (Patient role)
2. Uploaded medical reports (PDF/Image)
3. Reports with extracted lab values

Example report contents that will appear:

- HbA1c
- Glucose
- Cholesterol
- Creatinine
- Hemoglobin
- Platelets
- etc.

## 🔍 Testing the Dashboard

### Test with Different Parameters

```bash
# All parameters
GET http://localhost:8000/api/dashboard

# Specific parameter
GET http://localhost:8000/api/dashboard?parameter=HbA1c

# With auth token
Authorization: Bearer YOUR_TOKEN
```

### Expected Response

```json
{
  "parameters": [
    {
      "parameter": "HbA1c",
      "analytics": {
        "parameter": "HbA1c",
        "values": [...],
        "trend": "Decreasing",
        "avg": 7.1,
        "min": 6.8,
        "max": 7.5
      },
      "risk": {
        "risk_level": "MEDIUM",
        "confidence": 85,
        "reason": "..."
      },
      "insights": {
        "summary": "...",
        "trend_insight": "...",
        "risk_insight": "...",
        "recommendation": "..."
      }
    }
  ]
}
```

## 🛠️ Component Stack

| Component              | Purpose                  | Status   |
| ---------------------- | ------------------------ | -------- |
| `ParameterCard.jsx`    | Summary display          | ✅ Ready |
| `TrendChart.jsx`       | Line chart visualization | ✅ Ready |
| `RiskBadge.jsx`        | Risk indicator           | ✅ Ready |
| `InsightsPanel.jsx`    | Insights display         | ✅ Ready |
| `MedicalDashboard.jsx` | Main page                | ✅ Ready |
| `dashboardService.js`  | API integration          | ✅ Ready |
| `/api/dashboard`       | Backend endpoint         | ✅ Ready |

## 🐛 Troubleshooting

### "No Data Available" Message

- ✅ Upload medical reports first
- ✅ Ensure reports have lab values
- ✅ Check that OCR processing completed

### Chart Not Showing

- ✅ Verify data format in console
- ✅ Check recharts is installed: `npm list recharts`
- ✅ Look for errors in browser console

### Risk Levels Always "LOW"

- ✅ This is normal for newly uploaded reports
- ✅ Risk engine evaluates trend + value
- ✅ Risk increases with concerning trends

### Cannot Access Dashboard

- ✅ Login first (must be patient)
- ✅ Check browser console for errors
- ✅ Verify backend is running

## 📱 Mobile Support

Dashboard is fully responsive:

- 📱 Mobile: 1-column layout
- 📱 Tablet: 2-column layout
- 💻 Desktop: 3-column layout

## 🎨 Color Coding

| Level  | Color     | Icon            |
| ------ | --------- | --------------- |
| LOW    | 🟢 Green  | ↓ Trending Down |
| MEDIUM | 🟡 Yellow | ↑ Trending Up   |
| HIGH   | 🔴 Red    | ⚠️ Alert        |

## 📞 API Endpoints

### Get Dashboard Data

```
GET /api/dashboard
Headers: Authorization: Bearer <token>
```

### Filter by Parameter

```
GET /api/dashboard?parameter=HbA1c
Headers: Authorization: Bearer <token>
```

## 📝 Notes

- Dashboard caches data for 5 minutes
- All data is from your uploaded reports
- Risk scores are calculated based on:
  - Latest value
  - Historical trend
  - Statistical confidence
- Insights are AI-generated recommendations

## ✅ Verification Checklist

After setup, verify:

- [ ] Backend running on port 8000
- [ ] Frontend running on port 5173
- [ ] Can login to application
- [ ] Can upload medical reports
- [ ] Medical Dashboard accessible at `/medical-dashboard`
- [ ] Parameter cards display with data
- [ ] Can click card to see details
- [ ] Can filter by parameter
- [ ] Chart renders correctly
- [ ] Insights display properly

## 🎉 You're All Set!

Your medical dashboard is now ready to use. Start monitoring your health parameters with beautiful visualizations and actionable insights.

**Questions?** Check [MEDICAL_DASHBOARD.md](./MEDICAL_DASHBOARD.md) for detailed documentation.

---

**Version**: 1.0.0  
**Last Updated**: May 2, 2026
