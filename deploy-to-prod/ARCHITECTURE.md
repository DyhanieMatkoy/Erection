# Deployment Architecture

## System Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                    Construction Time Management                  │
│                         Production System                        │
└─────────────────────────────────────────────────────────────────┘

┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│  Web Client  │     │   Desktop    │     │  API Server  │
│    (SPA)     │────▶│     App      │────▶│   (FastAPI)  │
│   Vue.js     │     │   PyQt6      │     │   Backend    │
└──────────────┘     └──────────────┘     └──────────────┘
       │                    │                     │
       │                    │                     │
       └────────────────────┴─────────────────────┘
                            │
                            ▼
                   ┌─────────────────┐
                   │    Database     │
                   │  PostgreSQL/    │
                   │     MSSQL       │
                   └─────────────────┘
```

## Deployment Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                      Deployment Process                          │
└─────────────────────────────────────────────────────────────────┘

Step 1: Database Migration
┌──────────────┐         ┌──────────────┐
│   SQLite     │────────▶│ PostgreSQL/  │
│ construction │ Migrate │    MSSQL     │
│     .db      │         │ construction │
└──────────────┘         └──────────────┘
                                │
                                ▼
Step 2: Build Web Client
┌──────────────┐         ┌──────────────┐
│ web-client/  │  Build  │   output/    │
│    src/      │────────▶│ web-client/  │
│  Vue.js      │  (npm)  │   dist/      │
└──────────────┘         └──────────────┘
                                │
                                ▼
Step 3: Build Desktop App
┌──────────────┐         ┌──────────────┐
│   main.py    │  Build  │   output/    │
│   src/       │────────▶│  desktop/    │
│  PyQt6 App   │(PyInst) │    .exe      │
└──────────────┘         └──────────────┘
                                │
                                ▼
Step 4: Build API Server
┌──────────────┐         ┌──────────────┐
│   api/       │  Build  │   output/    │
│  FastAPI     │────────▶│ api-server/  │
│  Backend     │(PyInst) │    .exe      │
└──────────────┘         └──────────────┘
                                │
                                ▼
Step 5: Configure
┌──────────────┐         ┌──────────────┐
│deploy_config │Generate │  env.ini     │
│    .ini      │────────▶│  .env        │
│              │         │ config.json  │
└──────────────┘         └──────────────┘
```

## Component Architecture

### Web Client (SPA)

```
┌─────────────────────────────────────────┐
│          Web Client (Browser)           │
├─────────────────────────────────────────┤
│  Vue.js 3 + TypeScript                  │
│  ├─ Components                          │
│  ├─ Stores (Pinia)                      │
│  ├─ Router                              │
│  └─ API Client                          │
├─────────────────────────────────────────┤
│  Build Output (Vite)                    │
│  ├─ index.html                          │
│  ├─ assets/                             │
│  │   ├─ index-[hash].js (minified)     │
│  │   └─ index-[hash].css (minified)    │
│  └─ config.json                         │
└─────────────────────────────────────────┘
         │
         │ HTTP/HTTPS
         ▼
┌─────────────────────────────────────────┐
│         Web Server (nginx/Apache)       │
│  ├─ Serve static files                  │
│  ├─ SPA routing                         │
│  └─ Proxy /api → API Server             │
└─────────────────────────────────────────┘
```

### Desktop Application

```
┌─────────────────────────────────────────┐
│      Desktop Application (.exe)         │
├─────────────────────────────────────────┤
│  PyQt6 GUI                              │
│  ├─ Login Form                          │
│  ├─ Main Window                         │
│  ├─ Document Forms                      │
│  └─ Reports                             │
├─────────────────────────────────────────┤
│  Business Logic                         │
│  ├─ Services                            │
│  ├─ Repositories                        │
│  └─ Models                              │
├─────────────────────────────────────────┤
│  Database Layer                         │
│  ├─ SQLAlchemy ORM                      │
│  ├─ Connection Manager                  │
│  └─ Schema Manager                      │
├─────────────────────────────────────────┤
│  Bundled Components                     │
│  ├─ Python Interpreter                  │
│  ├─ Dependencies                        │
│  ├─ PrnForms/                           │
│  ├─ fonts/                              │
│  └─ env.ini                             │
└─────────────────────────────────────────┘
         │
         │ Database Connection
         ▼
┌─────────────────────────────────────────┐
│         Database Server                 │
└─────────────────────────────────────────┘
```

### API Server

```
┌─────────────────────────────────────────┐
│       API Server (.exe)                 │
├─────────────────────────────────────────┤
│  FastAPI Application                    │
│  ├─ REST Endpoints                      │
│  ├─ Authentication (JWT)                │
│  ├─ CORS Middleware                     │
│  └─ Error Handlers                      │
├─────────────────────────────────────────┤
│  Business Logic                         │
│  ├─ Services                            │
│  ├─ Repositories                        │
│  └─ Models                              │
├─────────────────────────────────────────┤
│  Database Layer                         │
│  ├─ SQLAlchemy ORM                      │
│  ├─ Connection Pool                     │
│  └─ Schema Manager                      │
├─────────────────────────────────────────┤
│  Uvicorn Server                         │
│  ├─ ASGI Server                         │
│  ├─ HTTP/HTTPS                          │
│  └─ WebSocket Support                   │
├─────────────────────────────────────────┤
│  Bundled Components                     │
│  ├─ Python Interpreter                  │
│  ├─ Dependencies                        │
│  ├─ env.ini                             │
│  └─ .env                                │
└─────────────────────────────────────────┘
         │
         │ Database Connection
         ▼
┌─────────────────────────────────────────┐
│         Database Server                 │
└─────────────────────────────────────────┘
```

## Database Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Database Schema                          │
├─────────────────────────────────────────────────────────────┤
│  Core Tables                                                │
│  ├─ users                    (Authentication)               │
│  ├─ persons                  (Personnel)                    │
│  ├─ organizations            (Companies)                    │
│  ├─ counterparties           (Business partners)            │
│  ├─ objects                  (Construction sites)           │
│  └─ works                    (Work types)                   │
├─────────────────────────────────────────────────────────────┤
│  Document Tables                                            │
│  ├─ estimates                (Cost estimates)               │
│  ├─ estimate_lines           (Estimate details)             │
│  ├─ daily_reports            (Daily work reports)           │
│  ├─ daily_report_lines       (Report details)               │
│  ├─ daily_report_executors   (Workers)                      │
│  ├─ timesheets               (Time tracking)                │
│  └─ timesheet_lines          (Time details)                 │
├─────────────────────────────────────────────────────────────┤
│  Register Tables                                            │
│  ├─ work_execution_register  (Work completion)              │
│  └─ payroll_register         (Payroll data)                 │
├─────────────────────────────────────────────────────────────┤
│  System Tables                                              │
│  ├─ user_settings            (User preferences)             │
│  └─ constants                (System constants)             │
└─────────────────────────────────────────────────────────────┘

Migration Path:
SQLite (development) → PostgreSQL/MSSQL (production)
```

## Network Architecture

### Production Deployment

```
                    Internet
                       │
                       ▼
              ┌────────────────┐
              │   Firewall     │
              │  (443, 80)     │
              └────────────────┘
                       │
                       ▼
              ┌────────────────┐
              │  Load Balancer │
              │   (Optional)   │
              └────────────────┘
                       │
        ┌──────────────┼──────────────┐
        │              │              │
        ▼              ▼              ▼
┌──────────────┐ ┌──────────────┐ ┌──────────────┐
│ Web Server 1 │ │ Web Server 2 │ │ Web Server N │
│   (nginx)    │ │   (nginx)    │ │   (nginx)    │
│              │ │              │ │              │
│ Static Files │ │ Static Files │ │ Static Files │
│ /web-client/ │ │ /web-client/ │ │ /web-client/ │
└──────────────┘ └──────────────┘ └──────────────┘
        │              │              │
        └──────────────┼──────────────┘
                       │ Proxy /api
                       ▼
              ┌────────────────┐
              │  API Server    │
              │   (FastAPI)    │
              │   Port 8000    │
              └────────────────┘
                       │
                       ▼
              ┌────────────────┐
              │   Database     │
              │  PostgreSQL/   │
              │     MSSQL      │
              │   Port 5432/   │
              │      1433      │
              └────────────────┘

Desktop Clients (Direct Connection)
┌──────────────┐
│  Desktop App │
│   (PyQt6)    │
└──────────────┘
        │
        │ Direct DB Connection
        ▼
┌────────────────┐
│   Database     │
│  PostgreSQL/   │
│     MSSQL      │
└────────────────┘
```

## Security Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Security Layers                          │
├─────────────────────────────────────────────────────────────┤
│  Transport Layer                                            │
│  ├─ HTTPS/TLS (Web Client)                                 │
│  ├─ SSL/TLS (Database)                                     │
│  └─ Encrypted Connections                                  │
├─────────────────────────────────────────────────────────────┤
│  Authentication Layer                                       │
│  ├─ JWT Tokens (API)                                       │
│  ├─ Password Hashing (bcrypt)                              │
│  └─ Session Management                                     │
├─────────────────────────────────────────────────────────────┤
│  Authorization Layer                                        │
│  ├─ Role-Based Access Control                              │
│  ├─ User Permissions                                       │
│  └─ Resource Access Control                                │
├─────────────────────────────────────────────────────────────┤
│  Application Layer                                          │
│  ├─ Input Validation                                       │
│  ├─ SQL Injection Prevention (ORM)                         │
│  ├─ XSS Protection                                         │
│  └─ CSRF Protection                                        │
├─────────────────────────────────────────────────────────────┤
│  Network Layer                                              │
│  ├─ Firewall Rules                                         │
│  ├─ CORS Configuration                                     │
│  └─ Rate Limiting                                          │
└─────────────────────────────────────────────────────────────┘
```

## Deployment Environments

### Development

```
Developer Machine
├─ SQLite Database (construction.db)
├─ Python Development Server
├─ Vue.js Dev Server (Vite)
└─ Local Testing
```

### Staging

```
Staging Server
├─ PostgreSQL/MSSQL Database (staging)
├─ API Server (development build)
├─ Web Client (development build)
└─ Integration Testing
```

### Production

```
Production Servers
├─ PostgreSQL/MSSQL Database (production)
├─ API Server (optimized build)
├─ Web Client (optimized build)
├─ Load Balancer
├─ Monitoring
└─ Backups
```

## Data Flow

### Web Client Request Flow

```
User Action
    │
    ▼
Vue Component
    │
    ▼
API Client (axios)
    │
    ▼
HTTP Request
    │
    ▼
nginx (Reverse Proxy)
    │
    ▼
FastAPI Endpoint
    │
    ▼
Authentication Middleware
    │
    ▼
Business Logic (Service)
    │
    ▼
Repository (SQLAlchemy)
    │
    ▼
Database Query
    │
    ▼
Database Server
    │
    ▼
Response (JSON)
    │
    ▼
Vue Component Update
    │
    ▼
UI Render
```

### Desktop App Data Flow

```
User Action
    │
    ▼
PyQt6 Widget
    │
    ▼
Signal/Slot
    │
    ▼
Business Logic (Service)
    │
    ▼
Repository (SQLAlchemy)
    │
    ▼
Database Query
    │
    ▼
Database Server
    │
    ▼
Response (ORM Objects)
    │
    ▼
Widget Update
    │
    ▼
UI Render
```

## Scalability Considerations

### Horizontal Scaling

```
┌─────────────────────────────────────────┐
│  Load Balancer                          │
└─────────────────────────────────────────┘
         │
         ├─────────────┬─────────────┐
         ▼             ▼             ▼
    ┌────────┐    ┌────────┐    ┌────────┐
    │ API 1  │    │ API 2  │    │ API N  │
    └────────┘    └────────┘    └────────┘
         │             │             │
         └─────────────┴─────────────┘
                       │
                       ▼
              ┌────────────────┐
              │   Database     │
              │  (Primary)     │
              └────────────────┘
                       │
              ┌────────┴────────┐
              ▼                 ▼
         ┌─────────┐       ┌─────────┐
         │ Replica │       │ Replica │
         │    1    │       │    2    │
         └─────────┘       └─────────┘
```

### Caching Strategy

```
┌─────────────────────────────────────────┐
│  Application Layer                      │
│  ├─ In-Memory Cache (LRU)              │
│  └─ Session Cache                       │
└─────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────┐
│  Redis Cache (Optional)                 │
│  ├─ API Response Cache                  │
│  ├─ Session Store                       │
│  └─ Rate Limiting                       │
└─────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────┐
│  Database                               │
│  ├─ Query Cache                         │
│  └─ Connection Pool                     │
└─────────────────────────────────────────┘
```

## Monitoring Architecture

```
┌─────────────────────────────────────────┐
│  Application Logs                       │
│  ├─ API Server Logs                     │
│  ├─ Web Server Logs                     │
│  └─ Database Logs                       │
└─────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────┐
│  Log Aggregation                        │
│  ├─ ELK Stack (Optional)                │
│  └─ Centralized Logging                 │
└─────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────┐
│  Monitoring & Alerts                    │
│  ├─ Performance Metrics                 │
│  ├─ Error Tracking                      │
│  ├─ Uptime Monitoring                   │
│  └─ Alert Notifications                 │
└─────────────────────────────────────────┘
```

## Backup Strategy

```
┌─────────────────────────────────────────┐
│  Database Backups                       │
│  ├─ Full Backup (Daily)                 │
│  ├─ Incremental Backup (Hourly)         │
│  └─ Transaction Log Backup              │
└─────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────┐
│  Backup Storage                         │
│  ├─ Local Storage (Recent)              │
│  ├─ Network Storage (Archive)           │
│  └─ Cloud Storage (Disaster Recovery)   │
└─────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────┐
│  Backup Verification                    │
│  ├─ Automated Testing                   │
│  ├─ Restore Testing                     │
│  └─ Integrity Checks                    │
└─────────────────────────────────────────┘
```

---

This architecture supports:
- High availability
- Scalability
- Security
- Maintainability
- Disaster recovery
