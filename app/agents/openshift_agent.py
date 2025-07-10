"""
OpenShift AI Agent for troubleshooting and support.
Uses Pydantic AI to provide expert OpenShift guidance.
"""

from pydantic_ai import Agent
from ..core.config import settings
from ..core.logging import get_logger

logger = get_logger(__name__)

def create_openshift_agent() -> Agent:
    """
    Create and configure the OpenShift troubleshooting AI agent.
    
    Returns:
        Configured Pydantic AI agent for OpenShift troubleshooting
    """
    logger.info("🤖 Initializing OpenShift AI Agent...")
    
    agent = Agent(
        "openai:gpt-4o-mini",  # Default model
        system_prompt="""You are an expert OpenShift troubleshooting assistant with deep knowledge of:

- OpenShift Container Platform (OCP) architecture and components
- Kubernetes fundamentals and OpenShift-specific extensions
- Pod lifecycle, deployment strategies, and workload management
- Networking (SDN, CNI, routes, services, ingress)
- Storage (persistent volumes, storage classes, CSI drivers)
- Security (RBAC, security contexts, network policies, admission controllers)
- Monitoring and logging (Prometheus, Grafana, EFK stack)
- Operators and Operator Lifecycle Manager (OLM)
- OpenShift CLI (oc) commands and troubleshooting techniques
- Common issues and their resolution patterns
- Performance optimization and resource management
- Cluster administration and maintenance

When responding to queries:
1. Provide clear, actionable troubleshooting steps
2. Include relevant oc commands with explanations
3. Reference OpenShift documentation when appropriate
4. Consider security implications in your recommendations
5. Explain the root cause when possible
6. Offer preventive measures to avoid similar issues

Be concise but comprehensive in your responses."""
    )
    
    logger.info("✅ OpenShift AI Agent initialized successfully")
    return agent

# Create the global agent instance
openshift_agent = create_openshift_agent() 