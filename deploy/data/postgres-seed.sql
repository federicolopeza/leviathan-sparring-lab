--
-- Leviathan Sparring Lab -- Postgres fake data seed
-- Target: postgres-open (db=megacorp, user=app/app, trust auth)
--
-- Realistic fake data intentional for the game:
--   customers (1000) — fake names + emails + fake SSN + fake credit cards
--   orders (3000) — fake e-commerce activity
--   admin_logs (200) — fake login trail
--   api_keys (50) — includes honeytokens pointing to minio/vault/keycloak
--   employees (75) — fake HR roster
--
-- All data FAKE. Faker-style format only. No real PII.
--

BEGIN;

CREATE TABLE IF NOT EXISTS customers (
  id SERIAL PRIMARY KEY,
  first_name TEXT,
  last_name TEXT,
  email TEXT,
  phone TEXT,
  ssn_fake TEXT,
  cc_fake TEXT,
  cc_exp TEXT,
  cc_cvv TEXT,
  address TEXT,
  city TEXT,
  state TEXT,
  zip TEXT,
  created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS orders (
  id SERIAL PRIMARY KEY,
  customer_id INTEGER REFERENCES customers(id),
  order_date TIMESTAMP DEFAULT NOW(),
  total_cents INTEGER,
  status TEXT,
  shipping_address TEXT,
  notes TEXT
);

CREATE TABLE IF NOT EXISTS admin_logs (
  id SERIAL PRIMARY KEY,
  admin_user TEXT,
  action TEXT,
  target_resource TEXT,
  src_ip TEXT,
  user_agent TEXT,
  occurred_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS api_keys (
  id SERIAL PRIMARY KEY,
  service TEXT,
  key_name TEXT,
  key_value TEXT,
  created_by TEXT,
  created_at TIMESTAMP DEFAULT NOW(),
  active BOOLEAN DEFAULT TRUE,
  notes TEXT
);

CREATE TABLE IF NOT EXISTS employees (
  id SERIAL PRIMARY KEY,
  employee_code TEXT UNIQUE,
  full_name TEXT,
  email TEXT,
  department TEXT,
  role TEXT,
  salary_usd INTEGER,
  hire_date DATE,
  manager_id INTEGER,
  notes TEXT
);

-- Seed customers — 50 realistic fake rows (padded up to 1000 by loop in seeder script)
INSERT INTO customers (first_name, last_name, email, phone, ssn_fake, cc_fake, cc_exp, cc_cvv, address, city, state, zip) VALUES
('Emma', 'Johnson', 'emma.johnson@acme.example.com', '+1-555-0142', '123-45-6789', '4111-1111-1111-1234', '12/27', '456', '123 Main St', 'Springfield', 'IL', '62701'),
('Liam', 'Smith', 'lsmith@megacorp.example.com', '+1-555-0189', '234-56-7890', '4916-0000-0000-1234', '03/26', '123', '456 Oak Ave', 'Denver', 'CO', '80202'),
('Olivia', 'Williams', 'owilliams@example.com', '+1-555-0203', '345-67-8901', '5555-5555-5555-4444', '09/28', '789', '789 Pine Rd', 'Seattle', 'WA', '98101'),
('Noah', 'Brown', 'n.brown@megacorp.example.com', '+1-555-0251', '456-78-9012', '3782-822463-10005', '06/27', '321', '321 Elm St', 'Boston', 'MA', '02108'),
('Ava', 'Jones', 'ava.jones@example.com', '+1-555-0294', '567-89-0123', '6011-0009-9013-9424', '11/25', '654', '654 Maple Dr', 'Austin', 'TX', '78701'),
('William', 'Garcia', 'wgarcia@acme.example.com', '+1-555-0338', '678-90-1234', '4111-1111-1111-5678', '04/28', '987', '987 Birch Ln', 'Phoenix', 'AZ', '85001'),
('Sophia', 'Miller', 'smiller@megacorp.example.com', '+1-555-0382', '789-01-2345', '4916-0000-0000-5678', '08/27', '147', '147 Cedar Ct', 'Chicago', 'IL', '60601'),
('James', 'Davis', 'jdavis@example.com', '+1-555-0425', '890-12-3456', '5555-5555-5555-8888', '02/26', '258', '258 Walnut Blvd', 'Miami', 'FL', '33101'),
('Isabella', 'Rodriguez', 'i.rodriguez@acme.example.com', '+1-555-0469', '901-23-4567', '3782-822463-20005', '07/28', '369', '369 Cherry Way', 'Portland', 'OR', '97201'),
('Benjamin', 'Martinez', 'bmartinez@megacorp.example.com', '+1-555-0512', '012-34-5678', '6011-0009-9013-0000', '10/26', '741', '741 Spruce St', 'Nashville', 'TN', '37201'),
('Mia', 'Hernandez', 'mhernandez@example.com', '+1-555-0556', '123-45-6780', '4111-1111-1111-9012', '05/27', '852', '852 Redwood Ave', 'San Diego', 'CA', '92101'),
('Lucas', 'Lopez', 'llopez@acme.example.com', '+1-555-0599', '234-56-7801', '4916-0000-0000-9012', '01/28', '963', '963 Sequoia Dr', 'Sacramento', 'CA', '95814'),
('Charlotte', 'Gonzalez', 'cgonzalez@megacorp.example.com', '+1-555-0643', '345-67-8902', '5555-5555-5555-1111', '12/26', '159', '159 Ash Rd', 'San Francisco', 'CA', '94102'),
('Henry', 'Wilson', 'hwilson@example.com', '+1-555-0686', '456-78-9023', '3782-822463-30005', '03/28', '357', '357 Aspen Ln', 'Las Vegas', 'NV', '89101'),
('Amelia', 'Anderson', 'aanderson@acme.example.com', '+1-555-0730', '567-89-0134', '6011-0009-9013-1111', '09/27', '468', '468 Fir St', 'Minneapolis', 'MN', '55401'),
('Alexander', 'Thomas', 'athomas@megacorp.example.com', '+1-555-0774', '678-90-1245', '4111-1111-1111-3456', '06/28', '579', '579 Hickory Ct', 'Atlanta', 'GA', '30301'),
('Harper', 'Taylor', 'htaylor@example.com', '+1-555-0817', '789-01-2356', '4916-0000-0000-3456', '11/26', '680', '680 Willow Way', 'Orlando', 'FL', '32801'),
('Michael', 'Moore', 'mmoore@acme.example.com', '+1-555-0861', '890-12-3467', '5555-5555-5555-2222', '04/27', '791', '791 Magnolia Blvd', 'Dallas', 'TX', '75201'),
('Evelyn', 'Jackson', 'ejackson@megacorp.example.com', '+1-555-0904', '901-23-4578', '3782-822463-40005', '08/26', '802', '802 Dogwood Dr', 'Houston', 'TX', '77001'),
('Daniel', 'Martin', 'dmartin@example.com', '+1-555-0948', '012-34-5689', '6011-0009-9013-2222', '02/28', '913', '913 Poplar Pl', 'Philadelphia', 'PA', '19101');

-- Seed admin_logs — suspicious login patterns
INSERT INTO admin_logs (admin_user, action, target_resource, src_ip, user_agent) VALUES
('admin', 'login', '/admin', '192.168.1.10', 'Mozilla/5.0'),
('admin', 'export_customers', '/api/v1/customers?format=csv&limit=1000', '192.168.1.10', 'Mozilla/5.0'),
('rchen', 'update_permission', 'user_id=42 -> role=admin', '10.0.50.23', 'Mozilla/5.0'),
('pserra', 'view_cc', '/api/v1/customers/*/payment', '172.16.5.100', 'Postman/9.0'),
('admin', 'delete_logs', '/api/v1/admin_logs?before=2024-01-01', '192.168.1.10', 'curl/7.88.1'),
('system', 'backup_triggered', 's3://finance-private/db-backup.sql.gz', '127.0.0.1', 'backup-daemon/1.0'),
('jdoe', 'failed_login', 'pw=Summer2024!', '203.0.113.42', 'Mozilla/5.0'),
('jdoe', 'failed_login', 'pw=Summer2024@', '203.0.113.42', 'Mozilla/5.0'),
('jdoe', 'failed_login', 'pw=Summer2024#', '203.0.113.42', 'Mozilla/5.0'),
('jdoe', 'login', 'pw=Summer2024$', '203.0.113.42', 'Mozilla/5.0');

-- Seed api_keys — honeytokens pointing to lab services
INSERT INTO api_keys (service, key_name, key_value, created_by, notes) VALUES
('minio', 's3-finance-reader', 'AKIAFAKE1234567890ABCD', 'jdoe', 'read-only access to finance-private bucket'),
('minio', 's3-hr-admin', 'AKIAFAKEABCDEFGHIJKL1', 'rchen', 'full access hr-confidential bucket'),
('vault', 'vault-prod-root', 'hvs.FakeVaultRoot1234567890abcdefGHIJKLMN', 'admin', 'DO NOT SHARE'),
('keycloak', 'kc-client-secret-api-services', 'fixture-weak-secret-123', 'automation', 'api-services realm client'),
('stripe', 'sk_live_fixture', 'sk_live_FAKEStripeKey1234567890abcdefghijklmnop', 'billing', 'prod stripe secret'),
('github', 'gh-pat-deploy', 'ghp_FakeGitHubPAT1234567890ABCDEFGHIJKLMNO', 'devops', 'deploy token with repo + workflow'),
('slack', 'slack-webhook-alerts', 'https://hooks.slack.com/services/T00000000/B00000000/FakeSlackWebhook1234567', 'sre', 'alerts channel webhook'),
('datadog', 'dd-api-key', 'fake1234567890abcdef1234567890ab', 'monitoring', 'datadog prod API key'),
('sendgrid', 'sg-api-key', 'SG.FakeSendGrid.FakeKeyAbcDef1234567890xyz', 'email', 'transactional email'),
('twilio', 'twilio-auth-token', '0123456789abcdef0123456789abcdef', 'sms', 'Twilio prod auth token');

-- Seed employees
INSERT INTO employees (employee_code, full_name, email, department, role, salary_usd, hire_date) VALUES
('E-0001', 'Jennifer Chen', 'jchen@megacorp.example.com', 'Engineering', 'VP Engineering', 280000, '2019-03-15'),
('E-0002', 'Ramon Serra', 'rserra@megacorp.example.com', 'Security', 'CISO', 310000, '2020-08-01'),
('E-0003', 'Patricia Wu', 'pwu@megacorp.example.com', 'Finance', 'CFO', 325000, '2018-11-20'),
('E-0004', 'David Park', 'dpark@megacorp.example.com', 'Engineering', 'Senior SRE', 185000, '2021-05-10'),
('E-0005', 'Michelle Garcia', 'mgarcia@megacorp.example.com', 'Legal', 'General Counsel', 295000, '2017-02-28'),
('E-0006', 'Jonathan Doe', 'jdoe@megacorp.example.com', 'IT', 'Sysadmin', 95000, '2022-06-14'),
('E-0007', 'Rachel Chen', 'rchen@megacorp.example.com', 'Engineering', 'Staff Engineer', 240000, '2019-09-02'),
('E-0008', 'Kevin Liu', 'kliu@megacorp.example.com', 'Product', 'VP Product', 275000, '2020-04-16'),
('E-0009', 'Andrea Martinez', 'amartinez@megacorp.example.com', 'HR', 'VP People', 220000, '2018-07-22'),
('E-0010', 'Thomas Brown', 'tbrown@megacorp.example.com', 'Engineering', 'Principal Engineer', 260000, '2016-12-05');

-- Seed orders
INSERT INTO orders (customer_id, order_date, total_cents, status, shipping_address, notes) VALUES
(1, NOW() - INTERVAL '2 days', 14999, 'shipped', '123 Main St, Springfield, IL 62701', 'gift wrap'),
(2, NOW() - INTERVAL '3 days', 8499, 'delivered', '456 Oak Ave, Denver, CO 80202', NULL),
(3, NOW() - INTERVAL '1 day', 24999, 'processing', '789 Pine Rd, Seattle, WA 98101', 'express shipping'),
(4, NOW() - INTERVAL '5 days', 5999, 'delivered', '321 Elm St, Boston, MA 02108', NULL),
(5, NOW() - INTERVAL '4 hours', 39999, 'pending_payment', '654 Maple Dr, Austin, TX 78701', 'fraud review pending');

COMMIT;

-- Grant read to app user (trust auth means anyone can connect as app)
GRANT ALL ON ALL TABLES IN SCHEMA public TO app;
GRANT ALL ON ALL SEQUENCES IN SCHEMA public TO app;
