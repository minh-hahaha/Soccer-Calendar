import typer
from typing import Optional
import json
from datetime import datetime

from ml.evaluation.learn_from_mistakes import (
    analyze_recent_predictions, 
    retrain_with_new_data,
    PredictionErrorAnalyzer,
    ModelRetrainer
)
from database.db import get_db

app = typer.Typer()


@app.command()
def analyze(
    days_back: int = typer.Option(7, help="Number of days back to analyze"),
    season: Optional[int] = typer.Option(None, help="Specific season to analyze"),
    matchday: Optional[int] = typer.Option(None, help="Specific matchday to analyze"),
    output_file: Optional[str] = typer.Option(None, help="Save analysis to JSON file")
):
    """Analyze recent prediction errors and performance"""
    
    print(f"🔍 Analyzing predictions from the last {days_back} days...")
    
    db = next(get_db())
    analyzer = PredictionErrorAnalyzer(db)
    
    # Get finished matches with predictions
    df = analyzer.get_finished_matches_with_predictions(
        season=season,
        matchday=matchday,
        days_back=days_back
    )
    
    if df.empty:
        print("❌ No finished matches with predictions found in the specified period")
        return
    
    # Analyze errors
    analysis = analyzer.analyze_prediction_errors(df)
    
    # Print results
    print("\n📊 PREDICTION ANALYSIS RESULTS")
    print("=" * 50)
    print(f"Total matches analyzed: {analysis['total_matches']}")
    print(f"Overall accuracy: {analysis['overall_accuracy']:.2%}")
    print(f"Average log loss: {analysis['average_log_loss']:.4f}")
    
    print(f"\n✅ Correct predictions: {analysis['error_distribution']['correct_predictions']}")
    print(f"❌ Incorrect predictions: {analysis['error_distribution']['incorrect_predictions']}")
    
    print(f"\n🏆 Outcome distribution:")
    print(f"  Home wins: {analysis['outcome_analysis']['home_wins']}")
    print(f"  Draws: {analysis['outcome_analysis']['draws']}")
    print(f"  Away wins: {analysis['outcome_analysis']['away_wins']}")
    
    print(f"\n🎯 Confidence analysis:")
    print(f"  High confidence errors (>60%): {analysis['confidence_analysis']['high_confidence_errors']}")
    print(f"  Low confidence correct (<40%): {analysis['confidence_analysis']['low_confidence_correct']}")
    print(f"  Average confidence: {analysis['confidence_analysis']['average_confidence']:.2%}")
    
    if analysis['worst_predictions']:
        print(f"\n🔥 WORST 5 PREDICTIONS:")
        for i, pred in enumerate(analysis['worst_predictions'][:5], 1):
            status = "✅" if pred['accuracy'] else "❌"
            print(f"  {i}. Match {pred['match_id']}: Log Loss {pred['log_loss_error']:.4f}, "
                  f"Confidence {pred['confidence']:.2%} {status}")
    
    if analysis['best_predictions']:
        print(f"\n⭐ BEST 5 PREDICTIONS:")
        for i, pred in enumerate(analysis['best_predictions'][:5], 1):
            status = "✅" if pred['accuracy'] else "❌"
            print(f"  {i}. Match {pred['match_id']}: Log Loss {pred['log_loss_error']:.4f}, "
                  f"Confidence {pred['confidence']:.2%} {status}")
    
    # Save to file if requested
    if output_file:
        with open(output_file, 'w') as f:
            json.dump(analysis, f, indent=2, default=str)
        print(f"\n💾 Analysis saved to {output_file}")


@app.command()
def retrain(
    algorithm: str = typer.Option("xgb", help="Algorithm: xgb, rf, lr"),
    days_back: int = typer.Option(30, help="Include matches from last N days"),
    error_weighting: bool = typer.Option(True, help="Apply error weighting to focus on mistakes"),
    force: bool = typer.Option(False, help="Force retraining even if no new data")
):
    """Retrain model with new finished matches and learn from mistakes"""
    
    print(f"🔄 Retraining {algorithm.upper()} model...")
    print(f"📅 Including matches from last {days_back} days")
    print(f"⚖️  Error weighting: {'Enabled' if error_weighting else 'Disabled'}")
    
    # First check if we have new data
    db = next(get_db())
    analyzer = PredictionErrorAnalyzer(db)
    
    new_matches_df = analyzer.get_finished_matches_with_predictions(days_back=days_back)
    
    if new_matches_df.empty and not force:
        print("❌ No new finished matches found for retraining")
        print("💡 Use --force to retrain anyway, or wait for more matches to finish")
        return
    
    if not new_matches_df.empty:
        print(f"📊 Found {len(new_matches_df)} new finished matches for retraining")
        
        # Quick analysis of new data
        new_analysis = analyzer.analyze_prediction_errors(new_matches_df)
        print(f"   Accuracy on new data: {new_analysis['overall_accuracy']:.2%}")
        print(f"   Average log loss: {new_analysis['average_log_loss']:.4f}")
    
    # Retrain model
    retrainer = ModelRetrainer(db)
    result = retrainer.retrain_model(
        algorithm=algorithm,
        new_matches_days_back=days_back,
        error_weighting=error_weighting
    )
    
    if result.get("error"):
        print(f"❌ Retraining failed: {result['error']}")
        return
    
    print("\n✅ RETRAINING COMPLETED")
    print("=" * 30)
    print(f"Algorithm: {result['algorithm'].upper()}")
    print(f"Original samples: {result['original_samples']}")
    print(f"New samples: {result['new_samples']}")
    print(f"Train accuracy: {result['metrics']['train_accuracy']:.4f}")
    print(f"Val accuracy: {result['metrics']['val_accuracy']:.4f}")
    print(f"Train log loss: {result['metrics']['train_logloss']:.4f}")
    print(f"Val log loss: {result['metrics']['val_logloss']:.4f}")


@app.command()
def compare(
    days_back: int = typer.Option(7, help="Number of days back to compare"),
    algorithm: str = typer.Option("xgb", help="Algorithm to retrain with")
):
    """Compare old vs new model performance on recent data"""
    
    print(f"🔍 Comparing model performance on last {days_back} days...")
    
    db = next(get_db())
    analyzer = PredictionErrorAnalyzer(db)
    
    # Get recent finished matches
    df = analyzer.get_finished_matches_with_predictions(days_back=days_back)
    
    if df.empty:
        print("❌ No finished matches found for comparison")
        return
    
    # Analyze current performance
    current_analysis = analyzer.analyze_prediction_errors(df)
    
    print(f"\n📊 CURRENT MODEL PERFORMANCE:")
    print(f"Accuracy: {current_analysis['overall_accuracy']:.2%}")
    print(f"Log Loss: {current_analysis['average_log_loss']:.4f}")
    
    # Retrain model
    print(f"\n🔄 Retraining model with {algorithm.upper()}...")
    retrainer = ModelRetrainer(db)
    retrain_result = retrainer.retrain_model(
        algorithm=algorithm,
        new_matches_days_back=days_back,
        error_weighting=True
    )
    
    if retrain_result.get("error"):
        print(f"❌ Retraining failed: {retrain_result['error']}")
        return
    
    print(f"\n✅ NEW MODEL PERFORMANCE:")
    print(f"Train accuracy: {retrain_result['metrics']['train_accuracy']:.4f}")
    print(f"Val accuracy: {retrain_result['metrics']['val_accuracy']:.4f}")
    print(f"Train log loss: {retrain_result['metrics']['train_logloss']:.4f}")
    print(f"Val log loss: {retrain_result['metrics']['val_logloss']:.4f}")
    
    # Calculate improvement
    accuracy_improvement = retrain_result['metrics']['val_accuracy'] - current_analysis['overall_accuracy']
    logloss_improvement = current_analysis['average_log_loss'] - retrain_result['metrics']['val_logloss']
    
    print(f"\n📈 IMPROVEMENT:")
    print(f"Accuracy: {accuracy_improvement:+.2%}")
    print(f"Log Loss: {logloss_improvement:+.4f} (lower is better)")


@app.command()
def monitor(
    interval_hours: int = typer.Option(24, help="Check every N hours"),
    auto_retrain: bool = typer.Option(False, help="Automatically retrain if performance drops"),
    min_matches: int = typer.Option(5, help="Minimum matches needed for analysis")
):
    """Monitor prediction performance and optionally auto-retrain"""
    
    print(f"👀 Starting performance monitoring...")
    print(f"⏰ Check interval: {interval_hours} hours")
    print(f"🤖 Auto-retrain: {'Enabled' if auto_retrain else 'Disabled'}")
    print(f"📊 Min matches for analysis: {min_matches}")
    
    import time
    from datetime import datetime, timedelta
    
    while True:
        print(f"\n🕐 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - Checking performance...")
        
        # Analyze recent performance
        db = next(get_db())
        analyzer = PredictionErrorAnalyzer(db)
        
        # Check last 7 days
        df = analyzer.get_finished_matches_with_predictions(days_back=7)
        
        if len(df) < min_matches:
            print(f"📊 Only {len(df)} matches in last 7 days (need {min_matches})")
        else:
            analysis = analyzer.analyze_prediction_errors(df)
            accuracy = analysis['overall_accuracy']
            logloss = analysis['average_log_loss']
            
            print(f"📊 Performance: {accuracy:.2%} accuracy, {logloss:.4f} log loss")
            
            # Check if performance is poor and auto-retrain is enabled
            if auto_retrain and accuracy < 0.4:  # Less than 40% accuracy
                print(f"⚠️  Poor performance detected! Auto-retraining...")
                retrainer = ModelRetrainer(db)
                result = retrainer.retrain_model(
                    algorithm="xgb",
                    new_matches_days_back=30,
                    error_weighting=True
                )
                
                if result.get("success"):
                    print(f"✅ Auto-retraining completed. New accuracy: {result['metrics']['val_accuracy']:.2%}")
                else:
                    print(f"❌ Auto-retraining failed: {result.get('error')}")
        
        print(f"😴 Sleeping for {interval_hours} hours...")
        time.sleep(interval_hours * 3600)


if __name__ == "__main__":
    app()
