import os
import pickle
import numpy as np
from sklearn.ensemble import RandomForestClassifier
import pandas as pd

def create_initial_model():
    """Crea un modelo inicial básico para demostraciones si no existe uno entrenado."""
    
    model_path = os.path.join(os.path.dirname(__file__), "models", "trained_model.pkl")
    
    # Verificar si ya existe un modelo
    if os.path.exists(model_path):
        print("Modelo ya existente, no se creará uno nuevo.")
        return

    print("Creando modelo inicial básico...")
    
    # Crear directorios si no existen
    os.makedirs(os.path.dirname(model_path), exist_ok=True)
    
    # Características simuladas para un modelo muy básico
    X = pd.DataFrame({
        'experience_years': [1, 5, 10, 2, 3, 7, 8, 2, 1, 4],
        'hourly_rate': [20, 50, 80, 30, 40, 60, 70, 30, 25, 45],
        'rating': [3, 4.5, 5, 3.5, 4, 4.8, 4.2, 3.7, 3.2, 4.1],
        'skill_match_count': [1, 3, 4, 2, 3, 4, 3, 2, 1, 2],
        'skill_match_pct': [0.2, 0.8, 1.0, 0.5, 0.7, 0.9, 0.7, 0.5, 0.3, 0.6],
        'area_match': [0, 1, 1, 0, 1, 1, 0, 1, 0, 1],
        'budget': [500, 1000, 2000, 800, 1200, 1800, 1500, 900, 600, 1100]
    })
    
    # Etiquetas simuladas (0 = no match, 1 = match)
    y = np.array([0, 1, 1, 0, 1, 1, 0, 0, 0, 1])
    
    # Entrenar un modelo simple
    model = RandomForestClassifier(n_estimators=10, random_state=42)
    model.fit(X, y)
    
    # Guardar el modelo
    with open(model_path, 'wb') as f:
        pickle.dump(model, f)
    
    print(f"Modelo inicial guardado en {model_path}")

if __name__ == "__main__":
    create_initial_model()