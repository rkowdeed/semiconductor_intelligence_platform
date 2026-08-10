<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Semiconductor Intelligence Platform</title>
  <style>
    body {
      font-family: Arial, Helvetica, sans-serif;
      line-height: 1.6;
      margin: 0;
      padding: 2rem 1.25rem 3rem;
      color: #1f2937;
      background: #f8fafc;
    }
    main {
      max-width: 960px;
      margin: 0 auto;
      background: white;
      border: 1px solid #e5e7eb;
      border-radius: 12px;
      padding: 2rem;
      box-shadow: 0 8px 24px rgba(0,0,0,0.05);
    }
    h1, h2, h3 {
      color: #0f172a;
    }
    code, pre {
      background: #f1f5f9;
      border-radius: 6px;
    }
    pre {
      padding: 1rem;
      overflow-x: auto;
    }
    code {
      padding: 0.15rem 0.35rem;
    }
    ul, ol {
      padding-left: 1.25rem;
    }
    table {
      border-collapse: collapse;
      width: 100%;
      margin: 1rem 0;
    }
    th, td {
      border: 1px solid #e5e7eb;
      padding: 0.6rem 0.75rem;
      text-align: left;
    }
    th {
      background: #f8fafc;
    }
    .pill {
      display: inline-block;
      background: #e0f2fe;
      color: #075985;
      padding: 0.25rem 0.6rem;
      border-radius: 999px;
      font-size: 0.9rem;
      margin-right: 0.4rem;
      margin-bottom: 0.4rem;
    }
  </style>
</head>
<body>
  <main>
    <h1>Semiconductor Intelligence Platform (SIP)</h1>
    <p>A sovereign semiconductor intelligence platform for ingesting, governing, and analyzing manufacturing and engineering data. It combines metadata-driven ingestion, S3 lakehouse-style storage, PostgreSQL-backed intelligence, and AI-ready retrieval scaffolding.</p>

    <p>
      <span class="pill">Metadata-driven ingestion</span>
      <span class="pill">Governance</span>
      <span class="pill">Lakehouse catalog</span>
      <span class="pill">AI-ready search</span>
    </p>

    <h2>What this repository provides</h2>
    <ul>
      <li>Multi-format ingestion for MES, ERP, equipment, PLM, telemetry, and yield payloads</li>
      <li>Metadata-driven validation and routing for new data sources</li>
      <li>S3-based raw landing and lakehouse-style asset cataloging</li>
      <li>Governance controls for IP-sensitive and restricted data</li>
      <li>Traceability links across lots, wafers, tools, and design versions</li>
      <li>AI/RAG-ready document indexing and search scaffolding</li>
    </ul>

    <h2>Architecture at a glance</h2>
    <ol>
      <li>Source systems send events into the ingestion API.</li>
      <li>The parser and validator normalize each payload and check it against schema rules.</li>
      <li>Valid events are stored in S3 and published for downstream processing.</li>
      <li>Curated records are persisted in PostgreSQL and linked to governance, traceability, and AI services.</li>
    </ol>

    <h2>Quick start</h2>
    <pre><code>git clone &lt;this-repo&gt;
cd Semiconductor_Operations_Data_Platform
docker compose up --build</code></pre>

    <p>Once the services are up, use the Swagger UI at <code>http://localhost:8000/docs</code> or call the ingestion endpoints directly.</p>

    <h2>Key services</h2>
    <table>
      <tr><th>Service</th><th>Purpose</th></tr>
      <tr><td>FastAPI ingestion API</td><td>Accepts and routes new events</td></tr>
      <tr><td>S3 landing zone</td><td>Stores raw payloads for lakehouse workflows</td></tr>
      <tr><td>PostgreSQL</td><td>Stores curated records and audit information</td></tr>
      <tr><td>Governance and AI layers</td><td>Applies policy rules and supports retrieval-based intelligence</td></tr>
    </table>

    <h2>Test and validation</h2>
    <pre><code>pytest</code></pre>
    <p>The repository includes sample payloads and smoke-test flows for telemetry, yield, and core ingestion paths.</p>

    <h2>Project owner</h2>
    <p>ravikanth.kowdeed@gmail.com</p>
  </main>
</body>
</html>
