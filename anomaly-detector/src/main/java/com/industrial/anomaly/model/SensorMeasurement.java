package com.industrial.anomaly.model; // Note o pacote: .model no final

import java.time.Instant;

public record SensorMeasurement(
    String sensorId,
    String machineId,
    double temperature,
    double vibration,
    double rotationSpeed,
    Instant timestamp
) {}