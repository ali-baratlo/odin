# Odin - Kubernetes Resource Collector and Inspector

Odin is a powerful, containerized application designed to collect, store, and inspect Kubernetes resources from multiple clusters. It provides a RESTful API and a simple web interface to search and analyze resource configurations, making it easy to track changes, audit configurations, and ensure consistency across environments.

## Key Features

- **Multi-Cluster Support**: Collects resources from any number of Kubernetes or OKD clusters.
- **Comprehensive Resource Collection**: Gathers a wide range of resources, including ConfigMaps, Secrets, Deployments, Services, and Ingresses.
- **MongoDB Backend**: Stores all resources as structured JSON documents in a MongoDB database, enabling flexible and powerful queries.
- **Resource Versioning & Auditing**: Tracks changes to resources over time by storing new versions and logging the differences.
- **RESTful API**: A robust FastAPI-powered API for listing, inspecting, and searching resources.
- **Automatic Documentation**: Interactive API documentation (Swagger UI) is automatically generated and available at `/docs`.
- **Scheduled Data Collection**: A background job runs periodically to keep the resource data up-to-date.
- **Containerized & Deployable**: Easily deployable with Docker and `docker-compose`.

## Technology Stack

- **Backend**: Python 3, FastAPI
- **Database**: MongoDB
- **Kubernetes Client**: `kubernetes` Python client
- **Containerization**: Docker, Docker Compose

## Getting Started

### Prerequisites

- [Docker](https://docs.docker.com/get-docker/)
- [Docker Compose](https://docs.docker.com/compose/install/)

### Setup & Running the Project

1.  **Clone the repository:**
    ```bash
    git clone <repository-url>
    cd <repository-directory>
    ```

2.  **Configure Cluster Connections:**

    Create a `clusters.yaml` file in the root of the project. This file defines the clusters you want to collect resources from.

    ```yaml
    # clusters.yaml
    - name: my-cluster-1
      api_server: https://api.my-cluster-1.com:6443
      token_env: MY_CLUSTER_1_TOKEN

    - name: my-cluster-2
      api_server: https://api.my-cluster-2.com:6443
      token_env: MY_CLUSTER_2_TOKEN
    ```

3.  **Set Environment Variables:**

    Odin uses environment variables to securely load the authentication tokens for your clusters. Create a `.env` file in the root directory:

    ```env
    # .env
    MY_CLUSTER_1_TOKEN="your-kube-api-token-for-cluster-1"
    MY_CLUSTER_2_TOKEN="your-kube-api-token-for-cluster-2"
    ```
    *Note: The `token_env` value in `clusters.yaml` must match the environment variable name in your `.env` file.*

4.  **Build and Run with Docker Compose:**

    With the configuration in place, start the application:
    ```bash
    docker-compose up --build
    ```
    This will build the FastAPI application image and start both the `web` and `mongo` services.

5.  **Access the Application:**

    - **Web Interface**: Open your browser to [http://localhost:8000](http://localhost:8000)
    - **API Documentation**: Access the interactive Swagger UI at [http://localhost:8000/docs](http://localhost:8000/docs)

## API Endpoints

The application provides several API endpoints for interacting with the collected resource data. For detailed information and to try them out, please visit the `/docs` endpoint.

- `GET /api/resources`: List and search for resources.
- `GET /api/resources/{resource_id}`: Inspect a single resource by its ID.
- `GET /filters/*`: Get unique values for filters like cluster names, namespaces, and resource types.

The resource collector will run automatically upon startup and then every 5 minutes to keep the data fresh. You can monitor the collection process in the container logs.