# Stage 1: Build wheels
FROM python:3.12.2 AS builder

WORKDIR /build

COPY requirements.txt .
RUN pip wheel --no-cache-dir --no-deps --wheel-dir /wheels -r requirements.txt

# Copy the entire 'app' directory into the build context
COPY app /build/app


# Stage 2: Final image
FROM python:3.12.2-slim

# Set the working directory to the directory that will contain our package
WORKDIR /app

COPY --from=builder /wheels /wheels
COPY --from=builder /build/requirements.txt .
RUN pip install --no-cache /wheels/*

# Copy the 'app' package into the workdir, creating the /app/app structure
COPY --from=builder /build/app /app/app

# Ensure it's treated as a package (important)
RUN touch /app/app/__init__.py

EXPOSE 8080

# Run gunicorn from /app. It will find the 'app' package in the current directory.
# The target 'app.api:app' tells it to look for the 'api' module inside the 'app' package.
ENTRYPOINT ["gunicorn", "--bind", "0.0.0.0:8080", "app.api:app"]

