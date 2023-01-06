# fluffy-observability 🐩🧐
Learning (?) observability by playing around with OpenTelemetry, Prometheus and Jaeger

# Getting started

## Prerequisites

Install kind, ctlptl, kubectl, helm, docker, k9s and Tilt. For installation guide visit this [repo](https://github.com/daniwk/app-scaling-keda#prequisites).

## Create local cluster and install dependencies

1. Create a Kubernetes cluster: `ctlptl apply -f deploy/k8s/kind.yaml && kubectl apply -k deploy/k8s`. This will create a local k8s cluster with a built-in container registry and k8s metrics server.
2. Install cert-manager: `kubectl apply -f https://github.com/cert-manager/cert-manager/releases/download/v1.10.1/cert-manager.yaml` (change to kustomized helm later).
3. Install Promethues: `kubectl create -f https://raw.githubusercontent.com/prometheus-operator/prometheus-operator/main/bundle.yaml`
4. Install Jaeger Operator: `kubectl create namespace observability && kubectl create -f https://github.com/jaegertracing/jaeger-operator/releases/download/v1.40.0/jaeger-operator.yaml -n observability`
5. Install OpenTelemtry Operator: `kubectl apply -f https://github.com/open-telemetry/opentelemetry-operator/releases/latest/download/opentelemetry-operator.yaml`
6. Install Grafana Operator: `helm repo add my-repo https://charts.bitnami.com/bitnami && helm install my-grafana-release my-repo/grafana-operator`. Port-forward the `prometheus-operated` and `grafana-service` service. Fetch login credentials from `grafana-admin-credentials` secret.

## Deploy the stuff

1. Deploy Prometheus: `kubectl apply -k deploy/prometheus`. Port-forward the `prometheus-operated` and `alertmanager-operated` services. 
2. Deploy Jaeger: `kubectl apply -k deploy/jaeger`. Port-forward the `simplest-query port 16686` service.