import React, { useState, useEffect } from 'react';
import axios from 'axios';
import './App.css';

// Note: In a real app, these would be separate component files.
// For simplicity in this context, they are included here.

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

const ResourceCard = ({ resource, keyword }) => {
  const [activeTab, setActiveTab] = useState('summary');

  const highlight = (text) => {
    if (!keyword || !text) return text;
    const regex = new RegExp(`(${keyword})`, 'gi');
    return text.split(regex).map((part, index) =>
      regex.test(part) ? <span key={index} className="highlight">{part}</span> : part
    );
  };

  // A simple summary view
  const summary = (
    <div className="key-value-table">
      {Object.entries(resource.data).slice(0, 5).map(([key, value]) => (
        <div className="kv-row" key={key}>
          <div className="kv-key">{highlight(key)}</div>
          <div className="kv-value">{highlight(String(value))}</div>
        </div>
      ))}
       {Object.keys(resource.data).length > 5 && <div className="kv-row"><div className="kv-key">...</div><div className="kv-value"></div></div>}
    </div>
  );

  const rawData = (
    <div className="code-block">
      <pre><code>{highlight(JSON.stringify(resource.data, null, 2))}</code></pre>
    </div>
  );

  return (
    <div className="resource-card">
      <h3>{highlight(resource.resource_name)} ({highlight(resource.resource_type)})</h3>
      <p>
        <strong>Cluster:</strong> {highlight(resource.cluster_name)} | <strong>Namespace:</strong> {highlight(resource.namespace)}
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