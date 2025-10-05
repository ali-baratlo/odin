import yaml from 'js-yaml';
import ini from 'ini';

/**
 * Takes a raw resource object and returns a structured, human-readable summary.
 * @param {object} resource - The full resource object from the API.
 * @returns {object} A dictionary of key-value pairs for the summary view.
 */
export function presentResource(resource) {
  const resourceType = resource?.resource_type?.toLowerCase();
  const data = resource?.data || {};

  switch (resourceType) {
    case 'deployment':
      return presentDeployment(data);
    case 'service':
      return presentService(data);
    case 'secret':
      return presentSecret(data);
    case 'ingress':
      return presentIngress(data);
    case 'configmap':
      return presentConfigMap(data);
    default:
      // A sensible fallback for unknown resource types
      return { "Info": "No specific summary view available for this resource type.", "Data": data };
  }
}

function presentDeployment(data) {
  const spec = data.spec || {};
  const status = data.status || {};
  const templateSpec = spec.template?.spec || {};
  const containers = templateSpec.containers || [];

  return {
    "Replicas": `${status.readyReplicas || 0} / ${spec.replicas || 0}`,
    "Strategy": spec.strategy?.type || 'N/A',
    "Containers": containers.map(c => ({
      Name: c.name,
      Image: c.image,
      Ports: c.ports ? c.ports.map(p => p.containerPort).join(', ') : 'None',
    })),
    "Conditions": status.conditions ? status.conditions.map(c => `${c.type}: ${c.status}`) : [],
  };
}

function presentService(data) {
  const spec = data.spec || {};
  return {
    "Type": spec.type,
    "Cluster IP": spec.clusterIP,
    "Ports": spec.ports ? spec.ports.map(p => `${p.name || ''} ${p.port}:${p.targetPort}/${p.protocol}`) : [],
    "Selector": spec.selector || 'None',
  };
}

function presentSecret(data) {
  return {
    "Type": data.type,
    "Data Keys": Object.keys(data.data || {}),
  };
}

function presentIngress(data) {
    const spec = data.spec || {};
    const rules = spec.rules || [];

    return {
        "Ingress Class": spec.ingressClassName || 'None',
        "Rules": rules.map(rule => ({
            Host: rule.host,
            Paths: rule.http?.paths.map(p =>
                `${p.path} ➔ ${p.backend.service?.name}:${p.backend.service?.port?.number || p.backend.service?.port?.name}`
            ) || [],
        })),
    };
}

function presentConfigMap(data) {
    const configData = data.data || {};
    const presentedData = {};

    for (const key in configData) {
        const value = configData[key];
        try {
            if (key.endsWith('.yml') || key.endsWith('.yaml') || key.endsWith('.conf')) {
                const parsed = yaml.load(value);
                // Ensure we don't return null or undefined, which can break rendering.
                presentedData[key] = parsed || value;
            } else if (key.endsWith('.ini')) {
                presentedData[key] = ini.parse(value);
            } else {
                presentedData[key] = value;
            }
        } catch (e) {
            // If parsing fails, fall back to the raw text.
            console.error(`Failed to parse ${key}:`, e);
            presentedData[key] = value;
        }
    }
    return presentedData;
}