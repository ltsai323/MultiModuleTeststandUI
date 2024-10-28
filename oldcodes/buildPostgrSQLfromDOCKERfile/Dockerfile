# Use offical PostgreSQL image as the base
FROM postgres:latest



# Copy the SQL script to crate the database and table
COPY init.sql /docker-entrypoint-initdb.d/

# Expose the default PostgreSQL port.
# 5432 is a reserved channel used in PostgreSQL.
# If you want to change it. One should use command
# > docker run -p 5423:5432
# Such that the host is able to listen 5423 channel.
# And computer builds 5423 -> 5432 channel and deliver to DB.
EXPOSE 5432

# Expose a port for pgweb
# EXPOSE 8018

# Define environmental variables used in PostgreSQL
ENV POSTGRES_USER=root
ENV POSTGRES_PASSWORD=myROOTpasswd_
ENV POSTGRES_DB=TESTDB

# Start pgweb on container startup
CMD ["postgres"]
