
import math

def safe_div(a, b):
    return a / b if b != 0 else 0.0

def confusion(y_true, y_pred):
    tp = sum(1 for i in range(len(y_true)) if y_true[i]==1 and y_pred[i]==1)
    tn = sum(1 for i in range(len(y_true)) if y_true[i]==0 and y_pred[i]==0)
    fp = sum(1 for i in range(len(y_true)) if y_true[i]==0 and y_pred[i]==1)
    fn = sum(1 for i in range(len(y_true)) if y_true[i]==1 and y_pred[i]==0)
    return tp, tn, fp, fn

def normalize(score, threshold):
    return min(score / threshold, 1.0) if threshold > 0 else 0.0
