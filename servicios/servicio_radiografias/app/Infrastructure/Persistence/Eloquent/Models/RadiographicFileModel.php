<?php

namespace App\Infrastructure\Persistence\Eloquent\Models;

use Illuminate\Database\Eloquent\Model;
use Illuminate\Database\Eloquent\Relations\BelongsTo;
use Illuminate\Database\Eloquent\Relations\HasMany;
use Illuminate\Database\Eloquent\Relations\HasOne;

class RadiographicFileModel extends Model
{
    protected $table =
        'archivos_radiograficos';

    protected $primaryKey =
        'id_archivo';

    public $incrementing =
        false;

    protected $keyType =
        'string';

    public $timestamps =
        false;

    protected $guarded =
        [];

    protected $casts = [
        'activo' =>
            'boolean',

        'version' =>
            'integer',

        'tamano_bytes' =>
            'integer',

        'ancho_px' =>
            'integer',

        'alto_px' =>
            'integer',

        'fecha_carga' =>
            'datetime',

        'fecha_reemplazo' =>
            'datetime',
    ];


    public function study(): BelongsTo
    {
        return $this->belongsTo(
            RadiographicStudyModel::class,
            'id_estudio',
            'id_estudio'
        );
    }


    public function mimeType(): BelongsTo
    {
        return $this->belongsTo(
            MimeType::class,
            'id_tipo_mime',
            'id_tipo_mime'
        );
    }


    public function validations(): HasMany
    {
        return $this->hasMany(
            RadiographicFileValidation::class,
            'id_archivo',
            'id_archivo'
        )
            ->orderBy(
                'id_validacion'
            );
    }


    /*
     * Versión anterior reemplazada por este archivo.
     *
     * Ejemplo:
     *
     * V2.reemplaza_archivo_uuid -> V1.id_archivo
     */
    public function replacedFile(): BelongsTo
    {
        return $this->belongsTo(
            self::class,
            'reemplaza_archivo_uuid',
            'id_archivo'
        );
    }


    /*
     * Versión que reemplazó a este archivo.
     *
     * Ejemplo:
     *
     * V1 <- V2.reemplaza_archivo_uuid
     */
    public function replacementFile(): HasOne
    {
        return $this->hasOne(
            self::class,
            'reemplaza_archivo_uuid',
            'id_archivo'
        );
    }
}