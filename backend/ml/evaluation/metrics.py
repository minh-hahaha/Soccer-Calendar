import numpy as np
from typing import List, Tuple
from sklearn.metrics import accuracy_score, log_loss, confusion_matrix


def calculate_brier_score(y_true: np.ndarray, y_pred_proba: np.ndarray) -> float:
    """Calculate Brier score for multiclass classification"""
    # Convert labels to one-hot encoding if needed
    if len(y_true.shape) == 1:
        # Convert to one-hot
        n_classes = y_pred_proba.shape[1]
        y_true_one_hot = np.zeros((len(y_true), n_classes))
        y_true_one_hot[np.arange(len(y_true)), y_true] = 1
    else:
        y_true_one_hot = y_true
    
    # Calculate Brier score
    brier_score = np.mean(np.sum((y_true_one_hot - y_pred_proba) ** 2, axis=1))
    return brier_score


def calculate_calibration_metrics(y_true: np.ndarray, y_pred_proba: np.ndarray) -> dict:
    """Calculate calibration metrics"""
    if len(y_true.shape) == 1:
        # Convert to one-hot
        n_classes = y_pred_proba.shape[1]
        y_true_one_hot = np.zeros((len(y_true), n_classes))
        y_true_one_hot[np.arange(len(y_true)), y_true] = 1
    else:
        y_true_one_hot = y_true
    
    # Calculate reliability diagram
    n_bins = 10
    bin_boundaries = np.linspace(0, 1, n_bins + 1)
    bin_lowers = bin_boundaries[:-1]
    bin_uppers = bin_boundaries[1:]
    
    calibration_errors = []
    confidences = []
    accuracies = []
    
    for bin_lower, bin_upper in zip(bin_lowers, bin_uppers):
        # Find predictions in this bin
        in_bin = np.logical_and(y_pred_proba.max(axis=1) > bin_lower,
                               y_pred_proba.max(axis=1) <= bin_upper)
        
        if np.sum(in_bin) > 0:
            # Calculate accuracy and confidence for this bin
            bin_acc = np.mean(y_true_one_hot[in_bin].argmax(axis=1) == y_pred_proba[in_bin].argmax(axis=1))
            bin_conf = np.mean(y_pred_proba[in_bin].max(axis=1))
            
            # Calculate calibration error
            calibration_error = np.abs(bin_conf - bin_acc)
            
            calibration_errors.append(calibration_error)
            confidences.append(bin_conf)
            accuracies.append(bin_acc)
    
    # Calculate ECE (Expected Calibration Error)
    ece = np.mean(calibration_errors) if calibration_errors else 0.0
    
    return {
        'ece': ece,
        'calibration_errors': calibration_errors,
        'confidences': confidences,
        'accuracies': accuracies
    }


def calculate_multiclass_metrics(y_true: np.ndarray, y_pred: np.ndarray, 
                                y_pred_proba: np.ndarray) -> dict:
    """Calculate comprehensive multiclass metrics"""
    # Basic metrics
    accuracy = accuracy_score(y_true, y_pred)
    logloss = log_loss(y_true, y_pred_proba)
    brier = calculate_brier_score(y_true, y_pred_proba)
    
    # Confusion matrix
    cm = confusion_matrix(y_true, y_pred)
    
    # Per-class metrics
    n_classes = len(np.unique(y_true))
    precision = np.zeros(n_classes)
    recall = np.zeros(n_classes)
    f1 = np.zeros(n_classes)
    
    for i in range(n_classes):
        tp = cm[i, i]
        fp = np.sum(cm[:, i]) - tp
        fn = np.sum(cm[i, :]) - tp
        
        precision[i] = tp / (tp + fp) if (tp + fp) > 0 else 0
        recall[i] = tp / (tp + fn) if (tp + fn) > 0 else 0
        f1[i] = 2 * (precision[i] * recall[i]) / (precision[i] + recall[i]) if (precision[i] + recall[i]) > 0 else 0
    
    # Macro averages
    macro_precision = np.mean(precision)
    macro_recall = np.mean(recall)
    macro_f1 = np.mean(f1)
    
    # Calibration metrics
    calibration = calculate_calibration_metrics(y_true, y_pred_proba)
    
    return {
        'accuracy': accuracy,
        'logloss': logloss,
        'brier_score': brier,
        'precision': precision.tolist(),
        'recall': recall.tolist(),
        'f1': f1.tolist(),
        'macro_precision': macro_precision,
        'macro_recall': macro_recall,
        'macro_f1': macro_f1,
        'confusion_matrix': cm.tolist(),
        'calibration': calibration
    }


def format_metrics_report(metrics: dict) -> str:
    """Format metrics into a readable report"""
    report = []
    report.append("=" * 50)
    report.append("MODEL EVALUATION REPORT")
    report.append("=" * 50)
    
    report.append(f"Accuracy: {metrics['accuracy']:.4f}")
    report.append(f"Log Loss: {metrics['logloss']:.4f}")
    report.append(f"Brier Score: {metrics['brier_score']:.4f}")
    report.append(f"Expected Calibration Error: {metrics['calibration']['ece']:.4f}")
    
    report.append("\nPer-Class Metrics:")
    report.append("-" * 30)
    classes = ["Away Win", "Draw", "Home Win"]
    for i, class_name in enumerate(classes):
        report.append(f"{class_name}:")
        report.append(f"  Precision: {metrics['precision'][i]:.4f}")
        report.append(f"  Recall: {metrics['recall'][i]:.4f}")
        report.append(f"  F1: {metrics['f1'][i]:.4f}")
    
    report.append(f"\nMacro Averages:")
    report.append(f"  Precision: {metrics['macro_precision']:.4f}")
    report.append(f"  Recall: {metrics['macro_recall']:.4f}")
    report.append(f"  F1: {metrics['macro_f1']:.4f}")
    
    return "\n".join(report)
