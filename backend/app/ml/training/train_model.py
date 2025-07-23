import os
import pickle
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split, GridSearchCV
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, classification_report

# Importar generador de datos si no existen los datos
from app.ml.training.data_generator import generate_training_data

def train_model():
    """Entrena un modelo de recomendación y lo guarda."""
    
    # Verificar si ya existen datos de entrenamiento
    data_file = "app/ml/training/data/training_data.csv"
    
    if os.path.exists(data_file):
        print("Cargando datos existentes...")
        data = pd.read_csv(data_file)
        X = data.drop('match', axis=1)
        y = data['match']
    else:
        print("Generando nuevos datos de entrenamiento...")
        X, y, _, _, _ = generate_training_data()
    
    # Dividir en conjuntos de entrenamiento y prueba
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    
    print("Entrenando modelo de recomendación...")
    
    # Definir modelo y parámetros para búsqueda de hiperparámetros
    model = RandomForestClassifier(random_state=42)
    param_grid = {
        'n_estimators': [50, 100],
        'max_depth': [None, 10, 20],
        'min_samples_split': [2, 5],
        'min_samples_leaf': [1, 2]
    }
    
    # Para un anteproyecto, simplificar la búsqueda de hiperparámetros
    # para reducir el tiempo de entrenamiento
    simplified_param_grid = {
        'n_estimators': [50],
        'max_depth': [10],
    }
    
    grid_search = GridSearchCV(
        estimator=model,
        param_grid=simplified_param_grid,
        cv=3,
        n_jobs=-1,
        scoring='f1'
    )
    
    grid_search.fit(X_train, y_train)
    
    # Obtener el mejor modelo
    best_model = grid_search.best_estimator_
    
    # Evaluar el modelo
    y_pred = best_model.predict(X_test)
    
    print("Resultados de evaluación:")
    print(f"Accuracy: {accuracy_score(y_test, y_pred):.4f}")
    print(f"Precision: {precision_score(y_test, y_pred):.4f}")
    print(f"Recall: {recall_score(y_test, y_pred):.4f}")
    print(f"F1 Score: {f1_score(y_test, y_pred):.4f}")
    print("\nInforme de clasificación:")
    print(classification_report(y_test, y_pred))
    
    # Guardar el modelo
    model_dir = "app/ml/models"
    os.makedirs(model_dir, exist_ok=True)
    
    model_path = os.path.join(model_dir, "trained_model.pkl")
    with open(model_path, 'wb') as f:
        pickle.dump(best_model, f)
    
    print(f"Modelo guardado en {model_path}")
    
    # Guardar también información sobre las características
    feature_importance = pd.DataFrame({
        'feature': X.columns,
        'importance': best_model.feature_importances_
    })
    feature_importance = feature_importance.sort_values('importance', ascending=False)
    
    print("\nImportancia de características:")
    print(feature_importance)
    
    return best_model

if __name__ == "__main__":
    train_model()