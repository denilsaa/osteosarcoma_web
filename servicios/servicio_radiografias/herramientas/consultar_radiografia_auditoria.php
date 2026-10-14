<?php
/**
 * CONSULTA LOCAL DE DESARROLLO, NO ES API WEB.
 * Únicamente ejecutable por quien tenga acceso a consola del contenedor.
 * Devuelve ruta privada y hash; no imprime datos personales ni bytes de la imagen.
 */
require __DIR__.'/../vendor/autoload.php';
$app = require __DIR__.'/../bootstrap/app.php';
$app->make(\Illuminate\Contracts\Console\Kernel::class)->bootstrap();

$id = (string) ($argv[1] ?? '');
if (!preg_match('/^[a-f0-9]{8}-[a-f0-9]{4}-[1-5][a-f0-9]{3}-[89ab][a-f0-9]{3}-[a-f0-9]{12}$/i', $id)) {
    fwrite(STDERR, "UUID_INVALIDO\n");
    exit(2);
}
$model = \App\Infrastructure\Persistence\Eloquent\Models\RadiographicFileModel::query()
    ->where('id_archivo', $id)
    ->where('activo', true)
    ->first();
if ($model === null) {
    fwrite(STDERR, "RADIOGRAFIA_NO_ENCONTRADA_O_INACTIVA\n");
    exit(3);
}
$disk = \Illuminate\Support\Facades\Storage::disk('local');
$relative = (string) $model->ruta_almacenamiento;
$root = realpath($disk->path(''));
$realPath = realpath($disk->path($relative));
// La imagen nunca puede salir de la carpeta privada de radiografías por rutas relativas.
if ($root === false || $realPath === false || !str_starts_with($realPath, $root.'/radiografias/')) {
    fwrite(STDERR, "RUTA_PRIVADA_INVALIDA\n");
    exit(4);
}
if (!is_file($realPath) || filesize($realPath) > 20 * 1024 * 1024) {
    fwrite(STDERR, "ORIGINAL_NO_DISPONIBLE_O_GRANDE\n");
    exit(5);
}
$actual = hash_file('sha256', $realPath);
$expected = strtolower((string) $model->hash_sha256);
if (!hash_equals($expected, strtolower((string) $actual))) {
    fwrite(STDERR, "HASH_REGISTRADO_NO_COINCIDE\n");
    exit(6);
}
$extension = strtolower((string) pathinfo($realPath, PATHINFO_EXTENSION));
if (!in_array($extension, ['png', 'jpg', 'jpeg', 'bmp', 'tif', 'tiff', 'dcm'], true)) {
    fwrite(STDERR, "EXTENSION_NO_ADMITIDA\n");
    exit(7);
}
echo 'AUDIT_PATH='.$realPath.PHP_EOL;
echo 'AUDIT_SHA256='.$actual.PHP_EOL;
echo 'AUDIT_EXTENSION='.$extension.PHP_EOL;
echo "AUDIT_OK=1\n";
