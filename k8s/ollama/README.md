# Optional In-Cluster Ollama (On-Premises / Offline Only)

> **Notice:** Standard production deployment uses **Groq API** (`LLM_PROVIDER=groq`) as configured in `k8s/configmap.yaml`. 
> 
> The manifests in this directory (`deployment.yaml`, `service.yaml`, `pvc.yaml`) are preserved strictly for **offline, private on-premises, or air-gapped hospital intranet** deployments where external cloud egress to Groq is prohibited.
> 
> When deploying to standard cloud environments (e.g. AWS EKS, Google GKE, Azure AKS), **do NOT deploy this directory**.
