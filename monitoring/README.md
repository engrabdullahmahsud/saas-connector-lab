# Monitoring

Phase 11 monitoring uses kube-prometheus-stack with Prometheus and Grafana.

## Install

Create the namespace:

    kubectl create namespace monitoring

Add the Prometheus Community Helm repository:

    helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
    helm repo update

Install the monitoring stack:

    helm install monitoring prometheus-community/kube-prometheus-stack --namespace monitoring -f monitoring/values.yaml

## Verify

    kubectl get pods -n monitoring

Expected components:

- Grafana
- Prometheus
- Alertmanager
- kube-prometheus-operator
- kube-state-metrics

## Access Grafana

    kubectl port-forward -n monitoring svc/monitoring-grafana 3000:80

Open http://localhost:3000.

Get the Grafana admin password:

    kubectl get secret -n monitoring monitoring-grafana -o jsonpath="{.data.admin-password}" | base64 -d; echo

## Application Monitoring

The saas-connector namespace is monitored through the Kubernetes dashboards.

Verified workloads:

- API
- PostgreSQL
- Redis

Grafana confirms CPU usage and running pod metrics for all three workloads.

## Configuration

The Helm values are stored in monitoring/values.yaml.

Node Exporter is disabled because the current K3s environment does not support the host root mount configuration required by the chart Node Exporter deployment.
