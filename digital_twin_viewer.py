import rerun as rr
import json
from kafka import KafkaConsumer
import argparse

# --- IMPORTS ROBUSTOS (Busca Profunda) ---
try:
    # Tentativa 1: Versões Modernas (0.15 - 0.27+)
    # Importamos direto dos Arquétipos para garantir
    from rerun.archetypes import Scalar, Boxes3D, TextLog
    print("✅ Classes carregadas via rerun.archetypes")
except ImportError:
    try:
        # Tentativa 2: Versões de Transição
        from rerun.components import Scalar
        from rerun.archetypes import Boxes3D, TextLog
        print("✅ Classes carregadas via rerun.components")
    except ImportError:
        # Fallback: Vamos definir como None e tentar usar API antiga no loop
        Scalar = None
        Boxes3D = None
        TextLog = None
        print("⚠️ Classes modernas não encontradas. Tentaremos modo legado.")

# --- FIM DOS IMPORTS ---

def run_simulation():
    # 1. Inicia o Rerun
    print(f"ℹ️ Versão do Rerun: {rr.__version__}")
    rr.init("Industrial Digital Twin", spawn=True)

    # 2. Conecta no Kafka
    try:
        consumer = KafkaConsumer(
            'industrial-sensors-v1',
            bootstrap_servers=['localhost:9092'],
            auto_offset_reset='latest',
            value_deserializer=lambda x: json.loads(x.decode('utf-8'))
        )
        print("🚀 Visualizador Iniciado! Aguardando dados do Kafka...")
    except Exception as e:
        print(f"❌ Erro ao conectar no Kafka: {e}")
        return

    # 3. Loop de Processamento
    print("⏳ Aguardando mensagens...")
    for message in consumer:
        data = message.value
        
        sensor_id = data.get('sensorId', 'Unknown')
        temp = data.get('temperature', 0.0)
        vib = data.get('vibration', 0.0)
        
        # --- PLOTAGEM (Gráficos) ---
        if Scalar:
            # Modo Moderno (Archetypes)
            rr.log("telemetry/temperature", Scalar(temp))
            rr.log("telemetry/vibration", Scalar(vib))
        elif hasattr(rr, "log_scalar"):
            # Modo Legado
            rr.log_scalar("telemetry/temperature", temp)
            rr.log_scalar("telemetry/vibration", vib)

        # --- GÊMEO DIGITAL 3D ---
        is_anomaly = vib > 5.0
        color = [255, 0, 0] if is_anomaly else [0, 255, 0]
        scale_x = 1.0 + (vib / 5.0) if is_anomaly else 1.0
        label = f"{sensor_id} - {'CRITICAL' if is_anomaly else 'OK'}"

        if Boxes3D:
            # Modo Moderno
            rr.log(
                "digital_twin/machine_box",
                Boxes3D(
                    half_sizes=[scale_x, 1.0, 1.0],
                    centers=[0, 0, 0],
                    colors=color,
                    labels=label
                )
            )
        elif hasattr(rr, "log_obb"):
            # Modo Legado (Oriented Bounding Box)
            rr.log_obb(
                "digital_twin/machine_box",
                half_size=[scale_x, 1.0, 1.0],
                position=[0, 0, 0],
                color=color,
                label=label
            )

        # --- LOG DE TEXTO ---
        status_text = f"Temp: {temp:.2f} | Vib: {vib:.2f}"
        if TextLog:
            rr.log("logs/status", TextLog(status_text, level="CRITICAL" if is_anomaly else "INFO"))

if __name__ == "__main__":
    run_simulation()