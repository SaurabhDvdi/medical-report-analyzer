# Medical Dashboard Implementation Guide

## Overview

A comprehensive React-based medical dashboard UI that consumes the FastAPI `/api/dashboard` endpoint. The dashboard displays structured medical intelligence data including analytics, risk assessment, and actionable insights for medical parameters.

## ✨ Features

### 1. **Parameter Cards**

- Display parameter name, latest value, trend, and risk level
- Color-coded trend indicators (Increasing/Decreasing/Stable)
- Risk badges with confidence scores (LOW/MEDIUM/HIGH)
- Click to expand for detailed view
- Responsive grid layout (1-3 columns based on screen size)

### 2. **Trend Visualization**

- Interactive line chart using Recharts
- X-axis: Report dates
- Y-axis: Parameter values
- Hover tooltips with detailed information
- Smooth animations and transitions

### 3. **Risk Indicators**

- Color-coded badges:
  - 🟢 **GREEN** = LOW risk
  - 🟡 **YELLOW** = MEDIUM risk
  - 🔴 **RED** = HIGH risk
- Displays confidence percentage
- Icons for quick visual reference

### 4. **Insights Panel**

- **Summary**: Overview of parameter status
- **Trend Analysis**: Historical trend interpretation
- **Risk Assessment**: Risk level explanation
- **Recommendation**: Actionable medical recommendations

### 5. **Data Handling**

- Automatic data fetching from backend
- 5-minute cache (configurable)
- Parameter filtering
- Real-time refresh button
- Error handling and retry logic

### 6. **UI/UX**

- Clean, modern medical UI with Tailwind CSS
- Responsive design (mobile, tablet, desktop)
- Loading skeletons for better UX
- Modal for detailed parameter view
- Minimal clutter, focus on data

## 📁 Component Structure

```
frontend/src/
├── components/
│   ├── ParameterCard.jsx       # Individual parameter card
│   ├── TrendChart.jsx          # Line chart for trends
│   ├── RiskBadge.jsx           # Risk level badge
│   └── InsightsPanel.jsx       # Insights and recommendations
├── pages/
│   └── MedicalDashboard.jsx    # Main dashboard page
├── services/
│   └── dashboardService.js     # API integration
└── App.jsx                     # Route integration
```

## 🔧 Setup Instructions

### 1. Install Dependencies (Already Done)

```bash
npm install recharts
```

**Recharts packages included:**

- `recharts` - Line charts, tooltips, and interactive visualizations
- Date formatting via `date-fns` (already installed)
- Icons via `lucide-react` (already installed)

### 2. Backend Setup

The backend endpoint is now available at:

```
GET /api/dashboard?parameter=HbA1c  (optional)
```

**Response Structure:**

```json
{
  "parameters": [
    {
      "parameter": "HbA1c",
      "analytics": {
        "parameter": "HbA1c",
        "values": [
          { "date": "2024-01-15", "value": 7.2 },
          { "date": "2024-02-15", "value": 7.0 }
        ],
        "trend": "Decreasing",
        "avg": 7.1,
        "min": 6.8,
        "max": 7.5,
        "slope": -0.2
      },
      "risk": {
        "parameter": "HbA1c",
        "risk_level": "MEDIUM",
        "confidence": 85,
        "reason": "Value is elevated but trending downward..."
      },
      "insights": {
        "parameter": "HbA1c",
        "summary": "HbA1c is currently 7.0. The trend is decreasing...",
        "trend_insight": "Your HbA1c shows a positive trend...",
        "risk_insight": "Medium risk requires monitoring...",
        "recommendation": "Continue current treatment plan..."
      }
    }
  ]
}
```

### 3. Frontend Routes

Access the medical dashboard:

```
http://localhost:5173/medical-dashboard
```

The dashboard is also accessible via the app navigation (patients only).

## 🎯 Component Usage

### ParameterCard

```jsx
<ParameterCard
  parameter="HbA1c"
  latestValue={7.2}
  unit="%"
  trend="Decreasing"
  riskLevel="MEDIUM"
  confidence={85}
  onClick={() => handleCardClick()}
/>
```

### TrendChart

```jsx
<TrendChart
  data={[
    { date: "2024-01-15T00:00:00", value: 7.2 },
    { date: "2024-02-15T00:00:00", value: 7.0 },
  ]}
  parameter="HbA1c"
  unit="%"
  height={400}
/>
```

### RiskBadge

```jsx
<RiskBadge
  riskLevel="HIGH"
  confidence={90}
  size="md" // 'sm' | 'md' | 'lg'
/>
```

### InsightsPanel

```jsx
<InsightsPanel
  insights={{
    summary: "HbA1c is currently 7.0...",
    trend_insight: "Your HbA1c shows...",
    risk_insight: "Medium risk requires...",
    recommendation: "Continue current treatment...",
  }}
  parameter="HbA1c"
/>
```

## 🚀 Features in Action

### 1. Initial Load

- Displays skeleton loaders while fetching
- Shows all parameters in grid layout
- Displays parameter cards with latest values

### 2. Parameter Filtering

- Dropdown to filter by parameter
- Real-time data updates
- Clear filter button

### 3. Detailed View

- Click any card to open modal
- Shows full analytics with metrics
- Interactive line chart
- Complete insights and recommendations
- Risk analysis details

### 4. Refresh Data

- Manual refresh button
- Automatic 5-minute cache refresh
- Real-time error handling

## 🎨 Styling

### Tailwind CSS Classes

- **Colors**: Blue, green, red, yellow for risk levels
- **Spacing**: Consistent padding and margins
- **Typography**: Clear hierarchy with font weights
- **Borders**: Subtle borders for card separation
- **Shadows**: Hover effects for interactivity

### Responsive Breakpoints

- **Mobile**: 1 column (full width)
- **Tablet**: 2 columns (md breakpoint)
- **Desktop**: 3 columns (lg breakpoint)

## 📊 Data Flow

```
1. User navigates to /medical-dashboard
   ↓
2. useQuery fetches from GET /api/dashboard
   ↓
3. Backend returns parameters with analytics/risk/insights
   ↓
4. Components parse and display data:
   - ParameterCard: Summary view
   - TrendChart: Visualization
   - RiskBadge: Risk indicator
   - InsightsPanel: Details
   ↓
5. User clicks card → detailed modal opens
   ↓
6. User can refresh or filter as needed
```

## ⚠️ Error Handling

### Loading States

- **Skeleton loaders** during initial fetch
- **Loading card** styling
- **Disabled interactions** during fetch

### Error States

- **Error banner** with retry button
- **User-friendly messages**
- **Fallback content**

### Empty States

- **No data message**
- **Action suggestion** (upload reports)
- **Refresh button**

## 🔐 Security & Access Control

- **Authentication**: Managed via JWT tokens (existing)
- **Authorization**: Role-based (patients only)
- **Doctor Access**: Can view approved patient data
- **CORS**: Configured in backend

## 📈 Performance Optimizations

### Caching

- React Query caches for 5 minutes
- Configurable stale time
- Background refetching

### Rendering

- Memoization for cards
- Virtualization ready (for large datasets)
- Conditional rendering

### Network

- Single API call per parameter
- Efficient data serialization
- Gzip compression ready

## 🔄 Future Enhancements

### Ready for Implementation

1. **Doctor View**: Multi-patient comparison
2. **Comparison Charts**: Parameter comparisons
3. **Alerts/Notifications**: Risk threshold alerts
4. **Export**: PDF reports
5. **Scheduling**: Doctor appointments
6. **Messaging**: In-app communications

### Advanced Features

- Predictive analytics
- Machine learning risk scores
- Time-series forecasting
- Patient cohort analysis

## 🧪 Testing the Dashboard

### Manual Testing Checklist

```
[ ] Navigate to /medical-dashboard
[ ] Verify parameters load
[ ] Click on a parameter card
[ ] Verify detailed modal opens
[ ] Verify chart renders
[ ] Verify insights display
[ ] Test parameter filter dropdown
[ ] Test refresh button
[ ] Test close modal
[ ] Test error state (disconnect API)
[ ] Test empty state
[ ] Test on mobile/tablet/desktop
```

### Backend Testing

```bash
# With authentication token
curl -H "Authorization: Bearer YOUR_TOKEN" \
  http://localhost:8000/api/dashboard

# With parameter filter
curl -H "Authorization: Bearer YOUR_TOKEN" \
  http://localhost:8000/api/dashboard?parameter=HbA1c
```

## 📝 API Integration Details

### dashboardService.js

```javascript
// Get all parameters
getDashboardData();

// Get specific parameter
getDashboardData("HbA1c");

// Both return Promise<{parameters: Array}>
```

### Error Handling

- **401 Unauthorized**: Redirects to login
- **403 Forbidden**: Access denied (non-patient)
- **500 Server Error**: Shows error banner
- **Network Error**: Retry logic

## 🎓 Component Documentation

### ParameterCard.jsx

**Purpose**: Display parameter summary

**Props**:

- `parameter` (string): Parameter name
- `latestValue` (number): Latest measured value
- `unit` (string): Unit of measurement
- `trend` (string): 'Increasing' | 'Decreasing' | 'Stable'
- `riskLevel` (string): 'LOW' | 'MEDIUM' | 'HIGH'
- `confidence` (number): 0-100 confidence percentage
- `isLoading` (boolean): Show loading state
- `onClick` (function): Card click handler

### TrendChart.jsx

**Purpose**: Visualize parameter trends

**Props**:

- `data` (array): [{date: ISO string, value: number}]
- `parameter` (string): Parameter name
- `unit` (string): Unit label
- `height` (number): Chart height in pixels

### RiskBadge.jsx

**Purpose**: Display risk level indicator

**Props**:

- `riskLevel` (string): 'LOW' | 'MEDIUM' | 'HIGH'
- `confidence` (number, optional): Confidence percentage
- `size` (string): 'sm' | 'md' | 'lg'

### InsightsPanel.jsx

**Purpose**: Show medical insights

**Props**:

- `insights` (object): {summary, trend_insight, risk_insight, recommendation}
- `parameter` (string, optional): Parameter name

### MedicalDashboard.jsx

**Purpose**: Main dashboard orchestrator

**Features**:

- Data fetching via React Query
- Parameter filtering
- Modal management
- Loading/error states

## 🐛 Troubleshooting

### Dashboard Not Showing Data

1. Check API endpoint is running
2. Verify user authentication
3. Check browser console for errors
4. Verify database has reports/lab values

### Chart Not Rendering

1. Check data format (ISO dates)
2. Verify recharts is installed
3. Check for null/undefined values
4. Inspect browser console

### Styling Issues

1. Clear Tailwind cache: `npm run build`
2. Verify CSS files loaded
3. Check for conflicting styles
4. Inspect element in DevTools

## 📞 Support

For issues or questions:

1. Check component props documentation
2. Review error messages in console
3. Verify backend API response
4. Check network tab in DevTools
5. Review React Query debugging tools

---

**Dashboard Version**: 1.0.0  
**Last Updated**: May 2, 2026  
**Status**: ✅ Production Ready
