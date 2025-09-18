# Arquitectura Cloud Híbrida para Aplicación de Banca Móvil

## Descripción General

Este proyecto simula el diseño de una arquitectura cloud híbrida para una aplicación de banca móvil, utilizando funciones serverless para garantizar escalabilidad, seguridad y eficiencia de costos.

## Arquitectura Propuesta

### Filosofía del Diseño

La arquitectura híbrida combina:
- **Nube Pública (AWS)**: Para servicios de cara al cliente, APIs y lógica de negocio
- **Nube Privada (On-Premises)**: Para el core bancario y datos críticos sensibles
- **Funciones Serverless**: Para escalabilidad automática y pago por uso

### Diagrama Arquitectónico

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              CLIENTE                                        │
│  ┌─────────────────┐                                                        │
│  │   App Móvil     │                                                        │
│  │   (iOS/Android) │                                                        │
│  └─────────────────┘                                                        │
└─────────────────────────────────────────────────────────────────────────────┘
                              │ HTTPS
                              ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                          NUBE PÚBLICA (AWS)                                │
│                                                                             │
│  ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐        │
│  │   API Gateway   │    │   Cognito       │    │   CloudWatch    │        │
│  │   (REST API)    │    │ (Autenticación) │    │   (Monitoreo)   │        │
│  └─────────────────┘    └─────────────────┘    └─────────────────┘        │
│           │                       │                       │                │
│           ▼                       │                       │                │
│  ┌─────────────────────────────────────────────────────────────────┐      │
│  │                  FUNCIONES LAMBDA                              │      │
│  │                                                                 │      │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐        │      │
│  │  │ getBalance   │  │transferFunds │  │getTransactions│        │      │
│  │  └──────────────┘  └──────────────┘  └──────────────┘        │      │
│  │                                                                 │      │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐        │      │
│  │  │updateProfile │  │ validateCard │  │sendNotification│       │      │
│  │  └──────────────┘  └──────────────┘  └──────────────┘        │      │
│  └─────────────────────────────────────────────────────────────────┘      │
│           │                                                                │
│           │                                                                │
│  ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐        │
│  │   DynamoDB      │    │      SNS        │    │      SQS        │        │
│  │ (Cache/Perfiles)│    │(Notificaciones) │    │   (Mensajes)    │        │
│  └─────────────────┘    └─────────────────┘    └─────────────────┘        │
└─────────────────────────────────────────────────────────────────────────────┘
                              │ VPN/Direct Connect
                              ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                    CENTRO DE DATOS ON-PREMISES                             │
│                                                                             │
│  ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐        │
│  │ Security Gateway│    │  Core Bancario  │    │   PostgreSQL    │        │
│  │   (Firewall)    │    │   (Mainframe)   │    │ (Base de Datos) │        │
│  └─────────────────┘    └─────────────────┘    └─────────────────┘        │
│                                                                             │
│  ┌─────────────────┐    ┌─────────────────┐                               │
│  │ Active Directory│    │ Backup Systems  │                               │
│  │ (Autenticación) │    │   (Respaldo)    │                               │
│  └─────────────────┘    └─────────────────┘                               │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Flujo de Operaciones

### 1. Consulta de Saldo
1. Usuario solicita saldo en la app móvil
2. App envía petición HTTPS a API Gateway
3. API Gateway valida token con Cognito
4. Invoca función Lambda `getBalance`
5. Lambda se conecta de forma segura al core bancario on-premises
6. Core bancario consulta base de datos y retorna saldo
7. Respuesta se envía de vuelta a la app móvil

### 2. Transferencia de Fondos
1. Usuario inicia transferencia en la app
2. Validación de autenticación y autorización
3. Función Lambda `transferFunds` procesa la solicitud
4. Validación de fondos con el core bancario
5. Ejecución de la transacción
6. Notificación al usuario vía SNS

## Ventajas de la Arquitectura

- **Seguridad**: Datos críticos permanecen on-premises
- **Escalabilidad**: Funciones serverless escalan automáticamente
- **Costo-Eficiencia**: Pago por uso real
- **Disponibilidad**: Redundancia y failover automático
- **Cumplimiento**: Facilita el cumplimiento de regulaciones bancarias
- **Flexibilidad**: Permite integración gradual de nuevos servicios

## Tecnologías Utilizadas

- **AWS Lambda**: Funciones serverless
- **API Gateway**: Gestión de APIs REST
- **Amazon Cognito**: Autenticación y autorización
- **DynamoDB**: Base de datos NoSQL para cache
- **SNS/SQS**: Mensajería y notificaciones
- **VPN/Direct Connect**: Conectividad híbrida segura
- **PostgreSQL**: Base de datos transaccional on-premises

## Seguridad

- Cifrado end-to-end
- Tokens JWT para autenticación
- VPN/Direct Connect para comunicación híbrida
- WAF (Web Application Firewall) en API Gateway
- Monitoreo continuo con CloudWatch
- Auditoría completa de transacciones

## Estructura del Proyecto

```
banca-movil-backend/
├── src/
│   ├── handlers/          # Funciones Lambda
│   ├── utils/             # Utilidades compartidas
│   ├── models/            # Modelos de datos
│   └── services/          # Servicios de negocio
├── config/                # Configuraciones
├── template.yaml          # SAM Template
└── README.md             # Este archivo
```
