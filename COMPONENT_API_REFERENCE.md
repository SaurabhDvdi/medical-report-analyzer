# Medical Dashboard - Component API Reference

## Components Overview

### 1. ParameterCard

Display a parameter summary card with latest value, trend, and risk level.

#### Location

```
frontend/src/components/ParameterCard.jsx
```

#### Props

| Prop          | Type     | Required | Default   | Description                              |
| ------------- | -------- | -------- | --------- | ---------------------------------------- |
| `parameter`   | string   | ✅       | -         | Parameter name (e.g., "HbA1c")           |
| `latestValue` | number   | ❌       | null      | Latest measured value                    |
| `unit`        | string   | ❌       | ""        | Unit of measurement (e.g., "%")          |
| `trend`       | string   | ❌       | "Unknown" | 'Increasing' \| 'Decreasing' \| 'Stable' |
| `riskLevel`   | string   | ❌       | null      | 'LOW' \| 'MEDIUM' \| 'HIGH'              |
| `confidence`  | number   | ❌       | -         | 0-100 confidence percentage              |
| `isLoading`   | boolean  | ❌       | false     | Show loading skeleton                    |
| `onClick`     | function | ❌       | -         | Card click handler                       |

#### Example Usage

```jsx
import ParameterCard from "@/components/ParameterCard";

<ParameterCard
  parameter="HbA1c"
  latestValue={7.2}
  unit="%"
  trend="Decreasing"
  riskLevel="MEDIUM"
  confidence={85}
  isLoading={false}
  onClick={() => console.log("Card clicked")}
/>;
```

#### Features

- ✅ Responsive design
- ✅ Loading skeleton
- ✅ Trend icons (↑↓→)
- ✅ Risk badge integration
- ✅ Hover effects
- ✅ Click interaction

---

### 2. TrendChart

Interactive line chart showing parameter values over time using Recharts.

#### Location

```
frontend/src/components/TrendChart.jsx
```

#### Props

| Prop        | Type   | Required | Default | Description                                     |
| ----------- | ------ | -------- | ------- | ----------------------------------------------- |
| `data`      | array  | ❌       | []      | Chart data: [{date: ISO string, value: number}] |
| `parameter` | string | ❌       | ""      | Parameter name for chart title                  |
| `unit`      | string | ❌       | ""      | Unit label for Y-axis                           |
| `height`    | number | ❌       | 300     | Chart height in pixels                          |

#### Data Format

```javascript
const data = [
  { date: "2024-01-15T00:00:00Z", value: 7.2 },
  { date: "2024-02-15T00:00:00Z", value: 7.0 },
  { date: "2024-03-15T00:00:00Z", value: 6.9 },
];
```

#### Example Usage

```jsx
import TrendChart from "@/components/TrendChart";

<TrendChart
  data={analyticsData.values}
  parameter="HbA1c"
  unit="%"
  height={400}
/>;
```

#### Features

- ✅ Interactive tooltips
- ✅ Responsive container
- ✅ Date formatting
- ✅ Smooth animations
- ✅ Grid and axis labels
- ✅ Empty state handling

---

### 3. RiskBadge

Color-coded badge indicating risk level with optional confidence.

#### Location

```
frontend/src/components/RiskBadge.jsx
```

#### Props

| Prop         | Type   | Required | Default | Description                 |
| ------------ | ------ | -------- | ------- | --------------------------- |
| `riskLevel`  | string | ✅       | -       | 'LOW' \| 'MEDIUM' \| 'HIGH' |
| `confidence` | number | ❌       | -       | 0-100 confidence percentage |
| `size`       | string | ❌       | 'md'    | 'sm' \| 'md' \| 'lg'        |

#### Size Options

| Size | Padding     | Font    | Use Case           |
| ---- | ----------- | ------- | ------------------ |
| 'sm' | px-2 py-1   | text-xs | Cards, inline      |
| 'md' | px-3 py-1.5 | text-sm | Default, most uses |
| 'lg' | px-4 py-2   | text-lg | Headers, emphasis  |

#### Color Mapping

| Risk Level | Background    | Text            | Icon            |
| ---------- | ------------- | --------------- | --------------- |
| LOW        | bg-green-100  | text-green-800  | ↓ Trending Down |
| MEDIUM     | bg-yellow-100 | text-yellow-800 | ↑ Trending Up   |
| HIGH       | bg-red-100    | text-red-800    | ⚠️ Alert        |

#### Example Usage

```jsx
import RiskBadge from '@/components/RiskBadge'

// With confidence
<RiskBadge
  riskLevel="MEDIUM"
  confidence={85}
  size="md"
/>

// Sizes
<RiskBadge riskLevel="HIGH" size="sm" />
<RiskBadge riskLevel="MEDIUM" size="md" />
<RiskBadge riskLevel="LOW" size="lg" />
```

#### Features

- ✅ Color-coded backgrounds
- ✅ Icons for each level
- ✅ Multiple sizes
- ✅ Confidence display
- ✅ Responsive padding

---

### 4. InsightsPanel

Display medical insights including summary, trend, risk, and recommendations.

#### Location

```
frontend/src/components/InsightsPanel.jsx
```

#### Props

| Prop        | Type   | Required | Default | Description                  |
| ----------- | ------ | -------- | ------- | ---------------------------- |
| `insights`  | object | ❌       | {}      | Insights object from backend |
| `parameter` | string | ❌       | -       | Parameter name for header    |

#### Insights Object Structure

```javascript
const insights = {
  summary:
    "HbA1c is currently 7.2%. The trend is decreasing and overall risk is medium.",
  trend_insight:
    "Your HbA1c shows a positive downward trend over the past 3 months.",
  risk_insight:
    "Medium risk requires continued monitoring and adherence to treatment plan.",
  recommendation:
    "Continue current treatment plan. Schedule follow-up in 3 months.",
};
```

#### Example Usage

```jsx
import InsightsPanel from "@/components/InsightsPanel";

<InsightsPanel insights={dashboardData.insights} parameter="HbA1c" />;
```

#### Features

- ✅ Sectioned layout
- ✅ Icon labels
- ✅ Border separators
- ✅ Highlight recommendations
- ✅ Empty state
- ✅ Responsive design

#### Sections

| Section         | Icon | Use                |
| --------------- | ---- | ------------------ |
| Summary         | 📋   | Quick overview     |
| Trend Analysis  | 📈   | Historical context |
| Risk Assessment | ⚠️   | Risk explanation   |
| Recommendation  | 💡   | Action items       |

---

### 5. MedicalDashboard

Main dashboard page component orchestrating all views.

#### Location

```
frontend/src/pages/MedicalDashboard.jsx
```

#### Features

- ✅ Data fetching with React Query
- ✅ Parameter filtering
- ✅ Modal for detailed view
- ✅ Loading/error states
- ✅ Refresh functionality
- ✅ Responsive grid

#### State Management

```javascript
// Selected parameter for detail view
const [selectedParameter, setSelectedParameter] = useState(null);

// Filter by parameter
const [filterParameter, setFilterParameter] = useState("");

// All available parameters
const [allParameters, setAllParameters] = useState([]);
```

#### Query Configuration

```javascript
const { data, isLoading, error, refetch } = useQuery({
  queryKey: ["dashboard", filterParameter],
  queryFn: () => getDashboardData(filterParameter),
  staleTime: 1000 * 60 * 5, // 5 minutes
});
```

#### Handlers

```javascript
// Close detail modal
handleCloseDetail();

// Reset filters and close modal
handleReset();

// Extract latest value from analytics
getLatestValue(analytics);

// Get unit from analytics (extensible)
getUnit(analytics);
```

---

## Service API

### dashboardService.js

Backend API integration service.

#### Location

```
frontend/src/services/dashboardService.js
```

#### Functions

##### getDashboardData(parameter?: string)

Fetch dashboard data from backend.

```typescript
getDashboardData(parameter?: string): Promise<{
  parameters: Array<{
    parameter: string
    analytics: Analytics
    risk: Risk
    insights: Insights
  }>
}>
```

**Parameters:**

- `parameter` (string, optional): Filter by parameter name

**Returns:** Promise with parameters array

**Example:**

```javascript
// Get all parameters
const data = await getDashboardData();

// Get specific parameter
const data = await getDashboardData("HbA1c");

// With React Query
const { data } = useQuery({
  queryKey: ["dashboard"],
  queryFn: () => getDashboardData(),
});
```

---

## Data Structures

### Analytics Object

```javascript
{
  parameter: "HbA1c",
  values: [
    { date: "2024-01-15T00:00:00Z", value: 7.2 },
    { date: "2024-02-15T00:00:00Z", value: 7.0 }
  ],
  trend: "Decreasing",
  avg: 7.1,
  min: 6.8,
  max: 7.5,
  slope: -0.2
}
```

### Risk Object

```javascript
{
  parameter: "HbA1c",
  risk_level: "MEDIUM",
  confidence: 85,
  reason: "Value is elevated but trending downward. Continue monitoring."
}
```

### Insights Object

```javascript
{
  parameter: "HbA1c",
  summary: "HbA1c is currently 7.2%. The trend is decreasing...",
  trend_insight: "Your HbA1c shows a positive trend...",
  risk_insight: "Medium risk requires monitoring...",
  recommendation: "Continue current treatment plan..."
}
```

---

## Hooks & Libraries

### React Libraries Used

- **@tanstack/react-query**: Data fetching and caching
- **recharts**: Chart visualization
- **date-fns**: Date formatting
- **lucide-react**: Icons
- **react-loading-skeleton**: Loading skeletons
- **tailwindcss**: Styling

### Custom Hooks

None currently - uses React Query's `useQuery`

---

## Styling Guidelines

### Tailwind Classes Used

#### Colors

```
Text: text-gray-700, text-blue-600, text-red-800
Background: bg-white, bg-gray-50, bg-blue-50
Borders: border-gray-200, border-blue-200
```

#### Spacing

```
Padding: p-4, p-6, px-3, py-2
Margin: mb-4, mt-1
Gap: gap-2, gap-4
```

#### Typography

```
Font Weight: font-bold, font-semibold, font-medium
Font Size: text-sm, text-lg, text-3xl
```

#### Interactive

```
Hover: hover:shadow-lg, hover:border-gray-300
Focus: focus:ring-2, focus:ring-blue-500
Transition: transition-shadow, transition-colors
```

---

## Integration Examples

### Adding to Existing Page

```jsx
import MedicalDashboard from "@/pages/MedicalDashboard";

// In your router
<Route path="medical-dashboard" element={<MedicalDashboard />} />;
```

### Displaying Single Parameter

```jsx
import ParameterCard from "@/components/ParameterCard";
import { getDashboardData } from "@/services/dashboardService";
import { useQuery } from "@tanstack/react-query";

function MyComponent() {
  const { data } = useQuery({
    queryKey: ["dashboard", "HbA1c"],
    queryFn: () => getDashboardData("HbA1c"),
  });

  const param = data?.parameters[0];

  return (
    <ParameterCard
      parameter={param.parameter}
      latestValue={
        param.analytics.values[param.analytics.values.length - 1]?.value
      }
      trend={param.analytics.trend}
      riskLevel={param.risk.risk_level}
      confidence={param.risk.confidence}
    />
  );
}
```

### Extending with Custom Logic

```jsx
// Override data formatting
const getFormattedValue = (value) => {
  return value?.toFixed(2) || "N/A";
};

// Add custom filtering
const filterParameters = (params, condition) => {
  return params.filter((p) => condition(p.risk.risk_level));
};

// Get high-risk only
const highRiskParams = filterParameters(
  data.parameters,
  (level) => level === "HIGH",
);
```

---

## Performance Considerations

### Memoization

Components use React defaults - can be memoized if needed:

```jsx
export default memo(ParameterCard, (prev, next) => {
  return (
    prev.parameter === next.parameter && prev.latestValue === next.latestValue
  );
});
```

### Lazy Loading

For many parameters, consider pagination:

```jsx
import { useState } from "react";

function Dashboard() {
  const [page, setPage] = useState(1);
  const itemsPerPage = 6;

  const start = (page - 1) * itemsPerPage;
  const paginatedParams = parameters.slice(start, start + itemsPerPage);

  return (
    <>
      {paginatedParams.map((p) => (
        <ParameterCard key={p.parameter} {...p} />
      ))}
      <Pagination page={page} onChange={setPage} />
    </>
  );
}
```

---

## Testing Components

### Unit Tests (Example)

```javascript
import { render, screen } from "@testing-library/react";
import ParameterCard from "@/components/ParameterCard";

describe("ParameterCard", () => {
  it("renders parameter name", () => {
    render(
      <ParameterCard parameter="HbA1c" latestValue={7.2} trend="Decreasing" />,
    );
    expect(screen.getByText("HbA1c")).toBeInTheDocument();
  });
});
```

---

## Browser Compatibility

- ✅ Chrome/Edge (Latest)
- ✅ Firefox (Latest)
- ✅ Safari (Latest)
- ✅ Mobile browsers
- ❌ IE11 (not supported)

---

## Version History

| Version | Date        | Changes         |
| ------- | ----------- | --------------- |
| 1.0.0   | May 2, 2026 | Initial release |

---

## Related Documentation

- [MEDICAL_DASHBOARD.md](../MEDICAL_DASHBOARD.md) - Detailed guide
- [DASHBOARD_QUICKSTART.md](../DASHBOARD_QUICKSTART.md) - Quick start
- [README.md](../README.md) - Project overview

---

**Last Updated**: May 2, 2026  
**Maintainer**: Development Team  
**Status**: ✅ Production Ready
