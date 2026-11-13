---
name: k8s-deploy
description: Write and review Kubernetes manifests and Helm values for service deployments.
---
# Kubernetes deployment

Use this skill when a task touches `deploy/` manifests, Helm charts or rollout configuration.

## Workloads

- Every service runs as a `Deployment` with at least two replicas in staging and three in production.
- Set `resources.requests` and `resources.limits` for CPU and memory on every container; requests come from
  the last 14 days of p95 usage plus 20 percent.
- Never set a CPU limit lower than the request; prefer no CPU limit for latency-sensitive services.
- Use `readinessProbe` for traffic gating and `livenessProbe` only for deadlock detection; they must not share
  an endpoint that depends on downstream services.
- `startupProbe` is required for anything that takes longer than 10 seconds to boot.
- Set `terminationGracePeriodSeconds` longer than the longest in-flight request plus the preStop sleep.
- Add a `preStop` hook that sleeps 5 seconds so endpoints are removed before shutdown begins.

## Rollouts

- Use `RollingUpdate` with `maxUnavailable: 0` and `maxSurge: 25%` unless the service is a singleton.
- Every Deployment has a `PodDisruptionBudget` with `minAvailable` of at least one less than replicas.
- Pin images by digest in production overlays; tags are allowed only in development.
- Canary releases use the `argo-rollouts` `Rollout` resource with analysis templates on error rate and p99 latency.
- Roll back automatically when the analysis fails twice in a row.

## Configuration and secrets

- Configuration comes from `ConfigMap`s rendered by Helm; secrets come from the external secrets operator.
- Never commit a `Secret` manifest with data, even base64 encoded.
- Mount secrets as files, not environment variables, when the library supports it.
- Changing a ConfigMap must roll the pods: include a checksum annotation of the rendered config.

## Networking

- Every namespace has a default-deny `NetworkPolicy`; add explicit ingress and egress rules per service.
- Services expose named ports (`http`, `grpc`, `metrics`) and use `appProtocol`.
- Ingress uses the shared class `public-nginx`; internal services use `internal-nginx`.
- TLS certificates come from cert-manager; never embed certificates in charts.

## Scheduling

- Use topology spread constraints across zones with `maxSkew: 1`.
- Use `podAntiAffinity` (preferred, not required) across nodes for replicated services.
- GPU workloads use the `gpu` node pool taint and tolerations; nothing else may tolerate it.
- Batch jobs set `ttlSecondsAfterFinished` and `backoffLimit`.

## Observability

- Expose Prometheus metrics on the `metrics` port and add a `ServiceMonitor`.
- Logs are JSON on stdout with `trace_id` and `span_id` fields.
- Every alert links to a runbook in `docs/runbooks/`.
- Dashboards are provisioned from JSON in the chart, not edited by hand.

## Security context

- `runAsNonRoot: true`, `readOnlyRootFilesystem: true`, drop all capabilities.
- `allowPrivilegeEscalation: false` on every container.
- Use a dedicated `ServiceAccount` per service with `automountServiceAccountToken: false` unless the API is used.
- Seccomp profile `RuntimeDefault`.

## Review checklist

- [ ] Requests and limits justified by usage data
- [ ] Probes separated and tested
- [ ] PDB and rollout strategy present
- [ ] Images pinned by digest for production
- [ ] NetworkPolicy and security context present
- [ ] Metrics, logs and alerts wired
