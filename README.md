# 📈 Alpha-Strike: ML-Driven S&P 500 Strategy

**Outperforming the S&P 500 by timing market regimes with Machine Learning.**

![Strategy Performance](assets/performance_chart.png)

## **The Result**
This system doesn't just track the index—it beats it by identifying structural regime shifts. While standard models lagged during the recent volatility, this strategy successfully captured the **V-shaped recovery**, ending significantly above the benchmark.

## **Why This Wins**
* **Alpha Generation:** Engineered to pivot from defense to offense, catching bounces that traditional trend-followers miss.
* **Execution Realistic:** Backtested with **5bps transaction costs** and **T+1 execution lag** to ensure results translate to real-world trading.
* **Regime Intelligence:** Uses ternary XGBoost logic to classify Bull, Bear, and Neutral states with a confidence threshold of 52%.
* **Maximum Exposure:** Designed to stay in the market to capture the long-term upward drift of the S&P 500.

## **Core Metrics**
| Metric | Status |
| :--- | :--- |
| **Benchmark** | S&P 500 (SPY) |
| **Alpha** | Positive vs. Buy & Hold |
| **Model** | Gradient Boosted Decision Trees (XGBoost) |
| **Costs** | Institutional-grade slippage/commission included |

---

## Intellectual Property Note
Note: The specific mathematical weights, HMM transition matrices, and hyperparameter configurations are excluded from this public release to protect proprietary trading logic.

## License

All rights are reserved. No license is granted to use, modify, distribute, sublicense, or commercialize the code in this repository without explicit written permission from the author.

Certain proprietary components, model configurations, and trading logic are intentionally omitted from the public version.

