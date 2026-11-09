# FROM maven:3.9-eclipse-temurin-21 AS build
# WORKDIR /work
# COPY pom.xml .
# RUN mvn -q -DskipTests dependency:copy-dependencies -DoutputDirectory=/work/lib
# FROM eclipse-temurin:21-jre
# WORKDIR /fuseki
# COPY --from=build /work/lib /fuseki/lib
# EXPOSE 3030
# CMD ["java","-cp","/fuseki/lib/*","org.apache.jena.fuseki.main.cmds.FusekiMainCmd","--mem","--update","/shop"]



FROM eclipse-temurin:21-jre-jammy

ARG FUSEKI_VERSION=5.4.0

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
       curl ca-certificates tar \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /opt

# Download the complete Apache Fuseki distribution.
RUN curl -fL --retry 3 \
      "https://archive.apache.org/dist/jena/binaries/apache-jena-fuseki-${FUSEKI_VERSION}.tar.gz" \
      -o /tmp/fuseki.tar.gz \
    && tar -xzf /tmp/fuseki.tar.gz -C /opt \
    && mv "/opt/apache-jena-fuseki-${FUSEKI_VERSION}" /opt/fuseki \
    && test -f /opt/fuseki/fuseki-server.jar \
    && rm /tmp/fuseki.tar.gz

# Persistent database directory.
RUN mkdir -p /fuseki-data

EXPOSE 3030

# Run the packaged server, including its runtime dependencies.
ENTRYPOINT ["java", "-jar", "/opt/fuseki/fuseki-server.jar"]

CMD ["--loc=/fuseki-data", "--update", "/ecommerce"]

