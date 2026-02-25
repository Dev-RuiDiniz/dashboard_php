#!/usr/bin/env bash
set -euo pipefail

php -l public/index.php
php -l src/Http/Kernel.php
php -l src/Http/RequestContext.php
php -l src/Observability/JsonLogger.php
php -l src/Auth/JwtService.php
php -l src/Auth/UserStore.php
php -l src/Audit/AuditLogger.php
php -l src/Domain/CpfValidator.php
php -l src/Domain/SocialStore.php
php -l src/Domain/StreetStore.php
php -l src/Domain/DeliveryStore.php
php -l src/Domain/EquipmentStore.php
php -l src/Reports/ExportService.php
php -l tests/Feature/HealthReadyTest.php
php -l tests/Feature/AuthRbacAuditTest.php
php -l tests/Feature/FamilyDomainCrudTest.php
php -l tests/Feature/StreetLgpdReferralTest.php
php -l tests/Feature/DeliveryEventsRulesTest.php
php -l tests/Feature/ReportsExportTest.php
php -l tests/Feature/EquipmentLoansTest.php
php tests/Feature/HealthReadyTest.php
php tests/Feature/AuthRbacAuditTest.php
php tests/Feature/FamilyDomainCrudTest.php
php tests/Feature/StreetLgpdReferralTest.php
php tests/Feature/DeliveryEventsRulesTest.php
php tests/Feature/ReportsExportTest.php
php tests/Feature/EquipmentLoansTest.php
