package com.industrial.sensor.service;

import com.industrial.sensor.domain.SensorMeasurement;
import jakarta.enterprise.context.ApplicationScoped;
import org.eclipse.microprofile.reactive.messaging.Outgoing;

import java.time.Instant;
import java.util.Random;

@ApplicationScoped
public class SensorSimulationService {

    private final Random random = new Random();
    private double timeStep = 0; // Controla o eixo X do tempo para as ondas senoidais

    // A anotação @Outgoing conecta este método ao canal do Kafka definido no properties
    // O Quarkus vai chamar isso automaticamente a cada tick do scheduler
    @Outgoing("sensor-data-out")
    public SensorMeasurement generateTelemetry() {
        timeStep += 0.1;

        // 1. Simulação de Temperatura: Tende a estabilizar em 60 graus com oscilação
        double baseTemp = 60.0 + (5.0 * Math.sin(timeStep * 0.05));
        double temperature = baseTemp + (random.nextGaussian() * 0.5);

        // 2. Simulação de Vibração: Padrão de onda (motor girando)
        // Usamos Math.abs porque vibração é magnitude (sempre positiva)
        double vibration = Math.abs(2.0 * Math.sin(timeStep)) + (random.nextDouble() * 0.2);

        // 3. Rotação: Constante em 1500 RPM com leve variação
        double rotation = 1500 + (random.nextGaussian() * 10);

        // --- INJEÇÃO DE ANOMALIA (Para a IA detectar na Fase 3) ---
        // 5% de chance de gerar um pico de vibração (máquina falhando)
        if (random.nextInt(100) > 95) {
            vibration *= 5.0; // Pico de 10.0+ Hz
            System.out.println("⚠️ [ANOMALIA INJETADA] Vibração Crítica detectada: " + vibration);
        }

        return new SensorMeasurement(
            "SENSOR-X1",
            "TURBINA-01",
            temperature,
            vibration,
            rotation,
            Instant.now()
        );
    }
}