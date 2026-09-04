import json
import numpy as np
import sys
import os

sys.stdout.reconfigure(encoding='utf-8')

class PhantomOracle:
    """
    Predictive Oracle: Time-Series Forecasting using Numpy.
    Predicts Volatility Clusters (Spread Widenings) & Gas Spikes 1-hour in advance.
    """
    def __init__(self, history_file="sanitized_1yr_data.jsonl"):
        self.history_file = history_file
        self.data = []
        self.weights = np.random.randn(5) # Simple Autoregressive weights
        self.bias = np.random.randn(1)
        self.trained = False

    def load_data(self):
        print("🧠 [Oracle] Loading sanitized historical data for sequence learning...")
        if not os.path.exists(self.history_file):
            print("Error: Sanitized data not found.")
            return False
            
        with open(self.history_file, 'r') as f:
            for line in f:
                self.data.append(json.loads(line))
        print(f"✅ Loaded {len(self.data)} sequential records.")
        return True

    def train_time_series(self, epochs=50, learning_rate=0.01):
        """
        Trains a sequence model to predict future spreads based on past N periods.
        """
        if not self.load_data(): return
        
        print("🔮 [Oracle] Training Time-Series Predictive Model (Predicting 1-hour ahead)...")
        # Extract spread series
        spreads = [row["real_spread_pct"] for row in self.data]
        
        # We want to use past 5 periods to predict the state 12 periods (1 hour) ahead
        X = []
        y = []
        lookback = 5
        horizon = 12
        
        for i in range(len(spreads) - lookback - horizon):
            X.append(spreads[i : i+lookback])
            y.append(spreads[i + lookback + horizon - 1])
            
        X = np.array(X)
        y = np.array(y)
        
        # Simple Gradient Descent for AR model
        for epoch in range(epochs):
            predictions = np.dot(X, self.weights) + self.bias
            errors = predictions - y
            
            # Gradients
            dw = (2/len(X)) * np.dot(X.T, errors)
            db = (2/len(X)) * np.sum(errors)
            
            self.weights -= learning_rate * dw
            self.bias -= learning_rate * db
            
            if epoch % 10 == 0:
                mse = np.mean(errors**2)
                print(f"Epoch {epoch}: Mean Squared Error = {mse:.6f}")
                
        self.trained = True
        print("✅ Oracle Training Complete. Weights locked.")
        
    def predict_future(self, current_sequence):
        """
        Given the last 5 periods of spread, predicts the spread 1-hour into the future.
        """
        if not self.trained:
            print("Oracle not trained!")
            return 0.0
        prediction = np.dot(current_sequence, self.weights) + self.bias
        return float(prediction[0])

if __name__ == "__main__":
    oracle = PhantomOracle()
    oracle.train_time_series()
    
    # Simulate a live prediction
    test_seq = np.array([0.001, 0.002, 0.0015, 0.003, 0.004])
    pred = oracle.predict_future(test_seq)
    print(f"🎯 Oracle 1-Hour Forecast: Expected Spread = {pred*100:.2f}%")
