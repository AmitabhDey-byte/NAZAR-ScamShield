# Page dependency trees

## / Dashboard
Entry: frontend/src/pages/Dashboard.tsx
- frontend/src/components/Analyzer.tsx
  - frontend/src/lib/api.ts
- frontend/src/components/PageHeader.tsx
- frontend/src/components/RiskBadge.tsx
- frontend/src/lib/api.ts

## /analyze
Entry: frontend/src/pages/Analyze.tsx
- frontend/src/components/Analyzer.tsx
  - frontend/src/lib/api.ts
- frontend/src/components/PageHeader.tsx

## /result/:id
Entry: frontend/src/pages/Result.tsx
- frontend/src/components/StateBlock.tsx
- frontend/src/components/RiskBadge.tsx
- frontend/src/lib/api.ts
- frontend/src/lib/types.ts

## /honeypot/:id
Entry: frontend/src/pages/Honeypot.tsx
- frontend/src/components/PageHeader.tsx
- frontend/src/components/StateBlock.tsx
- frontend/src/lib/api.ts

## /intelligence
Entry: frontend/src/pages/Intelligence.tsx
- frontend/src/components/PageHeader.tsx
- frontend/src/components/ThreatGraph.tsx
  - frontend/src/lib/types.ts
- frontend/src/components/StateBlock.tsx
- frontend/src/lib/api.ts

## /campaigns
Entry: frontend/src/pages/Campaigns.tsx
- frontend/src/components/PageHeader.tsx
- frontend/src/components/StateBlock.tsx
- frontend/src/lib/api.ts
- frontend/src/lib/types.ts

## /campaign/:id
Entry: frontend/src/pages/CampaignDetail.tsx
- frontend/src/components/PageHeader.tsx
- frontend/src/components/StateBlock.tsx
- frontend/src/lib/api.ts
- frontend/src/lib/types.ts

## /report
Entry: frontend/src/pages/Report.tsx
- frontend/src/components/PageHeader.tsx
- frontend/src/lib/api.ts

## /calls
Entry: frontend/src/pages/Calls.tsx
- frontend/src/components/PageHeader.tsx
- frontend/src/lib/api.ts

## /model
Entry: frontend/src/pages/ModelMetrics.tsx
- frontend/src/components/PageHeader.tsx
- frontend/src/components/StateBlock.tsx
- frontend/src/lib/api.ts
