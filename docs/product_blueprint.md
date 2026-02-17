Business Expansion Intelligence Engine
Product & Modeling Blueprint
1. Product Vision

This project evolves from an analytical dashboard into a:

Regional Business Expansion Intelligence Engine

The system provides forward-looking strategic insights to support:

Market expansion decisions

Investment planning

Partnership identification

Risk assessment

Structural economic positioning

The core objective is to forecast business environment conditions over a rolling 4-year horizon.

2. Target Users

Medium and large companies planning geographic expansion

Investment groups evaluating regional markets

Strategy and planning teams

Economic intelligence professionals

The system is designed for decision support, not descriptive reporting.

3. Analytical Unit

The core analytical grain is:

State (UF) × Macro Sector × Subsector × Year


Example:

Bahia × Industry × Fashion × 2026

This allows:

Structural analysis

Dynamic forecasting

Historical backtesting

Scenario simulation

4. Core Forecasting Framework
4.1 Rolling Multi-Year Forecast

The engine supports:

User-selected historical base year

Forecast horizon: 1 to 4 years ahead

Rolling forecast structure

Example:

If base year = 2026:

Forecasts generated for:

2027

2028

2029

2030

4.2 Predictive Targets

Primary target:

Business Base Growth

Growth rate of active firms in each UF × Subsector

Secondary targets:

Net firm growth (openings − closures)

Sector participation change

Expansion probability

Derived indices:

Expansion Score

Risk Score

Saturation Score

Partnership Score

5. Feature Engineering Strategy
5.1 Structural Variables

Sector participation

Historical CAGR (3y, 5y)

Diversification index

Regional structural score

5.2 Business Dynamics

Active firms

Net openings

Churn rate

Density proxy

5.3 Saturation Indicators

Firm density relative to state baseline

Growth deceleration signals

5.4 Complementarity Signals

Growth correlation with complementary subsectors

Ecosystem reinforcement signals

Cluster formation indicators

5.5 Labor Context (Secondary Layer)

Labor supply proxy

Workforce volatility

Demographic distribution trends

Labor metrics are contextual, not primary targets.

6. Backtesting & Model Validation

The system uses walk-forward temporal validation:

For each historical base year:

Train model using data ≤ base year

Predict base+1 to base+4

Compare with real observed values

Results stored in:

forecast_backtest


Metrics:

MAE

SMAPE

Horizon-based error decay

Subsector-level performance

7. Model Strategy
Baseline Models

Last-year growth

Moving average

Linear trend

Main Model (v1)

Gradient Boosting Regressor

Lag features

Structural variables

Complementarity indicators

Future versions may include:

Hierarchical models

Quantile regression

Multi-output forecasting

8. Forecast Output Tables
forecast_forward

Forecasts using latest available year.

forecast_backtest

Historical simulated forecasts.

Both include:

Base year

Target year

Horizon

Prediction

Confidence interval

Model version

9. Dashboard Integration

The dashboard will present:

Strategic Overview

Expansion score (4-year window)

Risk level

Saturation signal

Partnership ecosystem signal

Subsector Diagnostic

Annual growth forecast

Confidence interval

Competitive density

Complementary sector dynamics

Historical Simulation

Model performance

Forecast vs actual comparison

10. Roadmap
Phase 1

Define macro-subsectors

Build core mart

Implement 1-year forecast baseline

Add backtesting structure

Phase 2

Multi-horizon forecasting

Complementarity modeling

Expansion & risk indices

Phase 3

Quantile intervals

Scenario simulation

Advanced clustering & ecosystem detection

11. Strategic Positioning

This project is not a descriptive dashboard.

It is:

A structured, explainable, multi-horizon regional business intelligence engine.

Designed for strategic expansion decisions under uncertainty.