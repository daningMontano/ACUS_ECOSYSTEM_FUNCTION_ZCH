import os
import ee
from dotenv import load_dotenv, find_dotenv

def initialize_gee():
    """
    Carga las variables de entorno desde el archivo .env e inicializa 
    la conexión con Google Earth Engine.
    """
    # Buscar y cargar el archivo .env
    env_path = find_dotenv()
    if env_path:
        load_dotenv(env_path)
    
    project_id = os.getenv('GEE_PROJECT_ID')
    
    if not project_id:
        print("❌ Error: GEE_PROJECT_ID no encontrado en el archivo .env")
        return

    try:
        # Inicializar GEE
        ee.Initialize(project=project_id)
        print(f"✅ Google Earth Engine inicializado exitosamente.")
        print(f"   Proyecto: {project_id}")
    except Exception as e:
        print(f"❌ Falló la inicialización de GEE: {e}")
        print("   Asegúrate de tener instalada 'earthengine-api' y haber ejecutado 'ee.Authenticate()'.")

if __name__ == "__main__":
    initialize_gee()
