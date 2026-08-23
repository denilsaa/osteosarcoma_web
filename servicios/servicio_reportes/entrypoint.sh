#!/bin/sh
set -e

echo "Esperando PostgreSQL reportes..."

php -r '
$host = getenv("DB_HOST");
$port = getenv("DB_PORT") ?: "5432";
$db   = getenv("DB_DATABASE");
$user = getenv("DB_USERNAME");
$pass = getenv("DB_PASSWORD");

for ($i = 1; $i <= 30; $i++) {
    try {
        $pdo = new PDO(
            "pgsql:host=$host;port=$port;dbname=$db",
            $user,
            $pass,
            [PDO::ATTR_ERRMODE => PDO::ERRMODE_EXCEPTION]
        );

        echo "PostgreSQL reportes disponible.\n";
        exit(0);

    } catch (Throwable $e) {
        echo "Intento $i/30: {$e->getMessage()}\n";
        sleep(2);
    }
}

exit(1);
'

echo "Iniciando servicio_reportes..."

exec php artisan serve --host=0.0.0.0 --port=8000