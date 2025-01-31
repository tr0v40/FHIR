# Usar a imagem oficial do PostgreSQL
FROM postgres:latest

# Definir variáveis de ambiente para criar o banco automaticamente
ENV POSTGRES_DB=fhir_db
ENV POSTGRES_USER=fhir_user
ENV POSTGRES_PASSWORD=fhir_password

# Expor a porta padrão do PostgreSQL
EXPOSE 5432

# Comando padrão para iniciar o PostgreSQL
CMD ["postgres"]
