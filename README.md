# fluffy-observability 🐩🧐
Learning observability by playing around with OpenTelemetry, Prometheus, Jaeger and Grafana. The goal here was to see how the OpenTelemetry inititative can make it easier for developers to implement observability in their software. 

Specifically, can [OpenTelemetry](https://opentelemetry.io/) help us standardize and simplify how developers implement observability on our software? Can OpenTelemetry help the platform team manage how telemetry data is exported to our backends? 

![overview](/media/obs_overview.png)

## Observability and OpenTelemetry

Telemetry data / signals consists of:
- `traces`: big picture of what happens when a request is made by user or an application. Provides insight into application's service calls. Helpful in forensic work.
- `metrics`: availability and performance data captured at runtime. Used for monitoring.
- `logs`: according to [OpenTelmetry](https://opentelemetry.io/docs/concepts/signals/logs/), any data not related to a trace or metric is a log (although logs can be a part of a trace).

Telemetry data is important for both software and platform engineers to run, manage and understand how our software is performing. 

So what's OpenTelemetry role in this? Simplified, OpenTelemetry aims to standardize how telemetry data is:
- formatted
- implemented in software
- exported to telemetry backends

![otel](/media/otel_diagram.png)

# Getting started

## Prerequisites

Install kind, ctlptl, kubectl, helm, docker, k9s and Tilt. For installation guide visit this [repo](https://github.com/daniwk/app-scaling-keda#prequisites).

## Create local cluster and install dependencies

1. Create a Kubernetes cluster: `ctlptl apply -f deploy/k8s/kind.yaml && kubectl apply -k deploy/k8s`. This will create a local k8s cluster with a built-in container registry and k8s metrics server.
2. Install cert-manager: `kubectl apply -f https://github.com/cert-manager/cert-manager/releases/download/v1.10.1/cert-manager.yaml` (change to kustomized helm later).
3. Install Promethues: `kubectl create -f https://raw.githubusercontent.com/prometheus-operator/prometheus-operator/main/bundle.yaml`
4. Install Jaeger Operator: `kubectl create namespace observability && kubectl create -f https://github.com/jaegertracing/jaeger-operator/releases/download/v1.40.0/jaeger-operator.yaml -n observability`
5. Install OpenTelemtry Operator: `kubectl apply -f https://github.com/open-telemetry/opentelemetry-operator/releases/latest/download/opentelemetry-operator.yaml`
6. Install Grafana Operator: `helm repo add my-repo https://charts.bitnami.com/bitnami && helm install grafana bitnami/grafana-operator --set grafana.enabled=false`. Port-forward the `grafana-service` service. Fetch login credentials from `grafana-admin-credentials` secret.
7. Deploy Prometheus: `kubectl apply -k deploy/k8s/prometheus`. Port-forward the `prometheus-operated` and `alertmanager-operated` services. 
8. Deploy Jaeger: `kubectl apply -k deploy/k8s/jaeger`. Port-forward the `simplest-query port 16686` service.

# OpenTelemetry with Python and FastAPI

> Goal: hands-off instrumentation of a Python API with OpenTelemetry to expose traces and metrics data. 

We will use the OpenTelemetry Operator to test this. The operator manages two custom resource definitions:
- OpenTelemetry Collector. Component responsible for configuring how and where telemetry data are received, processed and exported.
- OpenTelemetry Instrumentation. Component responsible for injecting workloads with auto-instrumentated OpenTelemetry SDK. 

Specifically, we want to use the Instrumentation resource to inject and automatically instrument our API so that it exposes both traces and metrics, while we use the collector to be responsible for fetching the telemetry data and export it to relevant backends (Jaeger for traces and Prometheus for metrics).

![python-overview](/media/obs_python.png)

## Test it locally

We'll use the following app (based on FastAPI) to test the capabilities of OpenTelemetry (`/app/python/main.py`). As you can see, the code itself does not contain any OpenTelemetry libraries:

```python
from typing import Union
from fastapi import FastAPI
import requests

app = FastAPI()

@app.get("/hello")
def read_root():
    r = requests.get('https://api.github.com/user')
    r.status_code
    return {"Hello": "World"}


@app.get("/items/{item_id}")
def read_item(item_id: int, q: Union[str, None] = None):
    return {"item_id": item_id, "q": q}

```
### Build and deploy our API in our local cluster
The k8s manifests we use to run the API in our local cluster can be viewed in the files (`/deploy/app/python/deployment.yaml` and `/deploy/app/python/service.yaml`). Tilt is used to build the API container image and actually deployed to our cluster (`/app/python/Tiltfile`).

Use tilt to build and deploy the above-mentioned to our local k8s cluster: `cd app/python && tilt up`. Press `space` to verify that the API is running. This will open a tab in your browser displaying the progress of your app deployment:

![tilt-python](/media/tilt_python.png)

Visit http://localhost:8000/hello to verify it's working. 


### Use OpenTelemetry Collector and Instrumentation
We can now add OpenTelemetry to instrument, collect and export telemetry data from our API. First, we configure the Instrumentation resource (`deploy/app/python/otel-instrumentation.yaml`):

```yaml
apiVersion: opentelemetry.io/v1alpha1
kind: Instrumentation
metadata:
  name: python-instrumentation
  namespace: default
spec:
  python:
    env:
    - name: OTEL_METRICS_EXPORTER
      value: otlp_proto_http
    - name: OTEL_EXPORTER_OTLP_ENDPOINT
      value: http://otel-collector:4318
    image: ghcr.io/open-telemetry/opentelemetry-operator/autoinstrumentation-python:0.36b0
  sampler:
    argument: "0.25"
    type: parentbased_traceidratio

```

This resource is responsible to inject instrumented (i.e. ready to use) OpenTelemetry libraries which exposes traces and metrics. The resource provides some basic configuration for the injection itself (e.g. where to export data, what type of data should be exported and the sample rate). This resource will inject workloads which have the following annonations added to their workloads:

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: python-api
spec:
  selector:
    matchLabels:
      app: python-api
  template:
    metadata:
      labels:
        app: python-api
      annotations:
        instrumentation.opentelemetry.io/inject-python: "true"
    ...
```

Since we have already done this we only need to add the Instrumentation resource to the cluster and redeploy our API to inject with the OpenTelemetry instrumentation:
- Apply the resource to your cluster by running `kubectl apply -f deploy/app/python/otel-instrumentation.yaml`. 
- Redeploy the app by pressing the refresh button in the Tilt tab in your browser. 

You can use k9s to see that the Instrumentation resource have added a init container named `opentelemetry-auto-instrumentation` to our deployment, which is used to the actual injection:

![injection](/media/inject.png)

Next step is to configure the Collector (`deploy/app/python/otel-collector.yaml`):
```yaml
apiVersion: opentelemetry.io/v1alpha1
kind: OpenTelemetryCollector
metadata:
  name: otel
  namespace: default
  labels:
    app: otel-python-api
spec:
  config: |
    receivers:
      otlp:
        protocols:
          grpc:
          http:

    processors:
      batch:

    exporters:
      logging:

      jaeger:
        endpoint: simplest-collector.observability.svc.cluster.local:14250
        tls:
          insecure: true
      
      prometheus:
        endpoint: '0.0.0.0:8889'
        namespace: default

      otlp:
        endpoint: '0.0.0.0:8889'
        tls:
          insecure: true


    service:
      pipelines:
        traces:
          receivers: [otlp]
          processors: []
          exporters: [logging, jaeger]
        metrics:
          receivers: [otlp]
          processors: []
          exporters: [logging, prometheus]
```

It configures where to receive data from (`otlp`), how to process it `batch` and where to send it `exporters`. The [full documentation](https://opentelemetry.io/docs/collector/configuration/) provides a good explanation, but in summary we define that we will receive both traces and metrics over the otlp receiver, we will batch the export of that data, and we send the traces to our Jaeger instance and the metrics to our Prometheus instance.

Apply the resource to your cluster by running `kubectl apply -f deploy/app/python/otel-collector.yaml`. 

### View the data in Jaeger and Prometheus
You can now view both traces and metrics in, respectively, Jaeger and Prometheus, without changing your application code! 

Visit both http://localhost:8000/hello and http://localhost:8000/items/1 to generate some traffic. 

Traces can now be viewed on Jaeger on http://localhost:16686/ and filtering for the `python-api` service:
![jaeger](/media/jaeger_python.png)

Metrics can be viewed in Prometheus on http://localhost:9090/:
![prometheus](/media/prom_python.png)