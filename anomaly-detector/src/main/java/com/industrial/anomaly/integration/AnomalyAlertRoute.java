package com.industrial.anomaly.integration;

import org.apache.camel.builder.RouteBuilder;
import org.springframework.stereotype.Component;

@Component
public class AnomalyAlertRoute extends RouteBuilder {

    @Override
    public void configure() throws Exception {
        
        // Configuração Global do Circuit Breaker
        // Se 50% das requisições falharem, ele abre o circuito e para de tentar por 5 segundos
        // "Entrevista Tip": Isso impede o "Cascading Failure" (Efeito Dominó)
        
        from("direct:sendAnomalyAlert")
            .routeId("rota-alerta-manutencao")
            .log("⚡ Tentando notificar sistema de Manutenção...")
            
            .circuitBreaker()
                // Configuração da Resiliência
                .resilience4jConfiguration()
                    .timeoutEnabled(true)
                    .timeoutDuration(1000) // Se demorar +1s, cancela
                    .failureRateThreshold(50) // Se 50% der erro, abre o circuito
                    .waitDurationInOpenState(5000) // Fica 5s sem tentar se abrir
                .end()
                
                // Tenta chamar um sistema externo (que não existe de propósito para falhar)
                .to("http://localhost:9999/api/maintenance-system?bridgeEndpoint=true")
                .log("✅ Sucesso! Manutenção avisada.")
                
            .onFallback()
                // PLANO B: Se o sistema externo falhar ou circuito estiver aberto
                .log("🔥 FALHA NA INTEGRAÇÃO! Ativando Fallback (Resilience4J).")
                .log("💾 Salvando alerta em arquivo de backup de emergência...")
                // Aqui poderíamos salvar no Redis, mas vamos simular salvando num arquivo log
                .to("file:backup-alerts?fileName=anomalies-${date:now:yyyyMMdd-HHmmss}.json")
            .end();
    }
}