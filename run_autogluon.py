# %%
import yaml
import pandas as pd
from autogluon.tabular import TabularPredictor
from autogluon.features.generators import AutoMLPipelineFeatureGenerator
# %%

def run_with_config(config_path, train_data_path, label=None):
    """
    Load configuration from YAML and run AutoGluon TabularPredictor.
    """
    # Load YAML config
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)
    
    # Load data
    train_data = pd.read_csv(train_data_path)
    
    # Override label from config if provided in function call
    if label:
        config['predictor_init']['label'] = label
    
    print(f"Initializing TabularPredictor with label: {config['predictor_init']['label']}")
    
    # Configure custom feature generator if provided
    feature_generator = None
    if 'feature_generator_args' in config:
        feature_generator = AutoMLPipelineFeatureGenerator(**config['feature_generator_args'])
    
    # Initialize Predictor
    predictor = TabularPredictor(**config['predictor_init'])
    
    # Run fit
    predictor.fit(
        train_data=train_data,
        feature_generator=feature_generator,
        **config['fit_args'],
        hyperparameters=config.get('hyperparameters'),
        ag_args_fit=config.get('ag_args_fit')
    )
    
    print("Training Completed.")
    print("Leaderboard:")
    print(predictor.leaderboard())
    
    return predictor

if __name__ == "__main__":
    # %%

    data_url = 'https://raw.githubusercontent.com/mli/ag-docs/main/knot_theory/'
    train_data = TabularDataset(f'{data_url}train.csv')
    train_data.head()

# %%
    # This is a demonstration. To run this, you need a training CSV.
    predictor = run_with_config('autogluon_config.yaml', 'train.csv')
    print("Configuration script loaded. Example usage:")
    print("python run_autogluon.py  # (Update paths in __main__ inside the script)")
    
    # Dummy creation logic if user wants to test immediately
    print("\nNote: To test this, ensure you have a 'train.csv' and run the commented out line.")
