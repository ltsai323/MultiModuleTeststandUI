# Use offical PostgreSQL image as the base
FROM postgres:latest


# Install pgweb
RUN apt-get update && \
    apt-get install -y unzip && \
    apt-get install -y --no-install-recommends \
            ca-certificates \
            wget && \
    wget -O /tmp/pgweb.zip https://github.com/sosedoff/pgweb/releases/download/v0.14.2/pgweb_linux_amd64.zip && \
    unzip /tmp/pgweb.zip -d /tmp/ && \
    mv /tmp/pgweb_linux_amd64 /usr/local/bin/pgweb && \
    rm /tmp/pgweb.zip && \
    chmod +x /usr/local/bin/pgweb && \
    apt-get purge -y --auto-remove ca-certificates wget && \
    rm -rf /var/lib/apt/lists/*

# Copy the SQL script to crate the database and table
COPY init.sql /docker-entrypoint-initdb.d/

# Expose the default PostgreSQL port
EXPOSE 5432

# Expose a port for pgweb
EXPOSE 8081

# Define environmental variables used in PostgreSQL
ENV POSTGRES_USER=myuser
ENV POSTGRES_PASSWORD=mypassword
ENV POSTGRES_DB=TESTDB

# Start pgweb on container startup
CMD ["postgres"]
CMD ["service", "postgresql", "start"]
CMD ["pgweb", "--bind=0.0.0.0", "--listen=8081", "--url=postgresql://myuser:mypassword@localhost:5432/TESTDB"]
