'use strict';

const express = require('express');
const { Client } = require('minio');

const app = express();
const PORT = process.env.PORT || 3000;

// Reads credentials from environment — canary: .env.production.bak leaks these
const minioClient = new Client({
  endPoint:  process.env.MINIO_ENDPOINT  || 'minio-open',
  port:      9000,
  useSSL:    false,
  accessKey: process.env.MINIO_ACCESS_KEY || '',
  secretKey: process.env.MINIO_SECRET_KEY || '',
});

app.get('/health', (_req, res) => {
  res.json({ status: 'ok', bucket: process.env.MINIO_BUCKET });
});

app.get('/files', async (_req, res) => {
  const bucket = process.env.MINIO_BUCKET || 'finance-private';
  const objects = [];
  const stream = minioClient.listObjects(bucket, '', true);
  stream.on('data', (obj) => objects.push(obj.name));
  stream.on('end', () => res.json({ bucket, objects }));
  stream.on('error', (err) => res.status(500).json({ error: err.message }));
});

if (require.main === module) {
  app.listen(PORT, () => {
    console.log(`dev-platform service listening on :${PORT}`);
  });
}

module.exports = app;
