CREATE DATABASE auth_db;
CREATE USER auth_user WITH PASSWORD 'securepassword';
GRANT ALL PRIVILEGES ON DATABASE auth_db TO auth_user;
