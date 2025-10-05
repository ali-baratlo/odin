import React, { useState, useEffect } from 'react';
import axios from 'axios';
import yaml from 'js-yaml';
import ini from 'ini';
import { presentResource } from './presenter';
import './App.css';

const SearchForm = ({ onSearch, loading, filters }) => {
  const [params, setParams] = useState({
    keyword: '',
    cluster_name: '',
    namespace: '',
    resource_type: '',
    resource_name: '',
    limit: 100,
  });

  const handleChange = (e) => {
    const { name, value } = e.target;
    setParams(prev => ({ ...prev, [name]: value }));
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    onSearch(params);
  };

  return (
    <form onSubmit={handleSubmit} className="search-form">
      <div className="form-row">
        <input
          type="text"
          name="keyword"
          placeholder="Keyword to search"
          value={params.keyword}
          onChange={handleChange}
          className="search-keyword-input"
        />
        <button type="submit" disabled={loading}>
          {loading ? 'Searching...' : 'Search'}
        </button>
      </div>
      <div className="form-row">
        <select name="cluster_name" value={params.cluster_name} onChange={handleChange}>
          <option value="">All Clusters</option>
          {filters.cluster_names.map(name => <option key={name} value={name}>{name}</option>)}
        </select>
        <select name="namespace" value={params.namespace} onChange={handleChange}>
          <option value="">All Namespaces</option>
          {filters.namespaces.map(name => <option key={name} value={name}>{name}</option>)}
        </select>
        <select name="resource_type" value={params.resource_type} onChange={handleChange}>
          <option value="">All Resource Types</option>
          {filters.resource_types.map(name => <option key={name} value={name}>{name}</option>)}
        </select>
        <input
          type="text"
          name="resource_name"
          placeholder="Resource Name (Optional)"
          value={params.resource_name}
          onChange={handleChange}
        />
        <input
          type="number"
          name="limit"
          value={params.limit}
          onChange={handleChange}
          className="limit-input"
        />
      </div>
    </form>
  );
};

const Highlight = ({ text, keyword }) => {
    if (!keyword || !text) return text;
    const regex = new RegExp(`(${keyword})`, 'gi');
    return text.split(regex).map((part, index) =>
      regex.test(part) ? <span key={index} className="highlight">{part}</span> : part
    );
};

const Snippet = ({ text, keyword, contextLines = 10 }) => {
    const lines = text.split('\n');
    const lineIndicesToShow = new Set();

    lines.forEach((line, i) => {
        if (keyword && line.toLowerCase().includes(keyword.toLowerCase())) {
            const start = Math.max(0, i - contextLines);
            const end = Math.min(lines.length, i + contextLines + 1);
            for (let j = start; j < end; j++) {
                lineIndicesToShow.add(j);
            }
        }
    });

    if (lineIndicesToShow.size === 0) return <Highlight text={text} keyword={keyword} />;

    const sortedIndices = Array.from(lineIndicesToShow).sort((a, b) => a - b);

    return (
        <div className="snippet-container">
            {sortedIndices.map(index => (
                <div key={index} className="snippet-line">
                    <span className="line-number">{index + 1}</span>
                    <span className="line-text"><Highlight text={lines[index]} keyword={keyword} /></span>
                </div>
            ))}
        </div>
    );
};

const ValueRenderer = ({ value, keyword, filename }) => {
    if (keyword && typeof value === 'string' && value.includes('\n')) {
        return <Snippet text={value} keyword={keyword} />;
    }

    if (typeof value === 'string') {
        try {
            if (filename.endsWith('.yml') || filename.endsWith('.yaml')) {
                const parsed = yaml.load(value);
                return <pre>{JSON.stringify(parsed, null, 2)}</pre>;
            }
            if (filename.endsWith('.ini') || filename.endsWith('.conf')) {
                const parsed = ini.parse(value);
                return <pre>{JSON.stringify(parsed, null, 2)}</pre>;
            }
        } catch (e) {
            return <pre>{value}</pre>;
        }
    }

    if (typeof value === 'object' && value !== null) {
        return <pre>{JSON.stringify(value, null, 2)}</pre>;
    }
    return <Highlight text={String(value)} keyword={keyword} />;
};

const ResourceCard = ({ resource, keyword }) => {
  const [activeTab, setActiveTab] = useState('summary');
  const summaryData = presentResource(resource);
  const isConfigMap = resource.resource_type?.toLowerCase() === 'configmap';

  const summary = (
    <div className="key-value-table">
      {Object.entries(summaryData).map(([key, value]) => (
        <div className="kv-row" key={key}>
          <div className="kv-key"><Highlight text={key} keyword={keyword} /></div>
          <div className="kv-value">
            <ValueRenderer
              value={value}
              keyword={keyword}
              filename={isConfigMap ? key : ""}
            />
          </div>
        </div>
      ))}
    </div>
  );

  const rawData = (
    <div className="code-block">
        <pre><code><Highlight text={JSON.stringify(resource.data, null, 2)} keyword={keyword} /></code></pre>
    </div>
  );

  return (
    <div className="resource-card">
      <h3><Highlight text={resource.resource_name} keyword={keyword} /> (<Highlight text={resource.resource_type} keyword={keyword} />)</h3>
      <p>
        <strong>Cluster:</strong> <Highlight text={resource.cluster_name} keyword={keyword} /> | <strong>Namespace:</strong> <Highlight text={resource.namespace} keyword={keyword} />
      </p>
      <div className="tab-buttons">
        <button className={activeTab === 'summary' ? 'active' : ''} onClick={() => setActiveTab('summary')}>Summary</button>
        <button className={activeTab === 'raw' ? 'active' : ''} onClick={() => setActiveTab('raw')}>Raw Data</button>
      </div>
      <div className="tab-content">
        {activeTab === 'summary' ? summary : rawData}
      </div>
    </div>
  );
};

const Results = ({ results, keyword }) => {
  if (!results.length) {
    return <p>No results found.</p>;
  }
  return (
    <div className="results-container">
      {results.map(res => <ResourceCard key={res.id} resource={res} keyword={keyword} />)}
    </div>
  );
};

function App() {
  const [results, setResults] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [filters, setFilters] = useState({ cluster_names: [], namespaces: [], resource_types: [] });
  const [searchKeyword, setSearchKeyword] = useState('');

  useEffect(() => {
    const fetchFilters = async () => {
      try {
        const [clusters, namespaces, types] = await Promise.all([
          axios.get('/filters/cluster_names'),
          axios.get('/filters/namespaces'),
          axios.get('/filters/resource_types'),
        ]);
        setFilters({
          cluster_names: clusters.data,
          namespaces: namespaces.data,
          resource_types: types.data,
        });
      } catch (err) {
        console.error("Failed to load filters", err);
      }
    };
    fetchFilters();
  }, []);

  const handleSearch = async (params) => {
    setLoading(true);
    setError('');
    setSearchKeyword(params.keyword);
    try {
      const response = await axios.get('/api/resources', { params });
      setResults(response.data);
    } catch (err) {
      setError('Failed to fetch results. Please try again.');
      console.error(err);
    }
    setLoading(false);
  };

  return (
    <div className="container">
      <h1>Odin (OKD Resource Inspector)</h1>
      <SearchForm onSearch={handleSearch} loading={loading} filters={filters} />
      {error && <p className="error-message">{error}</p>}
      <Results results={results} keyword={searchKeyword} />
    </div>
  );
}

export default App;
