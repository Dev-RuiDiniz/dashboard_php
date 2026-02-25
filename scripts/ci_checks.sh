#!/usr/bin/env bash
set -euo pipefail

php -l public/index.php
php -l src/Http/Kernel.php
php -l src/Http/RequestContext.php
php -l src/Observability/JsonLogger.php
php -l tests/Feature/HealthReadyTest.php
php tests/Feature/HealthReadyTest.php
