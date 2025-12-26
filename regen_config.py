"""regen_config.py

Simple utility to (re)generate `autogluon_config.yaml` from a template
and allow small overrides via CLI arguments.

Usage examples:
  python regen_config.py                    # regenerate with defaults
  python regen_config.py --label my_target --time-limit 7200
  python regen_config.py --problem-type null --num-bag-folds null

The script makes a timestamped backup of the existing config before overwriting.
"""
from __future__ import annotations
import argparse
import datetime
import os
import shutil
import textwrap
from typing import Optional

CONFIG_PATH = "autogluon_config.yaml"

TEMPLATE = textwrap.dedent("""\
# AutoGluon TabularPredictor Configuration File
# This file contains common and advanced parameters for TabularPredictor and its fit() method.

predictor_init:
  # Mandatory: Name of the column that contains the target variable to be predicted.
  label: {label}
  
  # Directory path where trained models and artifacts will be saved.
  path: {path}
  
  # Problem type: 'binary', 'multiclass', 'regression', 'quantile', 'softclass', or null (infer)
  problem_type: {problem_type}
  
  # Metric to optimize. If null, chosen automatically based on problem_type.
  eval_metric: {eval_metric}
  
  # Control output detail. 0: silent, 1: normal, 2: info, 3: debug, 4: everything.
  verbosity: {verbosity}
  
  # List of column names to ignore during training.
  # ignored_columns: {ignored_columns}
  
  # Sample weight column name.
  # sample_weight: "{sample_weight}"
  
  # Whether to use sample weights during evaluation.
  weight_evaluation: {weight_evaluation}

fit_args:
  # Training time limit in seconds.
  time_limit: {time_limit}
  
  # Selection of predefined settings:
  presets: {presets}
  
  # Number of folds for bagging (e.g., 5, 10). Set to 0 to disable. null = auto.
  num_bag_folds: {num_bag_folds}
  
  # Number of stacking levels (e.g., 1, 2, 3). null = auto.
  num_stack_levels: {num_stack_levels}
  
  # Whether to fit a weighted ensemble in each stack layer. (True/False)
  fit_weighted_ensemble: {fit_weighted_ensemble}
  
  # Whether to calibrate decision threshold at the end of fit (for classification).
  calibrate_decision_threshold: {calibrate_decision_threshold}
  
  # Number of CPU cores to use. ('auto' or integer)
  num_cpus: {num_cpus}
  
  # Number of GPUs to use. ('auto' or integer)
  num_gpus: {num_gpus}

hyperparameters:
  GBM: {{}}
  NN_TORCH: {{}}
  CAT: {{}}
  RF:
    n_estimators: 100
    ag_args:
      name_suffix: "_Large"
  XT: {{}}
  FASTAI: {{}}

ag_args_fit:
  # Global constraints for all models.

feature_generator_args:
  enable_numeric_features: true
  enable_categorical_features: true
  enable_datetime_features: true
  enable_text_special_features: true
  enable_text_ngram_features: true
  enable_raw_text_features: false
""")


def yaml_val(value: Optional[object]) -> str:
    """Render a simple Python value to a YAML textual representation used in our template.

    - None -> null
    - bool -> true/false
    - str -> quoted string (single quotes)
    - lists -> YAML list inline
    - numbers -> as-is
    """
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (int, float)):
        return str(value)
    if isinstance(value, (list, tuple)):
        if not value:
            return "[]"
        inner = ", ".join([yaml_val(v) for v in value])
        return f"[{inner}]"
    # Strings: protect with single quotes and escape single quotes inside
    s = str(value).replace("'", "''")
    return f"'{s}'"


def backup_existing(path: str) -> None:
    if not os.path.exists(path):
        return
    ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = f"bak.{ts}.{path}"
    shutil.copy2(path, backup_path)
    print(f"Backup created: {backup_path}")


def generate_config(args: argparse.Namespace) -> str:
    subs = {
        'label': yaml_val(args.label),
        'path': yaml_val(args.path),
        'problem_type': 'null' if args.problem_type in (None, 'null') else yaml_val(args.problem_type),
        'eval_metric': 'null' if args.eval_metric in (None, 'null') else yaml_val(args.eval_metric),
        'verbosity': yaml_val(args.verbosity),
        'ignored_columns': yaml_val(args.ignored_columns),
        'sample_weight': yaml_val(args.sample_weight),
        'weight_evaluation': yaml_val(args.weight_evaluation),
        'time_limit': 'null' if args.time_limit in (None, 'null') else yaml_val(args.time_limit),
        'presets': yaml_val(args.presets),
        'num_bag_folds': 'null' if args.num_bag_folds in (None, 'null') else yaml_val(args.num_bag_folds),
        'num_stack_levels': 'null' if args.num_stack_levels in (None, 'null') else yaml_val(args.num_stack_levels),
        'fit_weighted_ensemble': yaml_val(args.fit_weighted_ensemble),
        'calibrate_decision_threshold': yaml_val(args.calibrate_decision_threshold),
        'num_cpus': yaml_val(args.num_cpus),
        'num_gpus': yaml_val(args.num_gpus),
    }
    return TEMPLATE.format(**subs)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Regenerate autogluon_config.yaml from a template with optional overrides.")
    parser.add_argument('--label', default='target', help='Target column name')
    parser.add_argument('--path', default='AutogluonModels/ag-config-test', help='Model output path')
    parser.add_argument('--problem-type', default=None, help="Problem type or 'null' to infer")
    parser.add_argument('--eval-metric', default='f1_macro', help="Evaluation metric or 'null'")
    parser.add_argument('--verbosity', default=2, type=int, help='Verbosity level (0-4)')
    parser.add_argument('--ignored-columns', nargs='*', default=[], help='Columns to ignore (space separated)')
    parser.add_argument('--sample-weight', default='', help='Sample weight column name (leave empty for none)')

    # Whether to use sample weights during evaluation (enable/disable flags)
    parser.add_argument('--weight-evaluation', dest='weight_evaluation', action='store_true',
                        help='Enable use of sample weights during evaluation')
    parser.add_argument('--no-weight-evaluation', dest='weight_evaluation', action='store_false',
                        help='Disable use of sample weights during evaluation')
    parser.set_defaults(weight_evaluation=False)

    parser.add_argument('--time-limit', default=3600, help="Time limit in seconds (or 'null')")
    parser.add_argument('--presets', default='medium_quality', help='Preset string')
    parser.add_argument('--num-bag-folds', default=None, help="Number of bag folds (int) or 'null'")
    parser.add_argument('--num-stack-levels', default=None, help="Number of stack levels (int) or 'null')")
    parser.add_argument('--fit-weighted-ensemble', action='store_true', help='Enable fit weighted ensemble')
    parser.add_argument('--no-fit-weighted-ensemble', dest='fit_weighted_ensemble', action='store_false')
    parser.set_defaults(fit_weighted_ensemble=True)
    parser.add_argument('--calibrate-decision-threshold', default='auto', help="True/False/'auto'")
    parser.add_argument('--num-cpus', default='auto', help="'auto' or int")
    parser.add_argument('--num-gpus', default='auto', help="'auto' or int")
    parser.add_argument('--config-path', default=CONFIG_PATH, help="Path to write config file (must end with .yaml or .yml)")
    parser.add_argument('--backup', dest='backup', action='store_true', help='Create timestamped backup of existing config')
    parser.add_argument('--no-backup', dest='backup', action='store_false', help='Do not create backup of existing config')
    parser.set_defaults(backup=True)

    return parser.parse_args()


def main() -> int:
    args = parse_args()

    # Normalize some inputs
    if args.sample_weight == '':
        args.sample_weight = None
    if args.ignored_columns == []:
        args.ignored_columns = []

    # Convert numeric-like args from strings 'null' to None
    for attr in ('time_limit', 'num_bag_folds', 'num_stack_levels'):
        val = getattr(args, attr)
        if isinstance(val, str) and val.lower() == 'null':
            setattr(args, attr, None)

    # Determine config path and ensure it ends with .yaml or .yml
    config_path = args.config_path
    if not config_path.lower().endswith(('.yaml', '.yml')):
        config_path = f"{config_path}.yaml"
        print(f"Config path didn't end with .yaml/.yml; using '{config_path}'")
    if args.backup:
        backup_existing(config_path)

    content = generate_config(args)
    print(config_path)
    with open(config_path, 'w', encoding='utf-8') as f:
        f.write(content)

    print(f"Wrote {config_path} (use --backup/--no-backup to control creating backups)")
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
