package com.industrial.sensor.domain;

import java.time.Instant;

/**
 * Representa uma leitura imutável de um sensor industrial.
 * Uso de Record (Java 14+) para reduzir boilerplate.
 */
public record SensorMeasurement(
    String sensorId,
    String machineId,
    double temperature,   // Celsius
    double vibration,     // Hz
    double rotationSpeed, // RPM
    Instant timestamp
) {}