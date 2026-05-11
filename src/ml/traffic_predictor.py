import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import mean_absolute_error, r2_score
from typing import Dict, List, Tuple
import pickle
import os
from datetime import datetime

class TrafficPredictor:
    """
    ML-based traffic prediction using scikit-learn
    Trained on temporal traffic data to forecast congestion
    """
    
    def __init__(self):
        self.models = {
            'rf': RandomForestRegressor(n_estimators=100, random_state=42),
            'gbr': GradientBoostingRegressor(n_estimators=100, random_state=42)
        }
        self.scaler = StandardScaler()
        self.feature_importance = {}
        self.trained = False
        
    def prepare_features(self, traffic_data: List[Dict]) -> np.ndarray:
        """
        Create features from traffic data
        Features: time of day, day of week, season, geographic location, 
                 historical patterns, road characteristics
        """
        features = []
        
        for data_point in traffic_data:
            feature_vector = []
            
            # Temporal features
            feature_vector.append(data_point['hour'])
            feature_vector.append(data_point['day_of_week'])
            feature_vector.append(np.sin(2 * np.pi * data_point['hour'] / 24))
            feature_vector.append(np.cos(2 * np.pi * data_point['hour'] / 24))
            
            # Day type features
            feature_vector.append(1 if data_point.get('is_weekend', False) else 0)
            feature_vector.append(1 if data_point.get('is_holiday', False) else 0)
            
            # Road features
            feature_vector.append(data_point.get('road_capacity', 1000))
            feature_vector.append(data_point.get('road_condition', 7))
            feature_vector.append(data_point.get('road_length', 5.0))
            
            # Geographic features
            feature_vector.append(data_point.get('from_population', 100000))
            feature_vector.append(data_point.get('to_population', 100000))
            
            # Lagging features (if available)
            for lag in [1, 2, 24]:
                feature_vector.append(
                    data_point.get(f'traffic_lag_{lag}h', 
                                  data_point.get('historical_avg', 1000))
                )
            
            features.append(feature_vector)
            
        return np.array(features)
    
    def train(self, X: np.ndarray, y: np.ndarray) -> Dict:
        """
        Train multiple models and select the best performer
        """
        if len(X) > 0 and isinstance(X[0], dict):
            X = self.prepare_features(X)

        X = np.asarray(X)
        y = np.asarray(y)

        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42
        )
        
        # Scale features
        X_train_scaled = self.scaler.fit_transform(X_train)
        X_test_scaled = self.scaler.transform(X_test)
        
        results = {}
        
        for name, model in self.models.items():
            # Train
            model.fit(X_train_scaled, y_train)
            
            # Predict
            y_pred = model.predict(X_test_scaled)
            
            # Evaluate
            mae = mean_absolute_error(y_test, y_pred)
            r2 = r2_score(y_test, y_pred)
            
            # Feature importance (for tree-based models)
            if hasattr(model, 'feature_importances_'):
                self.feature_importance[name] = dict(
                    zip(range(X.shape[1]), model.feature_importances_)
                )
            
            results[name] = {
                'mae': mae,
                'r2': r2,
                'model': model
            }
            
        self.trained = True
        return results
    
    def predict(self, conditions: Dict, model_name: str = 'rf') -> float:
        """
        Predict traffic volume for given conditions
        """
        if not self.trained:
            raise ValueError("Model must be trained before prediction")
            
        # Prepare feature vector
        feature_vector = self.prepare_features([conditions])
        
        # Scale
        feature_vector_scaled = self.scaler.transform(feature_vector)
        
        # Predict
        if model_name in self.models:
            prediction = self.models[model_name].predict(feature_vector_scaled)[0]
            return max(0, prediction)  # Ensure non-negative
        else:
            return conditions.get('historical_avg', 1000)
    
    def predict_timeseries(self, road_id: str, hours: List[int], 
                          day_type: str = 'weekday') -> List[float]:
        """
        Predict traffic for a road over multiple hours
        """
        predictions = []
        
        for hour in hours:
            conditions = {
                'hour': hour,
                'day_of_week': 1 if day_type == 'weekday' else 6,
                'is_weekend': day_type == 'weekend',
                'is_holiday': False,
                'road_capacity': 3000,
                'road_condition': 7,
                'road_length': 10.0,
                'from_population': 300000,
                'to_population': 300000,
                'historical_avg': 2500
            }
            
            pred = self.predict(conditions)
            predictions.append(pred)
            
        return predictions
    
    def save_model(self, path: str):
        """Save trained models to disk"""
        with open(path, 'wb') as f:
            pickle.dump({
                'models': self.models,
                'scaler': self.scaler,
                'feature_importance': self.feature_importance,
                'trained': self.trained
            }, f)
    
    def load_model(self, path: str):
        """Load trained models from disk"""
        with open(path, 'rb') as f:
            data = pickle.load(f)
            self.models = data['models']
            self.scaler = data['scaler']
            self.feature_importance = data['feature_importance']
            self.trained = data['trained']

def generate_training_data(existing_traffic_data: Dict) -> Tuple[np.ndarray, np.ndarray]:
    """
    Generate synthetic training data from existing traffic patterns
    """
    X, y = [], []
    
    for road_id, pattern in existing_traffic_data.items():
        if isinstance(pattern, dict):
            capacity = pattern.get('capacity', 3000)
            length = pattern.get('length', 5.0)
            current_traffic = lambda hour: pattern.get('historical_avg', 1000)
        else:
            capacity = getattr(pattern, 'capacity', 3000)
            length = getattr(pattern, 'length', 5.0)
            current_traffic = pattern.get_current_traffic

        for hour in range(24):
            # Create multiple synthetic data points with variations
            for _ in range(5):  # 5 samples per hour
                base_traffic = current_traffic(hour)
                features = {
                    'hour': hour,
                    'day_of_week': np.random.randint(0, 7),
                    'is_weekend': np.random.choice([True, False]),
                    'is_holiday': np.random.choice([True, False], p=[0.1, 0.9]),
                    'road_capacity': capacity * np.random.normal(1, 0.1),
                    'road_condition': min(10, max(1, np.random.normal(7, 1.5))),
                    'road_length': length * np.random.normal(1, 0.05),
                    'from_population': np.random.exponential(300000),
                    'to_population': np.random.exponential(300000),
                    'traffic_lag_1h': current_traffic(hour - 1) if hour > 0 else 0,
                    'traffic_lag_2h': current_traffic(hour - 2) if hour > 1 else 0,
                    'traffic_lag_24h': base_traffic * np.random.normal(1, 0.1),
                    'historical_avg': base_traffic
                }
                
                # Target: actual traffic volume with some noise
                traffic = base_traffic * np.random.normal(1, 0.15)
                
                X.append(features)
                y.append(traffic)
    
    return X, y