import polars as pl
import numpy as np
import joblib
import matplotlib.pyplot as plt
import os

class DirectionalBacktester:
    def __init__(self, data_path="data/processed/regime_data.parquet", tc_bps=5, confidence_threshold=0.52):
        if not os.path.exists("data/processed/forecaster_model.pkl"):
            raise FileNotFoundError("Trained model not found. Run engine.py first.")
            
        self.df = pl.read_parquet(data_path).to_pandas()
        self.model = joblib.load("data/processed/forecaster_model.pkl")
        
        # If feature names cannot be found, this will throw an error early
        self.features = self.model.get_booster().feature_names 
        
        # Engineering deltas
        for d, f1, f2 in [("RSI_Delta", "RSI_Fast", "RSI"), ("Vol_Delta", "Vol_Fast", "Vol_5d"), ("Momentum_Delta", "Momentum_Fast", "Momentum_10d")]:
            if d not in self.df.columns:
                self.df[d] = self.df[f1] - self.df[f2]
        
        self.df = self.df.dropna(subset=self.features + ['Returns'])
        self.tc = tc_bps / 10000.0 
        self.threshold = confidence_threshold

    def run_simulation(self):
        print(f"--- Executing Alpha-Strike Logic ---")
        OOS_DAYS = 252 # Number of trading days to simulate (1 year)
        test_df = self.df.tail(OOS_DAYS).copy()
        
        probs = self.model.predict_proba(test_df[self.features])
        test_df['P_Bear'], test_df['P_Neutral'], test_df['P_Bull'] = probs[:, 0], probs[:, 1], probs[:, 2]
        
        test_df['Sizing_Signal'] = 0.0 
        test_df['Mkt_Trend'] = test_df['Returns'].rolling(10).sum()

        for i in range(len(test_df)):
            p_bull = test_df['P_Bull'].iloc[i]
            p_bear = test_df['P_Bear'].iloc[i]
            trend = test_df['Mkt_Trend'].iloc[i]
            
           # --- STRATEGY HIERARCHY ---
            # 1. Buy the Dip (Mean Reversion)
            if trend <= -0.07:
                weight = 1.0
            # 2. High Conviction ML Signals
            elif p_bull > self.threshold:
                weight = 1.0
            elif p_bear > self.threshold:
                weight = -1.0 
            # 3. Defensive Scaling 
            elif p_bear > (self.threshold - 0.05):
                # If market is already weak, go heavier short, else light hedge
                weight = -0.50 if trend < -0.05 else -0.05
            # 4. If the trend is negative cut losses early
            elif trend < -0.02:
                weight = -1.0 # Sell off to prevent whipsaws
            else:
            # 5. Default to no position
                weight = 1.0
                
            test_df.iloc[i, test_df.columns.get_loc('Sizing_Signal')] = weight

        # --- CORRECT ALIGNMENT ---
        # Signal on Day T -> Position on Day T+1 -> Profit from Day T+1 Return
        test_df['Target_Position'] = test_df['Sizing_Signal'].shift(1).fillna(0)
        
        test_df['Trade_Executed'] = test_df['Target_Position'].diff().fillna(0).abs()
        test_df['TC_Paid'] = test_df['Trade_Executed'] * self.tc
        
        # Use current row returns to calculate strategy performance
        test_df['Strategy_Net'] = (test_df['Target_Position'] * test_df['Returns']) - test_df['TC_Paid']
        test_df['Benchmark_Cum'] = (1 + test_df['Returns']).cumprod()
        test_df['Strategy_Cum'] = (1 + test_df['Strategy_Net']).cumprod()

        self.results_df = test_df
        self.calculate_metrics()

    def calculate_metrics(self):
        df = self.results_df
        
        total_rebalances = (df['Trade_Executed'] > 0).sum()
        total_tc_pct = df['TC_Paid'].sum() * 100
        
        tot_strat = (df['Strategy_Cum'].iloc[-1] - 1) * 100
        tot_bench = (df['Benchmark_Cum'].iloc[-1] - 1) * 100
        
        sharpe = (df['Strategy_Net'].mean() * 252) / (df['Strategy_Net'].std() * np.sqrt(252))
        max_dd = (df['Strategy_Cum'] / df['Strategy_Cum'].cummax() - 1).min() * 100
        
        # ADDED: Market Exposure Calculation
        active_days = (df['Target_Position'] != 0.0).sum()
        market_exposure = (active_days / len(df)) * 100
        
        print(f"\n📊 Portfolio Performance REPORT")
        print("-" * 45)
        print(f"Cumulative Strategy Net : {tot_strat:>8.2f}%")
        print(f"Cumulative Benchmark    : {tot_bench:>8.2f}%")
        print(f"Alpha vs Benchmark      : {tot_strat - tot_bench:>8.2f}%")
        print("-" * 45)
        print(f"Time in Market          : {market_exposure:>8.2f}%")
        print(f"Total Rebalances        : {total_rebalances:>8d}")
        print(f"Total Fees Paid (TC)    : {total_tc_pct:>8.2f}%")
        print(f"Sharpe Ratio            : {sharpe:>8.2f}")
        print(f"Max Drawdown            : {max_dd:>8.2f}%")
        print("-" * 45)

    def plot_results(self):
        # GitHub-Ready Premium Plot
        plt.style.use('dark_background')
        fig, ax = plt.subplots(figsize=(12, 6)) # Single clean plot
        
        # Plotting lines
        ax.plot(self.results_df.index, self.results_df['Benchmark_Cum'], color='#888888', alpha=0.6, label='S&P 500 (Buy & Hold)', linewidth=1.5)
        ax.plot(self.results_df.index, self.results_df['Strategy_Cum'], color='#00ffcc', label='Adaptive Alpha', linewidth=2)
        
        # Adding a subtle fill under the strategy curve for visual weight
        ax.fill_between(self.results_df.index, self.results_df['Strategy_Cum'], 1.0, color='#00ffcc', alpha=0.1)
        
        # Formatting
        ax.set_title("Strategy Cumulative Returns vs Benchmark", fontsize=16, fontweight='bold', pad=15)
        ax.set_ylabel("Cumulative Growth (1.0 = Base)", fontsize=12)
        
        # Removing the massive gaps on the left and right
        ax.margins(x=0) 
        
        # Subtle grid for readability
        ax.grid(True, linestyle='--', alpha=0.2)
        
        # Clean legend
        ax.legend(loc='upper left', frameon=False, fontsize=12)
        
        plt.tight_layout()
        plt.show()

if __name__ == "__main__":
    tester = DirectionalBacktester(tc_bps=5, confidence_threshold=0.52)
    tester.run_simulation()
    tester.plot_results()