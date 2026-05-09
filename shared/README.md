# Shared Module

Centralized utilities and configuration shared across all microservices.

## Structure

- **config/** - Centralized configuration (database, JWT, environment variables)
- **utils/** - Common utilities, helpers, decorators

## Purpose

Avoid code duplication across services. All services import from here.
