import pandas as pd
import numpy as np
import random
from sklearn.preprocessing import LabelEncoder

def generate_user_data(n_users=100):
    """Genera datos sintéticos de usuarios para entrenar el modelo de recomendación."""
    
    skills = [
        "Investigación cualitativa", "Investigación cuantitativa", "Análisis estadístico",
        "Diseño experimental", "Revisión de literatura", "Escritura científica",
        "Metodología de investigación", "Análisis de datos", "Desarrollo de encuestas",
        "Entrevistas estructuradas", "SPSS", "R", "Python", "Excel avanzado",
        "Investigación de mercados", "Estudios de caso", "Economía", "Finanzas",
        "Medicina", "Derecho", "Educación", "Psicología", "Sociología", "Marketing"
    ]
    
    areas = [
        "Ciencias sociales", "Economía", "Comercio exterior", 
        "Finanzas", "Jurisprudencia", "Medicina", "Educación",
        "Psicología", "Marketing", "Tecnología"
    ]
    
    users = []
    
    for i in range(n_users):
        is_freelancer = random.random() < 0.7  # 70% serán freelancers
        
        user = {
            "user_id": i + 1,
            "is_freelancer": is_freelancer,
            "is_client": not is_freelancer,
            "rating": round(random.uniform(3.0, 5.0), 1) if is_freelancer else None,
            "experience_years": round(random.uniform(0.5, 15.0), 1) if is_freelancer else None,
            "hourly_rate": round(random.uniform(10.0, 100.0), 2) if is_freelancer else None,
            "area_expertise": random.choice(areas) if is_freelancer else None,
            "skills": random.sample(skills, random.randint(3, 8)) if is_freelancer else []
        }
        users.append(user)
    
    return pd.DataFrame(users)

def generate_project_data(n_projects=200, n_users=100):
    """Genera datos sintéticos de proyectos para entrenar el modelo de recomendación."""
    
    skills = [
        "Investigación cualitativa", "Investigación cuantitativa", "Análisis estadístico",
        "Diseño experimental", "Revisión de literatura", "Escritura científica",
        "Metodología de investigación", "Análisis de datos", "Desarrollo de encuestas",
        "Entrevistas estructuradas", "SPSS", "R", "Python", "Excel avanzado",
        "Investigación de mercados", "Estudios de caso", "Economía", "Finanzas",
        "Medicina", "Derecho", "Educación", "Psicología", "Sociología", "Marketing"
    ]
    
    areas = [
        "Ciencias sociales", "Economía", "Comercio exterior", 
        "Finanzas", "Jurisprudencia", "Medicina", "Educación",
        "Psicología", "Marketing", "Tecnología"
    ]
    
    projects = []
    
    for i in range(n_projects):
        # Seleccionar un cliente aleatorio (user_id que no sea freelancer)
        client_id = random.randint(1, n_users)
        while client_id % 10 < 7:  # Asegurar que sea cliente (30% de usuarios son clientes)
            client_id = random.randint(1, n_users)
        
        # Asignar o no freelancer
        is_assigned = random.random() < 0.7  # 70% están asignados
        freelancer_id = None
        if is_assigned:
            # Seleccionar un freelancer aleatorio (user_id que sea freelancer)
            freelancer_id = random.randint(1, n_users)
            while freelancer_id % 10 >= 3:  # Asegurar que sea freelancer (70% de usuarios son freelancers)
                freelancer_id = random.randint(1, n_users)
        
        area = random.choice(areas)
        budget = round(random.uniform(100, 5000), 2)
        
        project = {
            "project_id": i + 1,
            "client_id": client_id,
            "freelancer_id": freelancer_id,
            "is_assigned": is_assigned,
            "area": area,
            "budget": budget,
            "skills_required": random.sample(skills, random.randint(2, 6))
        }
        projects.append(project)
    
    return pd.DataFrame(projects)

def generate_matching_data(users_df, projects_df):
    """Genera datos de emparejamiento para entrenar un modelo de recomendación."""
    
    # Filtrar usuarios freelancer
    freelancers = users_df[users_df["is_freelancer"]].copy()
    
    # Filtrar proyectos asignados
    assigned_projects = projects_df[projects_df["is_assigned"]].copy()
    
    # Crear datos de emparejamiento
    matches = []
    
    # Para proyectos asignados, crear ejemplos positivos
    for _, project in assigned_projects.iterrows():
        freelancer_id = project["freelancer_id"]
        project_id = project["project_id"]
        
        # Ejemplo positivo (match real)
        matches.append({
            "freelancer_id": freelancer_id,
            "project_id": project_id,
            "match": 1
        })
        
        # Ejemplos negativos (freelancers que no fueron seleccionados)
        for _ in range(3):  # 3 ejemplos negativos por cada positivo
            random_freelancer = freelancers.sample(1).iloc[0]
            if random_freelancer["user_id"] != freelancer_id:
                matches.append({
                    "freelancer_id": random_freelancer["user_id"],
                    "project_id": project_id,
                    "match": 0
                })
    
    matches_df = pd.DataFrame(matches)
    
    # Combinar con características de freelancer y proyecto
    result = matches_df.merge(
        freelancers.rename(columns={"user_id": "freelancer_id"}),
        on="freelancer_id",
        how="left"
    )
    
    result = result.merge(
        projects_df.rename(columns={"project_id": "project_id"}),
        on="project_id",
        how="left"
    )
    
    return result

def prepare_features(data):
    """Prepara características para el entrenamiento del modelo."""
    
    # Crear características basadas en habilidades
    # Contar cuántas habilidades coinciden entre el freelancer y el proyecto
    data['skill_match_count'] = data.apply(
        lambda row: len(set(row['skills']).intersection(set(row['skills_required']))) 
            if isinstance(row['skills'], list) and isinstance(row['skills_required'], list) 
            else 0, 
        axis=1
    )
    
    # Porcentaje de habilidades requeridas que posee el freelancer
    data['skill_match_pct'] = data.apply(
        lambda row: len(set(row['skills']).intersection(set(row['skills_required']))) / len(set(row['skills_required']))
            if isinstance(row['skills_required'], list) and len(row['skills_required']) > 0
            else 0,
        axis=1
    )
    
    # Coincidencia de área de expertise
    data['area_match'] = (data['area_expertise'] == data['area']).astype(int)
    
    # Características clave para el modelo
    X = data[['experience_years', 'hourly_rate', 'rating', 'skill_match_count', 'skill_match_pct', 'area_match', 'budget']]
    y = data['match']
    
    # Manejar valores nulos
    X = X.fillna(0)
    
    return X, y

def generate_training_data(save_to_csv=True):
    """Genera un conjunto completo de datos de entrenamiento."""
    
    # Generar datos de usuarios y proyectos
    print("Generando datos de usuarios...")
    users_df = generate_user_data(n_users=100)
    
    print("Generando datos de proyectos...")
    projects_df = generate_project_data(n_projects=200, n_users=100)
    
    print("Generando datos de emparejamiento...")
    matching_data = generate_matching_data(users_df, projects_df)
    
    print("Preparando características...")
    X, y = prepare_features(matching_data)
    
    if save_to_csv:
        print("Guardando datos...")
        users_df.to_csv("app/ml/training/data/users.csv", index=False)
        projects_df.to_csv("app/ml/training/data/projects.csv", index=False)
        matching_data.to_csv("app/ml/training/data/matching.csv", index=False)
        
        # Guardar datos de entrenamiento
        training_data = pd.concat([X, y], axis=1)
        training_data.to_csv("app/ml/training/data/training_data.csv", index=False)
    
    return X, y, users_df, projects_df, matching_data

if __name__ == "__main__":
    # Crear directorio de datos si no existe
    import os
    os.makedirs("app/ml/training/data", exist_ok=True)
    
    # Generar datos
    X, y, users_df, projects_df, matching_data = generate_training_data()
    
    print(f"Generados {len(users_df)} usuarios")
    print(f"Generados {len(projects_df)} proyectos")
    print(f"Generados {len(matching_data)} ejemplos de emparejamiento")