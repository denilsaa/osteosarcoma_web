#!/bin/sh

set -e


echo "=============================================="
echo " WORKER DE AUDITORIA - RABBITMQ"
echo "=============================================="


# ==========================================================
# POSTGRESQL
# ==========================================================

echo "Esperando PostgreSQL Auditoria..."


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

            [
                PDO::ATTR_ERRMODE =>
                    PDO::ERRMODE_EXCEPTION
            ]

        );

        echo "PostgreSQL Auditoria disponible.\n";

        exit(0);

    }

    catch (Throwable $e) {

        echo "Intento PostgreSQL $i/30\n";

        sleep(2);

    }
}

exit(1);
'


# ==========================================================
# RABBITMQ
# ==========================================================

echo "Esperando RabbitMQ..."


php -r '
$host = getenv("RABBITMQ_HOST") ?: "rabbitmq";
$port = (int) (getenv("RABBITMQ_PORT") ?: 5672);

for ($i = 1; $i <= 30; $i++) {

    $socket = @fsockopen(

        $host,

        $port,

        $errno,

        $errstr,

        2

    );


    if ($socket) {

        fclose(
            $socket
        );

        echo "RabbitMQ disponible.\n";

        exit(0);

    }


    echo "Intento RabbitMQ $i/30\n";

    sleep(2);
}

exit(1);
'


# ==========================================================
# WORKER
# ==========================================================

echo "Iniciando consumidor de Auditoria..."


exec php artisan audit:consume