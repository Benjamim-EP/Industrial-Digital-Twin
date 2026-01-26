import rerun as rr
import json
from kafka import KafkaConsumer
import math
import random
import os
import time
import numpy as np
from scipy.spatial.transform import Rotation as R

# --- CONFIGURAÇÃO DE IMPORTS RERUN 0.28+ ---
# Usando a classe Scalars (plural) conforme o erro anterior indicou
from rerun.archetypes import Asset3D, Transform3D, TextDocument, Scalars

# --- CONFIGURAÇÃO ---
ASSETS_DIR = "3dassets" 
FILES = {
    "base": "asset_base_fixa.glb",
    "torre": "asset_torre.glb",
    "arm1": "asset_braco1.glb",
    "arm2": "asset_braco2.glb",
    "arm3": "asset_braco3.glb"
}

def run_simulation():
    print(f"ℹ️ Versão do Rerun: {rr.__version__}")
    rr.init("Industrial Digital Twin", spawn=True)

    if not os.path.exists(ASSETS_DIR):
        print(f"❌ ERRO: Pasta '{ASSETS_DIR}' não encontrada!")
        return

    def get_path(key): return os.path.join(ASSETS_DIR, FILES[key])

    # ---------------------------------------------------------
    # 1. SETUP ESTÁTICO (MONTAGEM IGUAL AO SEU DEBUG)
    # ---------------------------------------------------------
    print("⏳ Carregando modelos e aplicando rotação de base...")
    
    # Rotação X=90 que você validou para levantar o robô
    q_fix_base = R.from_euler('x', 90, degrees=True).as_quat()
    rr.log("twin/robot", Transform3D(rotation=rr.Quaternion(xyzw=q_fix_base)))
    
    # Carregando as peças (Todas em POS [0,0,0] conforme seu sucesso no debug)
    rr.log("twin/robot", Asset3D(path=get_path("base")))
    rr.log("twin/robot/torre", Asset3D(path=get_path("torre")))
    rr.log("twin/robot/torre/arm1", Asset3D(path=get_path("arm1")))
    rr.log("twin/robot/torre/arm1/arm2", Asset3D(path=get_path("arm2")))
    rr.log("twin/robot/torre/arm1/arm2/arm3", Asset3D(path=get_path("arm3")))

    # ---------------------------------------------------------
    # 2. CONEXÃO KAFKA
    # ---------------------------------------------------------
    try:
        consumer = KafkaConsumer(
            'industrial-sensors-v1',
            bootstrap_servers=['localhost:9092'],
            auto_offset_reset='latest',
            value_deserializer=lambda x: json.loads(x.decode('utf-8'))
        )
        print("🚀 Visualizador Iniciado! Aguardando dados do Kafka...")
    except Exception as e:
        print(f"❌ Erro Kafka: {e}")
        return

    # Variáveis para controle de animação
    accumulated_rotation_z = 0.0
    cycle_time = 0.0

    print("🎥 Renderizando animação baseada em sensores...")
    
    for message in consumer:
        data = message.value
        
        # Extração de dados
        sensor_id = data.get('sensorId', 'Unknown')
        temp = data.get('temperature', 0.0)
        vib = data.get('vibration', 0.0)
        rpm = data.get('rotationSpeed', 0.0)

        # --- LÓGICA DE MOVIMENTO ---
        # A torre gira baseado no RPM
        velocidade_angular = rpm / 2000.0 # Ajuste de velocidade
        accumulated_rotation_z += velocidade_angular
        
        # O braço oscila suavemente (cycle_time)
        cycle_time += 0.02
        angle_arm1 = math.sin(cycle_time) * 15 # Oscila 15 graus
        angle_arm2 = math.cos(cycle_time) * 15 # Oscila 15 graus

        # --- ANOMALIA (TREMOR) ---
        is_anomaly = vib > 5.0
        status_msg = "OK"
        jitter = [0.0, 0.0, 0.0]
        
        if is_anomaly:
            status_msg = "CRITICAL VIBRATION"
            # Pequeno deslocamento aleatório na garra (arm3)
            j_amt = (vib / 10.0) * 0.02 
            jitter = [random.uniform(-j_amt, j_amt) for _ in range(3)]

        # ---------------------------------------------------------
        # 3. LOG DE TRANSFORMAÇÕES (MOVIMENTO)
        # ---------------------------------------------------------
        
        # Torre gira no eixo Z LOCAL (que agora é o eixo de rotação após o X=90 global)
        q_torre = R.from_euler('y', accumulated_rotation_z/100, degrees=False).as_quat()
        rr.log("twin/robot/torre", Transform3D(rotation=rr.Quaternion(xyzw=q_torre)))

        # Braços giram no eixo X LOCAL (dobradiça)
        q_arm1 = R.from_euler('x', angle_arm1, degrees=True).as_quat()
        rr.log("twin/robot/torre/arm1", Transform3D(rotation=rr.Quaternion(xyzw=q_arm1)))

        q_arm2 = R.from_euler('x', angle_arm2, degrees=True).as_quat()
        rr.log("twin/robot/torre/arm1/arm2", Transform3D(rotation=rr.Quaternion(xyzw=q_arm2)))

        # A garra apenas treme se houver anomalia (translation)
        # Como as peças estão montadas no 0,0,0, aplicamos apenas o jitter
        rr.log("twin/robot/torre/arm1/arm2/arm3", Transform3D(translation=jitter))

        # ---------------------------------------------------------
        # 4. TELEMETRIA E LOGS
        # ---------------------------------------------------------
        # Usando Scalars([valor]) conforme exigido pela sua versão 0.28.2
        rr.log("telemetry/temperature", Scalars([temp]))
        rr.log("telemetry/vibration", Scalars([vib]))
        rr.log("telemetry/rpm", Scalars([rpm]))
        
        rr.log("logs/status", TextDocument(f"Sensor: {sensor_id}\nTemp: {temp:.2f}°C\nStatus: {status_msg}"))

if __name__ == "__main__":
    run_simulation()