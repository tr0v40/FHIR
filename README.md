

# FHIR


## Database
Config do postgres
psql postgres

CREATE DATABASE fhir_db;

CREATE USER fhir_user_ WITH PASSWORD 'fhir_password';

GRANT ALL PRIVILEGES ON DATABASE fhir_db TO fhir_user;
ALTER DATABASE fhir_db OWNER TO fhir_user;


## Django
## Preparacao
criar virtualenv

python -m venv venv

windows
./venv/scripts/activate

linux/mac
source /venv/bin/Activate


instalar requirements

pip install -r requirements.txt


## Iniciar django

migrar banco (primeiro uso)

python manage.py migrate

Executar server

python manage.py runserver

\q