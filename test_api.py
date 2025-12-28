# ============================================================================
# API TESTING SCRIPT
# ============================================================================
# Test the churn prediction API with sample requests

import requests
import json
from pprint import pprint

# API base URL
BASE_URL = "http://localhost:8000"

def test_health_check():
    """Test the health check endpoint"""
    print("\n" + "="*70)
    print("TEST 1: Health Check")
    print("="*70)
    
    response = requests.get(f"{BASE_URL}/health")
    print(f"Status Code: {response.status_code}")
    pprint(response.json())
    return response.status_code == 200

def test_single_prediction():
    """Test single customer prediction"""
    print("\n" + "="*70)
    print("TEST 2: Single Customer Prediction")
    print("="*70)
    
    # Sample customer data
    payload = {
        "customer_id": "CUST_12345",
        "features": {
            "tenure_months": 24.5,
            "monthly_charges": 65.50,
            "total_charges": 1572.00,
            "service_calls": 2.0,
            "contract_duration": "Two-Year",
            "paperless_billing": 1.2,
            "tech_support": 0.9,
            "online_backup": 0.3,
            "payment_method": "Credit Card",
            "internet_service": 0.8,
            "streaming_tv": 0.5,
            "streaming_movies": 0.6,
            "device_protection": 0.2,
            "online_security": 0.7,
            "senior_citizen": 0.1
        },
        "threshold": 0.5
    }
    
    response = requests.post(f"{BASE_URL}/predict", json=payload)
    print(f"Status Code: {response.status_code}")
    pprint(response.json())
    return response.status_code == 200

def test_batch_prediction():
    """Test batch prediction"""
    print("\n" + "="*70)
    print("TEST 3: Batch Prediction (3 Customers)")
    print("="*70)
    
    # Sample batch data
    payload = {
        "customers": [
            {
                "customer_id": "CUST_001",
                "tenure_months": 3.0,
                "monthly_charges": 45.00,
                "total_charges": 135.00,
                "service_calls": 5.0,
                "contract_duration": "Monthly",
                "paperless_billing": -0.3,
                "tech_support": -1.1,
                "online_backup": 0.1,
                "payment_method": "Electronic",
                "internet_service": 0.2,
                "streaming_tv": -0.3,
                "streaming_movies": 0.0,
                "device_protection": -0.5,
                "online_security": -0.8,
                "senior_citizen": -0.2
            },
            {
                "customer_id": "CUST_002",
                "tenure_months": 36.0,
                "monthly_charges": 75.25,
                "total_charges": 2709.00,
                "service_calls": 0.0,
                "contract_duration": "Yearly",
                "paperless_billing": 0.8,
                "tech_support": 0.5,
                "online_backup": -0.7,
                "payment_method": "Bank Transfer",
                "internet_service": 1.1,
                "streaming_tv": 0.9,
                "streaming_movies": 0.7,
                "device_protection": 0.4,
                "online_security": 0.3,
                "senior_citizen": 1.5
            },
            {
                "customer_id": "CUST_003",
                "tenure_months": 12.0,
                "monthly_charges": 55.00,
                "total_charges": 660.00,
                "service_calls": 3.0,
                "contract_duration": "Monthly",
                "paperless_billing": 0.2,
                "tech_support": 0.0,
                "online_backup": 0.5,
                "payment_method": "Credit Card",
                "internet_service": 0.6,
                "streaming_tv": 0.3,
                "streaming_movies": 0.4,
                "device_protection": 0.1,
                "online_security": 0.2,
                "senior_citizen": 0.0
            }
        ],
        "threshold": 0.5
    }
    
    response = requests.post(f"{BASE_URL}/predict_batch", json=payload)
    print(f"Status Code: {response.status_code}")
    result = response.json()
    
    print("\nSummary:")
    pprint(result['summary'])
    
    print("\nIndividual Predictions:")
    for pred in result['predictions']:
        print(f"\n  Customer: {pred['customer_id']}")
        print(f"  Churn Probability: {pred['churn_probability']:.2%}")
        print(f"  Prediction: {pred['churn_prediction']}")
        print(f"  Risk Level: {pred['risk_level']}")
    
    return response.status_code == 200

def test_model_info():
    """Test model information endpoint"""
    print("\n" + "="*70)
    print("TEST 4: Model Information")
    print("="*70)
    
    response = requests.get(f"{BASE_URL}/model_info")
    print(f"Status Code: {response.status_code}")
    pprint(response.json())
    return response.status_code == 200

def run_all_tests():
    """Run all tests"""
    print("\n" + "="*70)
    print("CHURN PREDICTION API - TEST SUITE")
    print("="*70)
    print(f"Testing API at: {BASE_URL}")
    
    results = {
        "Health Check": False,
        "Single Prediction": False,
        "Batch Prediction": False,
        "Model Info": False
    }
    
    try:
        results["Health Check"] = test_health_check()
    except Exception as e:
        print(f"❌ Health check failed: {str(e)}")
    
    try:
        results["Single Prediction"] = test_single_prediction()
    except Exception as e:
        print(f"❌ Single prediction failed: {str(e)}")
    
    try:
        results["Batch Prediction"] = test_batch_prediction()
    except Exception as e:
        print(f"❌ Batch prediction failed: {str(e)}")
    
    try:
        results["Model Info"] = test_model_info()
    except Exception as e:
        print(f"❌ Model info failed: {str(e)}")
    
    # Summary
    print("\n" + "="*70)
    print("TEST SUMMARY")
    print("="*70)
    for test_name, passed in results.items():
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"{test_name}: {status}")
    
    total_passed = sum(results.values())
    total_tests = len(results)
    print(f"\nTotal: {total_passed}/{total_tests} tests passed")

if __name__ == "__main__":
    run_all_tests()
