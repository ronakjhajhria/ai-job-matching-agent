# Interview Notes

## Phase 1: Project foundation

**Why use an application factory?**
It makes app construction explicit, lets tests inject settings, and avoids
coupling endpoint tests to one global configuration instance.

**What does the health endpoint prove?**
It proves the API process can answer a request. It does not prove that external
dependencies are healthy; those checks should be added when the dependencies
exist, rather than returning a misleading all-services status now.

**Why validate environment settings?**
Configuration errors should fail early with a clear validation error. Typed
settings also give one place to document defaults and environment variable
names.