# Extractable components

## Layout
- Source: `frontend/src/components/Layout.tsx`
- Category: layout
- Description: Desktop operations sidebar/topbar and mobile bottom navigation.
- Extractable props: active route.
- Hardcoded: brand, route names, Lucide icon choices, defense lifecycle strip.

## Logo
- Source: `frontend/src/components/Logo.tsx`
- Category: basic
- Description: CSS-native NAZAR mark and wordmark.
- Extractable props: compact.
- Hardcoded: NAZAR name and motif.

## Analyzer
- Source: `frontend/src/components/Analyzer.tsx`
- Category: basic
- Description: Multi-mode scam analysis workspace.
- Extractable props: compact, active mode, sample value, loading state.
- Hardcoded: field labels and signal taxonomy.

## PageHeader
- Source: `frontend/src/components/PageHeader.tsx`
- Category: basic
- Description: Eyebrow, title, description, and optional action.
- Extractable props: eyebrow, title, description, action.

## RiskBadge
- Source: `frontend/src/components/RiskBadge.tsx`
- Category: basic
- Description: SAFE/SUSPICIOUS/DANGEROUS status chip.
- Extractable props: classification.

## StateBlock
- Source: `frontend/src/components/StateBlock.tsx`
- Category: basic
- Description: Loading and error states.
- Extractable props: label, message, retry.
