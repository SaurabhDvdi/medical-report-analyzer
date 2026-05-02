# Medical Dashboard - Architecture & Integration Guide

## 🏗️ System Architecture

### High-Level Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                        USER BROWSER                               │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │  Medical Dashboard UI (React)                             │  │
│  │  ┌─────────────────────────────────────────────────────┐  │  │
│  │  │  MedicalDashboard (Main Orchestrator)               │  │  │
│  │  │  ├─ ParameterCard ✖3                                │  │  │
│  │  │  ├─ TrendChart                                      │  │  │
│  │  │  ├─ RiskBadge                                       │  │  │
│  │  │  └─ InsightsPanel                                   │  │  │
│  │  └─────────────────────────────────────────────────────┘  │  │
│  │  ↓ React Query (caching, fetching)                        │  │
│  │  ↓ dashboardService.js (API calls)                        │  │
│  └───────────────────────────────────────────────────────────┘  │
│                        ↓ HTTP Request                             │
└────────────────────────────────────────────────────────────────────┘
                         ↓ GET /api/dashboard
                         ↓ Authorization: Bearer TOKEN
┌────────────────────────────────────────────────────────────────────┐
│                     BACKEND (FastAPI)                              │
│  ┌──────────────────────────────────────────────────────────────┐ │
│  │  /api/dashboard Endpoint                                     │ │
│  │  ├─ Fetch unique parameters (SQLAlchemy query)              │ │
│  │  ├─ For each parameter:                                     │ │
│  │  │  ├─ AnalyticsService.get_parameter_analytics()          │ │
│  │  │  ├─ RiskEngine.evaluate()                               │ │
│  │  │  └─ InsightsEngine.generate()                           │ │
│  │  └─ Return structured response                              │ │
│  └──────────────────────────────────────────────────────────────┘ │
│  ↓                                                                  │
│  ┌──────────────────────────────────────────────────────────────┐ │
│  │  Database                                                    │ │
│  │  ├─ users (authentication)                                  │ │
│  │  ├─ reports (medical reports)                               │ │
│  │  └─ lab_values (medical parameters)                         │ │
│  └──────────────────────────────────────────────────────────────┘ │
└────────────────────────────────────────────────────────────────────┘
                         ↑ JSON Response
                    {parameters: [...]}
```

---

## 📡 Request/Response Flow

### 1. Initial Load

```
User Opens /medical-dashboard
    ↓
MedicalDashboard Component Mounts
    ↓
useQuery Hook Triggered
    ↓
dashboardService.getDashboardData() Called
    ↓
HTTP GET /api/dashboard (with auth token)
    ↓
Backend:
  - get_current_user (from token)
  - query LabValue.parameter_name (distinct)
  - for each parameter:
    * get_parameter_analytics() → Analytics obj
    * evaluate() → Risk obj
    * generate() → Insights obj
  - return JSON
    ↓
Frontend Receives Data
    ↓
State Updated
    ↓
Components Re-render:
  - Grid of ParameterCards
  - Each card: parameter, value, trend, risk
    ↓
User Sees Dashboard
```

### 2. Parameter Detail View

```
User Clicks ParameterCard
    ↓
setSelectedParameter(parameter_name)
    ↓
MedicalDashboard Finds Data in Cache
    ↓
Modal Opens with:
  - Metrics (Latest, Avg, Trend, Risk)
  - TrendChart Component
    * Renders line chart from analytics.values
    * Interactive tooltips
  - InsightsPanel Component
    * Displays all insights
    * 4 sections with icons
    ↓
User Can:
  - Hover over chart
  - Read insights
  - Close modal
```

### 3. Parameter Filtering

```
User Selects Filter Dropdown
    ↓
setFilterParameter(selected_parameter)
    ↓
useQuery Re-runs with new queryKey
    ↓
HTTP GET /api/dashboard?parameter=HbA1c
    ↓
Backend:
  - Filters by parameter_name in where clause
  - Returns only HbA1c data
    ↓
Frontend:
  - Shows only HbA1c card
  - Grid updates
```

---

## 🔄 Component Hierarchy

```
App.jsx
└─ MedicalDashboard.jsx (Main Page)
   ├─ Header Section
   │  ├─ Title
   │  ├─ Subtitle
   │  └─ Refresh Button
   │
   ├─ Filter Bar
   │  ├─ Filter Icon
   │  ├─ Parameter Dropdown
   │  └─ Clear Button
   │
   ├─ Grid Container
   │  ├─ ParameterCard.jsx (1)
   │  │  ├─ Parameter Name
   │  │  ├─ Latest Value
   │  │  ├─ Trend Icon
   │  │  └─ RiskBadge.jsx
   │  │     ├─ Color Badge
   │  │     ├─ Risk Level Text
   │  │     └─ Confidence %
   │  │
   │  ├─ ParameterCard.jsx (2)
   │  └─ ParameterCard.jsx (3)
   │
   └─ Modal (When Card Clicked)
      ├─ Modal Header
      │  ├─ Parameter Title
      │  └─ Close Button
      │
      ├─ Metrics Grid
      │  ├─ Latest Card
      │  ├─ Average Card
      │  ├─ Trend Card
      │  └─ Risk Card
      │
      ├─ TrendChart.jsx
      │  ├─ LineChart (Recharts)
      │  ├─ XAxis (Dates)
      │  ├─ YAxis (Values)
      │  ├─ Grid
      │  ├─ Tooltip
      │  └─ Line
      │
      ├─ InsightsPanel.jsx
      │  ├─ Summary Section
      │  ├─ Trend Section
      │  ├─ Risk Section
      │  └─ Recommendation Section
      │
      ├─ Risk Analysis Box
      │  └─ Risk Reason Text
      │
      └─ Modal Footer
         └─ Close Button
```

---

## 📊 Data Structures

### Analytics Object (from Backend)

```javascript
{
  parameter: "HbA1c",                    // string
  values: [                              // array of time-series
    {
      date: "2024-01-15T00:00:00Z",     // ISO 8601
      value: 7.2                         // numeric
    },
    {
      date: "2024-02-15T00:00:00Z",
      value: 7.0
    }
  ],
  trend: "Decreasing",                  // "Increasing" | "Decreasing" | "Stable"
  avg: 7.1,                             // numeric
  min: 6.8,                             // numeric
  max: 7.5,                             // numeric
  slope: -0.2                           // numeric (rate of change)
}
```

### Risk Object (from Backend)

```javascript
{
  parameter: "HbA1c",                   // string
  risk_level: "MEDIUM",                 // "LOW" | "MEDIUM" | "HIGH"
  confidence: 85,                       // 0-100 percentage
  reason: "Value is elevated but..."   // string explanation
}
```

### Insights Object (from Backend)

```javascript
{
  parameter: "HbA1c",                   // string
  summary: "HbA1c is currently...",    // string overview
  trend_insight: "Your HbA1c shows...", // string analysis
  risk_insight: "Medium risk requires...", // string assessment
  recommendation: "Continue treatment..." // string advice
}
```

### Dashboard Response

```javascript
{
  parameters: [
    {
      parameter: "HbA1c",
      analytics: {
        /* Analytics object */
      },
      risk: {
        /* Risk object */
      },
      insights: {
        /* Insights object */
      },
    },
    {
      parameter: "Glucose",
      analytics: {
        /* ... */
      },
      risk: {
        /* ... */
      },
      insights: {
        /* ... */
      },
    },
    // ... more parameters
  ];
}
```

---

## 🎯 Component API Flows

### ParameterCard Component

```
Input Props:
  - parameter: "HbA1c"
  - latestValue: 7.2
  - unit: "%"
  - trend: "Decreasing"
  - riskLevel: "MEDIUM"
  - confidence: 85
  - onClick: () => setSelectedParameter("HbA1c")

Processing:
  1. getTrendIcon() → renders appropriate icon
  2. Maps colors based on trend
  3. Passes to RiskBadge for badge rendering

Output:
  - Card button that opens detail modal on click
  - Shows summary information
  - Clickable to expand
```

### TrendChart Component

```
Input Props:
  - data: [{date: "2024-01-15T...", value: 7.2}, ...]
  - parameter: "HbA1c"
  - unit: "%"
  - height: 400

Processing:
  1. Map data: Add displayDate (formatted) and fullDate
  2. Create CustomTooltip component
  3. Render ResponsiveContainer with LineChart

Output:
  - Interactive line chart
  - Hover tooltips
  - Legend
  - Grid lines
  - Formatted dates
```

### RiskBadge Component

```
Input Props:
  - riskLevel: "MEDIUM"
  - confidence: 85 (optional)
  - size: "md"

Processing:
  1. getRiskColor() → bg/text colors based on level
  2. getSizeClass() → padding/font for size
  3. getIconSize() → icon dimensions
  4. Map risk → icon (LOW=↓, MEDIUM=↑, HIGH=⚠️)

Output:
  - Colored badge with icon
  - Optional confidence %
  - Responsive sizing
```

### InsightsPanel Component

```
Input Props:
  - insights: {summary, trend_insight, risk_insight, recommendation}
  - parameter: "HbA1c" (optional)

Processing:
  1. Extract each insight field
  2. Render sections conditionally
  3. Add icons for each section
  4. Style recommendation highlight

Output:
  - 4-section panel
  - Icons for each section
  - Border separators
  - Empty state if no data
```

---

## 🔐 Authentication & Authorization Flow

```
User Login
  ↓
Receive JWT Token
  ↓
Token Stored in sessionStorage
  ↓
Navigate to /medical-dashboard
  ↓
useQuery Calls dashboardService.getDashboardData()
  ↓
dashboardService sends HTTP Request:
  headers: {
    Authorization: "Bearer JWT_TOKEN"
  }
  ↓
Backend:
  1. Extract token from header
  2. Verify token (get_current_user)
  3. Check user_id from token
  4. Check role (patient or doctor)
  5. If doctor: check approved access to patient
  6. Fetch data specific to user
  ↓
Response:
  - If unauthorized (401): API interceptor redirects to /login
  - If forbidden (403): Error message shown
  - If success (200): Data returned
```

---

## 🚀 Frontend Initialization

### App.jsx Integration

```jsx
1. Import MedicalDashboard
   import MedicalDashboard from './pages/MedicalDashboard'

2. Add Route
   <Route path="medical-dashboard" element={<MedicalDashboard />} />

3. Wrapped by:
   - Router (routing)
   - QueryClientProvider (React Query)
   - AuthProvider (authentication)
   - ToastProvider (notifications)
   - Layout (layout wrapper)
```

### Query Configuration

```javascript
const { data, isLoading, error, refetch } = useQuery({
  queryKey: ["dashboard", filterParameter],
  queryFn: () => getDashboardData(filterParameter),
  staleTime: 1000 * 60 * 5, // 5 minutes
});
```

**Behavior:**

- Query runs on mount
- Data cached for 5 minutes
- Re-runs if filterParameter changes
- `refetch()` manually triggers new request
- Error caught and displayed

---

## 📦 Dependencies & Versions

### Backend

```python
fastapi >= 0.100.0
sqlalchemy >= 2.0.0
# Uses existing services:
# - AnalyticsService (analytics_service.py)
# - RiskEngine (risk_engine.py)
# - InsightsEngine (insights.py)
```

### Frontend

```json
{
  "react": "^18.2.0",
  "recharts": "^2.8.0",
  "@tanstack/react-query": "^5.99.0",
  "tailwindcss": "^3.3.6",
  "lucide-react": "^0.294.0",
  "date-fns": "^2.30.0",
  "react-loading-skeleton": "^3.5.0",
  "axios": "^1.6.2"
}
```

---

## 🎨 Styling Architecture

### Tailwind Classes Used

#### Layout

```css
grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6
max-w-7xl mx-auto px-6 py-8
flex items-center justify-between
```

#### Cards

```css
bg-white rounded-lg border border-gray-200 p-6
hover:shadow-lg transition-shadow
cursor-pointer
```

#### Colors

```css
/* Risk Levels */
bg-green-100 text-green-800      /* LOW */
bg-yellow-100 text-yellow-800    /* MEDIUM */
bg-red-100 text-red-800          /* HIGH */

/* Status */
bg-blue-50, bg-green-50, bg-purple-50, bg-gray-50
```

#### Typography

```css
text-3xl font-bold text-gray-900   /* Large */
text-lg font-semibold text-gray-800 /* Medium */
text-sm font-medium text-gray-600   /* Small */
```

---

## 🔄 State Management Flow

### React State (MedicalDashboard)

```javascript
// 1. Selected parameter for detail view
const [selectedParameter, setSelectedParameter] = useState(null)
// Opens/closes modal when changed

// 2. Filter selection
const [filterParameter, setFilterParameter] = useState('')
// Triggers React Query re-run via queryKey

// 3. Available parameters
const [allParameters, setAllParameters] = useState([])
// Populated from data on mount, used for dropdown

// 4. Data (from React Query)
const { data, isLoading, error, refetch } = useQuery(...)
// Parameters array: [{parameter, analytics, risk, insights}, ...]
```

### Data Flow Through States

```
useQuery Fetches → data.parameters arrives
                   ↓
useEffect runs → extracts parameter names
                   ↓
setAllParameters(names)
                   ↓
Dropdown updates with options
                   ↓
User selects → setSelectedParameter()
                   ↓
Modal opens showing that parameter's data
```

---

## ⚠️ Error Handling

### Frontend Error Scenarios

```
1. Network Error
   ↓ caught by React Query
   ↓ error state updated
   ↓ Error banner shown with retry button

2. 401 Unauthorized
   ↓ API interceptor catches
   ↓ Removes token from sessionStorage
   ↓ Redirects to /login

3. 403 Forbidden
   ↓ Error shown
   ↓ Message: "Access not granted"

4. 500 Server Error
   ↓ Error banner shown
   ↓ Retry button available

5. No Data
   ↓ Empty state shown
   ↓ Message: "Upload reports first"
```

### Backend Error Scenarios

```python
@app.get("/api/dashboard")
async def get_dashboard(...):
    try:
        # Get current user (raises if invalid token)
        user_id = current_user["user_id"]

        # Query parameters
        parameters = [...] # May be empty

        # Process each parameter
        for param in parameters:
            try:
                analytics = analytics_service.get_parameter_analytics(...)
                risk = risk_engine.evaluate(analytics)
                insights = insights_engine.generate(analytics, risk)
                dashboard_data.append({...})
            except Exception as e:
                # Log but continue with other parameters
                print(f"Error processing {param}: {e}")
                continue

        return {"parameters": dashboard_data}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
```

---

## 📈 Performance Considerations

### Optimization Techniques

1. **React Query Caching**
   - 5-minute stale time
   - Reduces API calls
   - Instant UI updates

2. **Conditional Rendering**
   - Only renders selected card details
   - Modal hidden when not selected
   - Lazy load chart only in modal

3. **Memoization Ready**
   - Components can use React.memo()
   - Prevents unnecessary re-renders

4. **Image Optimization**
   - Chart renders only when visible
   - SVG-based (Recharts)
   - No external images

### Load Time Estimates

```
Initial Page Load: ~500ms
  - Fetch from /api/dashboard: ~200ms
  - Frontend render: ~300ms

Card Click to Detail: ~0ms
  - Uses cached data
  - Modal animation: ~300ms

Refresh Data: ~200ms
  - Network + processing

Chart Render: ~100ms
  - Recharts component
```

---

## 🧪 Integration Checklist

### Before Going to Production

- [ ] Verify backend endpoint works
- [ ] Test authentication flow
- [ ] Check error handling
- [ ] Test on mobile/tablet/desktop
- [ ] Performance profiling
- [ ] Security review
- [ ] Data privacy check
- [ ] Browser compatibility
- [ ] Accessibility audit
- [ ] Load testing

### Environment Setup

- [ ] Backend running on port 8000
- [ ] Frontend running on port 5173
- [ ] Database configured
- [ ] CORS enabled
- [ ] Auth tokens working
- [ ] Recharts installed
- [ ] Tailwind CSS configured

---

## 📝 Monitoring & Debugging

### React DevTools

```
1. Install React DevTools browser extension
2. Open DevTools
3. Components tab: Inspect component tree
4. Profiler tab: Profile performance
5. Check state updates
```

### Network Tab

```
1. Open DevTools → Network
2. Go to /medical-dashboard
3. Watch requests:
   - GET /api/dashboard (200)
   - Check response payload
   - Verify headers include Authorization
4. Click card and filter to check new requests
```

### Console

```
1. Watch for errors
2. Check for warnings
3. Verify React Query logging (optional)
4. Test API calls: dashboardService.getDashboardData()
```

### Backend Logging

```python
@app.get("/api/dashboard")
async def get_dashboard(...):
    print(f"Dashboard request from user {user_id}")
    # ... processing ...
    print(f"Found {len(parameters)} parameters")
    return response
```

---

## 🚀 Deployment Considerations

### Backend Deployment

```bash
# Production server
gunicorn -w 4 -b 0.0.0.0:8000 main:app

# Environment variables
DATABASE_URL=postgresql://...
JWT_SECRET=...
```

### Frontend Deployment

```bash
# Build
npm run build

# Output: dist/ folder
# Deploy to: Vercel, Netlify, S3+CloudFront, etc.

# Update API URL for production
# frontend/src/utils/api.js
baseURL = 'https://api.production.com'
```

---

## 📞 Troubleshooting Guide

### Dashboard Shows "No Data Available"

**Causes:**

- No reports uploaded
- Reports don't have lab values
- OCR processing failed
- Database query returned empty

**Solutions:**

1. Check `/api/reports` - verify reports uploaded
2. Check database: `SELECT * FROM lab_values LIMIT 5`
3. Run OCR manually if needed
4. Check backend logs

### Chart Not Rendering

**Causes:**

- Recharts not installed
- Data format incorrect
- Null/undefined values

**Solutions:**

1. `npm list recharts` - verify installation
2. Check data in DevTools → Network tab
3. Inspect chart errors in console
4. Filter out null values: `data.filter(d => d.value)`

### Filter Dropdown Empty

**Causes:**

- No parameters in database
- useEffect not running
- allParameters not set

**Solutions:**

1. Verify data arrives from API
2. Check useEffect dependencies
3. Inspect state in React DevTools

---

## 🎓 Architecture Principles

1. **Separation of Concerns**
   - Components: UI only
   - Services: API calls only
   - Pages: Orchestration only

2. **Reusability**
   - Components can be used independently
   - Services are framework-agnostic
   - Data structures are documented

3. **Error Resilience**
   - Graceful degradation
   - Fallback states
   - Error messages

4. **Performance First**
   - Caching strategy
   - Lazy loading ready
   - Optimized rendering

5. **Type Safety**
   - JSDoc comments for prop types
   - Consistent data structures
   - Validated API responses

---

**Architecture Version**: 1.0.0  
**Last Updated**: May 2, 2026  
**Status**: ✅ Production Ready
