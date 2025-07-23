#backend\app\ml\recomender.py
import os
import pickle
import numpy as np
import pandas as pd
from typing import List, Dict, Any

class FreelancerRecommender:
    """
    Sistema de recomendación para emparejar freelancers con proyectos
    basado en modelos de Machine Learning.
    """
    
    def __init__(self):
        # Cargar el modelo entrenado
        model_path = os.path.join(os.path.dirname(__file__), "models", "trained_model.pkl")
        
        # Si el modelo no existe, mostrar mensaje informativo
        if not os.path.exists(model_path):
            print("AVISO: Modelo no encontrado. Ejecute primero train_model.py para entrenar el modelo.")
            self.model = None
        else:
            with open(model_path, 'rb') as f:
                self.model = pickle.load(f)
    
    def prepare_features(self, freelancer: Dict[str, Any], project: Dict[str, Any]) -> pd.DataFrame:
        """Prepara las características para la predicción del modelo."""
        
        # Calcular coincidencia de habilidades
        freelancer_skills = set(freelancer.get('skills', []))
        project_skills = set(project.get('skills_required', []))
        
        # Número de habilidades coincidentes
        skill_match_count = len(freelancer_skills.intersection(project_skills))
        
        # Porcentaje de habilidades requeridas que posee el freelancer
        skill_match_pct = skill_match_count / len(project_skills) if project_skills else 0
        
        # Coincidencia de área
        area_match = 1 if freelancer.get('area_expertise') == project.get('area') else 0
        
        # Crear DataFrame con las características
        features = pd.DataFrame({
            'experience_years': [freelancer.get('experience_years', 0)],
            'hourly_rate': [freelancer.get('hourly_rate', 0)],
            'rating': [freelancer.get('rating', 0)],
            'skill_match_count': [skill_match_count],
            'skill_match_pct': [skill_match_pct],
            'area_match': [area_match],
            'budget': [project.get('budget', 0)]
        })
        
        return features
    
    def predict_match(self, freelancer: Dict[str, Any], project: Dict[str, Any]) -> float:
        """Predice la probabilidad de coincidencia entre un freelancer y un proyecto."""
        
        if self.model is None:
            raise ValueError("El modelo no ha sido cargado. Entrene el modelo primero.")
        
        # Preparar características
        features = self.prepare_features(freelancer, project)
        
        # Predecir probabilidad
        probabilities = self.model.predict_proba(features)
        
        # Retornar probabilidad de match (clase 1)
        return float(probabilities[0][1])
    
    def recommend_freelancers(self, project: Dict[str, Any], freelancers: List[Dict[str, Any]], top_n: int = 5) -> List[Dict[str, Any]]:
        """Recomienda los mejores freelancers para un proyecto dado."""
        
        if self.model is None:
            raise ValueError("El modelo no ha sido cargado. Entrene el modelo primero.")
        
        results = []
        
        for freelancer in freelancers:
            # Calcular probabilidad de match
            match_probability = self.predict_match(freelancer, project)
            
            # Añadir a resultados
            results.append({
                'freelancer': freelancer,
                'match_probability': match_probability
            })
        
        # Ordenar por probabilidad de match (descendente)
        results.sort(key=lambda x: x['match_probability'], reverse=True)
        
        # Devolver los top_n resultados
        return results[:top_n]
    
    def recommend_projects(self, freelancer: Dict[str, Any], projects: List[Dict[str, Any]], top_n: int = 5) -> List[Dict[str, Any]]:
        """Recomienda los mejores proyectos para un freelancer dado."""
        
        if self.model is None:
            raise ValueError("El modelo no ha sido cargado. Entrene el modelo primero.")
        
        results = []
        
        for project in projects:
            # Calcular probabilidad de match
            match_probability = self.predict_match(freelancer, project)
            
            # Añadir a resultados
            results.append({
                'project': project,
                'match_probability': match_probability
            })
        
        # Ordenar por probabilidad de match (descendente)
        results.sort(key=lambda x: x['match_probability'], reverse=True)
        
        # Devolver los top_n resultados
        return results[:top_n]