-- ---
-- init.sql for PostgreSQL
-- ---

-- CREATE DATABASE odin;
-- CREATE USER odin WITH PASSWORD 'odin';
-- GRANT ALL PRIVILEGES ON DATABASE odin TO odin;




SET client_encoding = 'UTF8';

-- ---
-- Table: public.k8s_resources
-- ---
CREATE TABLE IF NOT EXISTS public.k8s_resources (
    id SERIAL PRIMARY KEY, 
    cluster_name TEXT NOT NULL,
    namespace TEXT NOT NULL,
    resource_type TEXT NOT NULL,
    resource_name TEXT NOT NULL,
    resource_uid TEXT,
    version TEXT,
    collected_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    raw_json JSONB NOT NULL,
    labels JSONB,
    annotations JSONB,
    hash TEXT,
    version_int INTEGER DEFAULT 1,
    pretty_json TEXT,
    config_values TEXT,
    config_keys TEXT,

    CONSTRAINT uniq_k8s_resource_version UNIQUE (cluster_name, resource_type, namespace, resource_name, version)
);

-- ---
-- Indexes for public.k8s_resources
-- k8s_resources_pkey is automatically created by SERIAL PRIMARY KEY
-- ---
-- No explicit CREATE INDEX for uniq_resource_version needed if defined as a UNIQUE CONSTRAINT

-- ---
-- Table: public.configmap_kv_pairs
-- ---
CREATE TABLE public.configmap_kv_pairs (
    id SERIAL PRIMARY KEY,
    cluster_name TEXT NOT NULL,
    namespace TEXT NOT NULL,
    configmap_name TEXT NOT NULL,
    key TEXT NOT NULL,
    value TEXT,
    collected_at TIMESTAMP WITHOUT TIME ZONE DEFAULT NOW(),
    CONSTRAINT unique_configmap_entry UNIQUE (cluster_name, namespace, configmap_name, key)
);

-- ---
-- Indexes for public.configmap_kv_pairs
-- configmap_kv_pairs_pkey is automatically created by SERIAL PRIMARY KEY
-- ---


-- ---
-- Table: public.resource_audit_logs
-- ---
CREATE TABLE IF NOT EXISTS public.resource_audit_logs (
    id SERIAL PRIMARY KEY,
    cluster_name TEXT,
    namespace TEXT,
    resource_type TEXT,
    resource_name TEXT,
    version_old INTEGER,
    version_new INTEGER,
    diff JSONB,
    created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT NOW()
);

-- ---
-- Indexes for public.resource_audit_logs
-- resource_audit_logs_pkey is automatically created by SERIAL PRIMARY KEY
-- ---


-- ---
-- Table: public.metadata
-- ---
CREATE TABLE metadata (
    uid UUID PRIMARY KEY,
    name VARCHAR(63) NOT NULL,
    cluster_name VARCHAR(100) NOT NULL,
    labels JSONB,
    team TEXT,
    environment TEXT,
    annotations JSONB,
    resource_version TEXT,
    creation_timestamp TIMESTAMP WITH TIME ZONE,
    self_link TEXT,
    generate_name TEXT,
    owner_references JSONB,
    CONSTRAINT uniq_cluster_name UNIQUE (cluster_name, name)
);