# NutriCompra — Project Context

## 1. Product

NutriCompra is a web application designed to help budget-constrained households plan nutritious weekly food purchases.

Core flow:

Budget → Meal Plan → Shopping List → Price Comparison → Nutrition Information

## 2. Problem

Users with limited household budgets have difficulty deciding what nutritious food to buy, how much they can afford, and where products are cheaper.

NutriCompra aims to reduce uncertainty, save time, support nutritious decisions, and keep purchases within the household budget.

## 3. Target user

The primary user is a household member responsible for food purchases who has a limited weekly budget and wants affordable and nutritious meals.

## 4. MVP

The MVP includes:

- Authentication
- Onboarding
- Household configuration
- Dashboard
- Weekly meal plan
- Meal detail
- Meal replacement
- Automatic shopping list
- Price comparison
- Nutrition information
- Budget tracking

## 5. Current implementation

The repository already contains the foundation of the application.

Existing areas include:

- mock data
- TypeScript types
- business logic
- budget calculations
- nutrition logic
- shopping logic
- recommendations logic
- services
- AI service interfaces/mock implementations
- Zustand stores
- hooks
- authentication pages
- onboarding
- landing page
- reusable UI components
- application shell components

Do NOT rebuild these foundations.

## 6. Current state

Authentication, landing page and onboarding are already implemented.

The following product areas still need implementation/integration:

- application shell
- dashboard
- weekly meal plan
- meal detail
- shopping list
- price comparison
- nutrition
- household configuration
- final integration and quality improvements

## 7. Architecture

Current frontend:

Next.js + TypeScript + Tailwind + shadcn/ui.

Existing separation:

UI
→ hooks/services
→ business logic
→ mock data

Future architecture:

Next.js
→ NestJS REST API
→ PostgreSQL/Prisma

Future AI/ML should be an independent service, potentially using Python/FastAPI.

## 8. Important development rules

- Do NOT rebuild the project.
- Do NOT replace the existing architecture.
- Reuse existing types, mock data, hooks, services, stores and business logic.
- Do NOT duplicate business logic.
- Do NOT create alternative versions of existing services.
- Do NOT implement real AI yet.
- Mock data is intentional for the current MVP.
- Keep UI, business logic and data access separated.
- Prefer small incremental changes.
- Only implement the functionality explicitly requested in the current task.
- Do not modify unrelated features.
- Do not perform broad repository refactors unless explicitly requested.

## 9. Development strategy

Implement one feature at a time.

After each feature:

1. Verify the feature works.
2. Fix errors directly related to that feature.
3. Commit the changes.
4. Stop.

Do not automatically continue to the next feature.

## 10. Design

NutriCompra should have a modern, clean SaaS-style interface.

Primary visual language:

- green as primary color
- dark blue for important/navigation elements
- light background
- yellow/amber for savings/opportunities
- red only for warnings/destructive states
- rounded cards
- subtle shadows
- clear whitespace
- responsive desktop/tablet/mobile
- accessible controls and readable typography
