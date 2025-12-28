# ============================================================================
# Automated Data Refresh Job
# ============================================================================
# Schedules and executes automated data extraction and refresh

import schedule
import time
from datetime import datetime
import logging
from pathlib import Path
import pandas as pd
from typing import Optional
import sys

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from data.extractors import CustomerDataExtractor
from data.validators import DataValidator, MissingValueHandler
from monitoring.data_quality import DataQualityMonitor

logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)


class DataRefreshJob:
    """
    Automated data refresh job that extracts, validates, and stores customer data.
    """
    
    def __init__(
        self,
        output_dir: str = './data/refreshed',
        enable_validation: bool = True,
        enable_monitoring: bool = True,
        quality_threshold: float = 70.0
    ):
        """
        Initialize data refresh job.
        
        Args:
            output_dir: Directory to store refreshed data
            enable_validation: Whether to validate data
            enable_monitoring: Whether to monitor quality
            quality_threshold: Minimum acceptable quality score
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        self.extractor = CustomerDataExtractor()
        self.validator = DataValidator()
        self.missing_handler = MissingValueHandler()
        self.monitor = DataQualityMonitor()
        
        self.enable_validation = enable_validation
        self.enable_monitoring = enable_monitoring
        self.quality_threshold = quality_threshold
        
        logger.info("Data refresh job initialized")
    
    def run_refresh(self, dataset_name: str = 'customer_data') -> bool:
        """
        Execute data refresh process.
        
        Args:
            dataset_name: Name of the dataset
            
        Returns:
            True if refresh successful, False otherwise
        """
        logger.info(f"{'='*80}")
        logger.info(f"Starting data refresh job: {dataset_name}")
        logger.info(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        logger.info(f"{'='*80}")
        
        try:
            # Step 1: Extract data
            logger.info("📥 Step 1: Extracting customer data...")
            df = self.extractor.extract_for_prediction()
            logger.info(f"✅ Extracted {len(df)} customer records")
            
            if df.empty:
                logger.error("❌ No data extracted, aborting refresh")
                return False
            
            # Step 2: Validate data
            if self.enable_validation:
                logger.info("\n🔍 Step 2: Validating data quality...")
                validation_result = self.validator.validate(df)
                
                if not validation_result.passed:
                    logger.warning(
                        f"⚠️  Validation found {validation_result.failed_checks} issues"
                    )
                    for error in validation_result.errors[:3]:
                        logger.warning(f"  - {error['rule']}: {error['description']}")
                else:
                    logger.info("✅ Data validation passed")
                
                quality_score = self.validator.get_data_quality_score(df)
                logger.info(f"📊 Data quality score: {quality_score}/100")
                
                if quality_score < self.quality_threshold:
                    logger.error(
                        f"❌ Quality score ({quality_score}) below threshold ({self.quality_threshold}), "
                        f"aborting refresh"
                    )
                    return False
            
            # Step 3: Handle missing values
            logger.info("\n🔧 Step 3: Handling missing values and outliers...")
            missing_stats = self.missing_handler.detect_missing(df)
            
            if not missing_stats.empty:
                logger.info(f"Found missing values in {len(missing_stats)} columns")
                df = self.missing_handler.impute_missing(df, strategy='median')
                logger.info("✅ Missing values imputed")
            else:
                logger.info("✅ No missing values detected")
            
            # Step 4: Monitor quality
            if self.enable_monitoring:
                logger.info("\n📊 Step 4: Monitoring data quality...")
                self.monitor.monitor_and_alert(df, dataset_name, self.quality_threshold)
                
                # Generate and save report
                report = self.monitor.generate_quality_report(df, dataset_name)
                report_file = self.output_dir / f"{dataset_name}_quality_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
                with open(report_file, 'w', encoding='utf-8') as f:
                    f.write(report)
                logger.info(f"✅ Quality report saved to {report_file}")
            
            # Step 5: Save refreshed data
            logger.info("\n💾 Step 5: Saving refreshed data...")
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            output_file = self.output_dir / f"{dataset_name}_{timestamp}.csv"
            df.to_csv(output_file, index=False)
            logger.info(f"✅ Data saved to {output_file}")
            
            # Also save as latest
            latest_file = self.output_dir / f"{dataset_name}_latest.csv"
            df.to_csv(latest_file, index=False)
            logger.info(f"✅ Latest data saved to {latest_file}")
            
            # Step 6: Version tracking
            self._save_version_info(dataset_name, df, timestamp)
            
            logger.info(f"\n{'='*80}")
            logger.info(f"✅ Data refresh completed successfully")
            logger.info(f"{'='*80}\n")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Data refresh failed: {str(e)}", exc_info=True)
            return False
    
    def _save_version_info(self, dataset_name: str, df: pd.DataFrame, timestamp: str):
        """Save version information for data versioning."""
        version_info = {
            'dataset_name': dataset_name,
            'timestamp': timestamp,
            'row_count': len(df),
            'column_count': len(df.columns),
            'columns': list(df.columns),
            'file_size_mb': df.memory_usage(deep=True).sum() / 1024**2,
            'created_at': datetime.now().isoformat()
        }
        
        version_file = self.output_dir / f"{dataset_name}_versions.json"
        
        # Load existing versions
        import json
        if version_file.exists():
            with open(version_file, 'r') as f:
                versions = json.load(f)
        else:
            versions = []
        
        # Append new version
        versions.append(version_info)
        
        # Keep only last 100 versions
        versions = versions[-100:]
        
        # Save
        with open(version_file, 'w') as f:
            json.dump(versions, f, indent=2)
        
        logger.info(f"✅ Version info saved (total versions: {len(versions)})")
    
    def schedule_hourly(self, dataset_name: str = 'customer_data'):
        """Schedule job to run every hour."""
        schedule.every().hour.do(self.run_refresh, dataset_name=dataset_name)
        logger.info(f"📅 Scheduled hourly refresh for {dataset_name}")
    
    def schedule_daily(self, time_str: str = "02:00", dataset_name: str = 'customer_data'):
        """
        Schedule job to run daily at specific time.
        
        Args:
            time_str: Time in HH:MM format (24-hour)
            dataset_name: Name of the dataset
        """
        schedule.every().day.at(time_str).do(self.run_refresh, dataset_name=dataset_name)
        logger.info(f"📅 Scheduled daily refresh for {dataset_name} at {time_str}")
    
    def schedule_custom(self, interval_minutes: int, dataset_name: str = 'customer_data'):
        """
        Schedule job to run every N minutes.
        
        Args:
            interval_minutes: Interval in minutes
            dataset_name: Name of the dataset
        """
        schedule.every(interval_minutes).minutes.do(self.run_refresh, dataset_name=dataset_name)
        logger.info(f"📅 Scheduled refresh for {dataset_name} every {interval_minutes} minutes")
    
    def run_scheduler(self):
        """Run the scheduler (blocking)."""
        logger.info("🚀 Starting data refresh scheduler...")
        logger.info(f"Scheduled jobs: {len(schedule.jobs)}")
        
        try:
            while True:
                schedule.run_pending()
                time.sleep(60)  # Check every minute
        except KeyboardInterrupt:
            logger.info("\n⏹️  Scheduler stopped by user")
        except Exception as e:
            logger.error(f"❌ Scheduler error: {str(e)}", exc_info=True)


def main():
    """Main entry point for the data refresh job."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Automated Data Refresh Job')
    parser.add_argument('--mode', choices=['once', 'hourly', 'daily', 'custom'], 
                       default='once', help='Run mode')
    parser.add_argument('--time', default='02:00', help='Time for daily run (HH:MM)')
    parser.add_argument('--interval', type=int, default=60, help='Interval in minutes for custom mode')
    parser.add_argument('--dataset', default='customer_data', help='Dataset name')
    parser.add_argument('--output-dir', default='./data/refreshed', help='Output directory')
    parser.add_argument('--quality-threshold', type=float, default=70.0, 
                       help='Minimum quality score')
    
    args = parser.parse_args()
    
    # Initialize job
    job = DataRefreshJob(
        output_dir=args.output_dir,
        enable_validation=True,
        enable_monitoring=True,
        quality_threshold=args.quality_threshold
    )
    
    if args.mode == 'once':
        # Run once
        success = job.run_refresh(args.dataset)
        sys.exit(0 if success else 1)
        
    elif args.mode == 'hourly':
        # Schedule hourly
        job.schedule_hourly(args.dataset)
        job.run_scheduler()
        
    elif args.mode == 'daily':
        # Schedule daily
        job.schedule_daily(args.time, args.dataset)
        job.run_scheduler()
        
    elif args.mode == 'custom':
        # Schedule custom interval
        job.schedule_custom(args.interval, args.dataset)
        job.run_scheduler()


if __name__ == "__main__":
    main()
