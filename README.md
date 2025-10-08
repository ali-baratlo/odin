# Odin - Kubernetes Resource Collector and Inspector

Odin is a powerful, containerized application designed to collect, store, and inspect Kubernetes resources from multiple clusters. It features a modern React frontend and a robust FastAPI backend, providing an interactive and user-friendly experience for searching and analyzing resource configurations.

## Key Features

- **Modern React Frontend**: A fast, responsive, and intuitive user interface built with React and Vite.
- **Multi-Cluster Support**: Collects resources from any number of Kubernetes or OKD clusters.
- **Comprehensive Resource Collection**: Gathers a wide range of resources, including Pods, ConfigMaps, Secrets, Services, Deployments, StatefulSets, DaemonSets, Jobs, CronJobs, Ingresses, NetworkPolicies, PersistentVolumes (PVs), PersistentVolumeClaims (PVCs), HorizontalPodAutoscalers (HPAs), and CustomResourceDefinitions (CRDs).
- **MongoDB Backend**: Stores all resources as structured JSON documents, enabling flexible and powerful queries.
- **Resource Versioning & Auditing**: Tracks changes to resources over time by storing new versions and logging the differences.
- **RESTful API**: A robust FastAPI-powered API for all data operations.
- **Scheduled Data Collection**: A background job runs periodically to keep the resource data up-to-date.
- **Containerized & Deployable**: A multi-stage Docker build creates a single, optimized image for easy deployment.

## Technology Stack

- **Frontend**: React, Vite, Axios
- **Backend**: Python 3, FastAPI
- **Database**: MongoDB
- **Kubernetes Client**: `kubernetes` Python client
- **Containerization**: Docker, Docker Compose

## Project Structure

The project is now a monorepo with a separate frontend and backend:
-   `/frontend`: Contains the React application.
-   `/`: The root directory contains the Python backend and all Docker-related files.

## Getting Started

### Prerequisites

- [Docker](https://docs.docker.com/get-docker/)
- [Docker Compose](https://docs.docker.com/compose/install/)
- [Node.js and npm](https://nodejs.org/en/) (for local frontend development)

### Production (Docker)

This is the recommended way to run the application for most users.

1.  **Configure Cluster Connections:**
    Create a `clusters.yaml` file in the root of the project.
    ```yaml
    # clusters.yaml
    - name: my-cluster-1
      api_server: https://api.my-cluster-1.com:6443
      token_env: MY_CLUSTER_1_TOKEN
      namespace_label_selector: "environment=production" # Optional
      fqdn_env: MY_CLUSTER_1_FQDN # Optional: For generating clickable links

    - name: my-cluster-2
      api_server: https://api.my-cluster-2.com:6443
      token_env: MY_CLUSTER_2_TOKEN
      fqdn_env: MY_CLUSTER_2_FQDN
    ```

2.  **Set Environment Variables:**
    Create a `.env` file in the root directory. This file is used for your cluster tokens and other optional configurations.

    ```env
    # .env
    # Required: Cluster access tokens
    MY_CLUSTER_1_TOKEN="your-kube-api-token-for-cluster-1"
    MY_CLUSTER_2_TOKEN="your-kube-api-token-for-cluster-2"

    # Optional: FQDNs for cluster UI links
    MY_CLUSTER_1_FQDN="console.apps.my-cluster-1.com"
    MY_CLUSTER_2_FQDN="console.apps.my-cluster-2.com"

    # Optional: Scheduler interval
    # Set how often the collector runs (in hours). Defaults to 1.
    SCHEDULER_INTERVAL_HOURS=2
    ```

3.  **Build and Run with Docker Compose:**
    ```bash
    docker compose up --build
    ```
    This command will build the frontend, build the backend, and start all services.

4.  **Access the Application:**
    - **Web App**: [http://localhost:8000](http://localhost:8000)
    - **API Docs**: [http://localhost:8000/docs](http://localhost:8000/docs)

### Local Development

For developers who want to work on the frontend and backend separately.

1.  **Start the Backend:**
    - Ensure you have a MongoDB instance running.
    - Set up your `clusters.yaml` and `.env` files as described above.
    - Run the Python application:
      ```bash
      pip install -r requirements.txt
      uvicorn main:app --reload
      ```
    The backend will be available at `http://localhost:8000`.

2.  **Start the Frontend:**
    - Navigate to the `frontend` directory.
    - Install dependencies and start the Vite development server:
      ```bash
      cd frontend
      npm install
      npm run dev
      ```
    The frontend development server will be available at `http://localhost:5173` (or another port if 5173 is in use). Vite will proxy API requests to the backend at `http://localhost:8000`.

    *Note: A `vite.config.js` is included to handle the proxying of `/api` and `/filters` requests.*

## API Endpoints

The application provides several API endpoints for interacting with the collected resource data. For detailed information and to try them out, please visit the `/docs` endpoint.

- `GET /api/resources`: List and search for resources.
- `GET /api/resources/{resource_id}`: Inspect a single resource by its ID.
- `GET /filters/*`: Get unique values for filters like cluster names, namespaces, and resource types.
- `GET /api/related-namespaces`: Find all namespaces where a resource with a specific name and type exists.

The resource collector will run automatically upon startup and then every 5 minutes to keep the data fresh. You can monitor the collection process in the container logs.