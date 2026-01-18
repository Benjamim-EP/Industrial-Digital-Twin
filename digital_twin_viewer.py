import rerun as rr
import json
from kafka import KafkaConsumer
import math
import random
import os
import time
import numpy as np
from scipy.spatial.transform import Rotation as R

# --- IMPORTAÇÃO DOS ARQUÉTIPOS ---
# Tentamos importar os nomes corretos.
# O Rerun sugere "Scalars" (plural) na sua versão.
try:
    from rerun.archetypes import Asset3D, Transform3D, TextDocument, Scalars
    SCALAR_CLASS = Scalars
except ImportError:
    try:
        # Tenta singular se o plural falhar
        from rerun.archetypes import Asset3D, Transform3D, TextDocument, Scalar
        SCALAR_CLASS = Scalar
    except ImportError:
        # Fallback genérico
        print("⚠️ Aviso: Não foi possível importar Scalar/Scalars. Gráficos podem falhar.")
        SCALAR_CLASS = None
        from rerun.archetypes import Asset3D, Transform3D, TextDocument

# --- CONFIGURAÇÃO DE ARQUIVOS ---
ASSETS_DIR = "3dassets" 
FILES = {
    "base": "asset_base_fixa.glb",
    "torre": "asset_torre.glb",
    "arm1": "asset_braco1.glb",
    "arm2": "asset_braco2.glb",
    "arm3": "asset_braco3.glb"
}

# --- CONFIGURAÇÃO DE MONTAGEM ---
OFFSET_TORRE = [0, 0, 0]      
OFFSET_ARM1  = [0, 0, 0.2]  # Um leve ajuste pra cima
OFFSET_ARM2  = [0, 0.2, 0]  # Um leve ajuste pra frente/cima
OFFSET_ARM3  = [0, 0.2, 0]  # Um leve ajuste pra frente/cima 

def run_simulation():
    print(f"ℹ️ Versão do Rerun: {rr.__version__}")
    rr.init("Industrial Digital Twin", spawn=True)

    if not os.path.exists(ASSETS_DIR):
        print(f"❌ ERRO CRÍTICO: A pasta '{ASSETS_DIR}' não foi encontrada!")
        return

    # 1. CARREGAMENTO DOS MODELOS 3D
    print("⏳ Carregando modelos 3D...")
    
    def get_path(key):
        return os.path.join(ASSETS_DIR, FILES[key])

    # Rotação para levantar o robô
    q_fix_base = R.from_euler('x', 90, degrees=True).as_quat()
    rr.log("twin/robot", Transform3D(rotation=rr.Quaternion(xyzw=q_fix_base)))
    
    rr.log("twin/robot", Asset3D(path=get_path("base")))
    rr.log("twin/robot/torre", Asset3D(path=get_path("torre")))
    rr.log("twin/robot/torre/arm1", Asset3D(path=get_path("arm1")))
    rr.log("twin/robot/torre/arm1/arm2", Asset3D(path=get_path("arm2")))
    rr.log("twin/robot/torre/arm1/arm2/arm3", Asset3D(path=get_path("arm3")))

    # 2. CONEXÃO KAFKA
    try:
        consumer = KafkaConsumer(
            'industrial-sensors-v1',
            bootstrap_servers=['localhost:9092'],
            auto_offset_reset='latest',
            value_deserializer=lambda x: json.loads(x.decode('utf-8'))
        )
        print("🚀 Visualizador Iniciado! Aguardando dados...")
    except Exception as e:
        print(f"❌ Erro ao conectar no Kafka: {e}")
        return

    # Variáveis de Estado
    cycle_time = 0.0
    accumulated_rotation_z = 0.0

    print("🎥 Loop de renderização ativo...")
    
    for message in consumer:
        data = message.value
        
        sensor_id = data.get('sensorId', 'Unknown')
        temp = data.get('temperature', 0.0)
        vib = data.get('vibration', 0.0)
        rpm = data.get('rotationSpeed', 0.0)

        # Lógica de Movimento
        # 1. Deixa bem lento para visualizarmos
        velocidade_angular = rpm / 3000.0 
        accumulated_rotation_z += velocidade_angular
        
        # 2. Ciclo de trabalho mais lento
        cycle_time += 0.01 + (velocidade_angular * 0.05)
        
        # 3. Movimentos curtos (apenas 10 a 20 graus) para não "quebrar" o braço visualmente
        angle_arm1 = Math_map_sin(cycle_time, -10, 20) 
        angle_arm2 = Math_map_cos(cycle_time, -10, 20)

        # Anomalia
        is_anomaly = vib > 5.0
        status_msg = "OK"
        pos_garra_x = OFFSET_ARM3[0]
        pos_garra_y = OFFSET_ARM3[1]
        
        if is_anomaly:
            jitter = (vib / 10.0) * 0.1
            pos_garra_x += random.uniform(-jitter, jitter)
            pos_garra_y += random.uniform(-jitter, jitter)
            status_msg = "CRITICAL VIBRATION"

        # 3. ATUALIZAÇÃO 3D
        q_torre = R.from_euler('z', accumulated_rotation_z, degrees=False).as_quat()
        q_arm1 = R.from_euler('x', angle_arm1, degrees=True).as_quat()
        q_arm2 = R.from_euler('x', angle_arm2, degrees=True).as_quat()

        rr.log("twin/robot/torre", Transform3D(translation=OFFSET_TORRE, rotation=rr.Quaternion(xyzw=q_torre)))
        rr.log("twin/robot/torre/arm1", Transform3D(translation=OFFSET_ARM1, rotation=rr.Quaternion(xyzw=q_arm1)))
        rr.log("twin/robot/torre/arm1/arm2", Transform3D(translation=OFFSET_ARM2, rotation=rr.Quaternion(xyzw=q_arm2)))
        rr.log("twin/robot/torre/arm1/arm2/arm3", Transform3D(translation=[pos_garra_x, pos_garra_y, OFFSET_ARM3[2]]))

        # 4. GRÁFICOS (Correção Principal)
        if SCALAR_CLASS:
            # Importante: Scalars espera uma lista, ex: Scalars([temp])
            rr.log("telemetry/temperature", SCALAR_CLASS([temp]))
            rr.log("telemetry/vibration", SCALAR_CLASS([vib]))
            rr.log("telemetry/rpm", SCALAR_CLASS([rpm]))
        
        # 5. LOGS
        try:
            rr.log("logs/system", TextDocument(f"Sensor: {sensor_id}\nStatus: {status_msg}"))
        except:
            pass

def Math_map_sin(t, min_val, max_val):
    val = math.sin(t)
    return min_val + (max_val - min_val) * ((val + 1) / 2)

def Math_map_cos(t, min_val, max_val):
    val = math.cos(t)
    return min_val + (max_val - min_val) * ((val + 1) / 2)

if __name__ == "__main__":
    run_simulation()