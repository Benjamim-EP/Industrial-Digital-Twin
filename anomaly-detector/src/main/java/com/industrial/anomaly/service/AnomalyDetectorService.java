package com.industrial.anomaly.service;

import com.industrial.anomaly.model.SensorMeasurement;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.datatype.jsr310.JavaTimeModule;
import lombok.extern.slf4j.Slf4j;
import org.apache.camel.ProducerTemplate; // <--- Import do Camel
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.kafka.annotation.KafkaListener;
import org.springframework.stereotype.Service;

@Service
@Slf4j
public class AnomalyDetectorService {

    private final ObjectMapper objectMapper = new ObjectMapper()
            .registerModule(new JavaTimeModule());
    
    // Injetamos o "ProducerTemplate" do Camel para enviar mensagens para as rotas
    @Autowired
    private ProducerTemplate producerTemplate;

    private static final double VIBRATION_THRESHOLD = 5.0; 

    @KafkaListener(topics = "industrial-sensors-v1", groupId = "anomaly-detector-group")
    public void consume(String message) {
        try {
            SensorMeasurement data = objectMapper.readValue(message, SensorMeasurement.class);

            if (data.vibration() > VIBRATION_THRESHOLD) {
                log.warn("⚠️ ANOMALIA DETECTADA! Iniciando protocolo de integração...");
                
                // --- AQUI A MÁGICA ACONTECE ---
                // Enviamos o objeto Java direto para a rota do Camel
                producerTemplate.sendBody("direct:sendAnomalyAlert", message);
                
            } else {
                log.info("✅ Dados normais: Temp={}", String.format("%.2f", data.temperature()));
            }

        } catch (Exception e) {
            log.error("Erro ao processar mensagem", e);
        }
    }
}