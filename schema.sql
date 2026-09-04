-- ==========================================================
-- DevOps Project Tracker - Database Initialization Schema
-- ==========================================================

-- 1. Create database if it does not already exist
CREATE DATABASE IF NOT EXISTS devops_tracker
    CHARACTER SET utf8mb4
    COLLATE utf8mb4_unicode_ci;

USE devops_tracker;

-- 2. Create projects table
CREATE TABLE IF NOT EXISTS projects (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(150) NOT NULL,
    description TEXT,
    technology VARCHAR(255) NOT NULL,
    status ENUM('Planning', 'In Progress', 'Completed') NOT NULL DEFAULT 'Planning',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 3. Seed sample records for DevOps portfolio demonstration
INSERT INTO projects (name, description, technology, status) VALUES
(
    'CI/CD Pipeline Automation',
    'Automated continuous integration and deployment pipeline for multi-service microservices application.',
    'Jenkins, GitHub Actions, Docker, SonarQube',
    'Completed'
),
(
    'Kubernetes Production Cluster Setup',
    'Highly available multi-node Kubernetes cluster configuration with ingress controllers and cert-manager.',
    'Kubernetes, Helm, NGINX Ingress, containerd',
    'In Progress'
),
(
    'Infrastructure as Code (IaC) Provisioning',
    'Automated AWS cloud provisioning containing VPC, public/private subnets, NAT gateways, and EC2 instances.',
    'Terraform, AWS, AWS CLI, Bash',
    'In Progress'
),
(
    'Centralized Observability & Monitoring',
    'Cluster-wide observability stack for metric scraping, log aggregation, and real-time alerting dashboards.',
    'Prometheus, Grafana, Alertmanager, Node Exporter',
    'Planning'
),
(
    'Zero-Downtime Blue/Green Deployment',
    'Deployment strategy enabling seamless zero-downtime application releases with rapid rollback capability.',
    'Docker, NGINX, Python, Shell',
    'Planning'
);
