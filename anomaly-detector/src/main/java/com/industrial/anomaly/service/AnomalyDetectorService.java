package main.java.com.industrial.anomaly.service;

import com.industrial.anomaly.model.SensorMeasurement;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.datatype.jsr310.JavaTimeModule; // <--- Import Novo
import lombok.extern.slf4j.Slf4j;
import org.springframework.kafka.annotation.KafkaListener;
import org.springframework.stereotype.Service;

@Service
@Slf4j
public class AnomalyDetectorService {

    // CORREÇÃO AQUI: Registramos o JavaTimeModule para ele entender o 'Instant'
    private final ObjectMapper objectMapper = new ObjectMapper()
            .registerModule(new JavaTimeModule());
            
    private static final double VIBRATION_THRESHOLD = 5.0; 

    @KafkaListener(topics = "industrial-sensors-v1", groupId = "anomaly-detector-group")
    public void consume(String message) {
        try {
            SensorMeasurement data = objectMapper.readValue(message, SensorMeasurement.class);

            if (data.vibration() > VIBRATION_THRESHOLD) {
                log.error("🚨 ALERTA CRÍTICO: Máquina {} vibrando muito! Valor: {}", 
                    data.machineId(), data.vibration());
            } else {
                log.info("✅ Dados normais: Temp={} Vib={}", data.temperature(), data.vibration());
            }

        } catch (Exception e) {
            log.error("Erro ao processar mensagem", e);
        }
    }

    private boolean detectAnomaly(SensorMeasurement data) {
        return data.vibration() > VIBRATION_THRESHOLD;
    }
}