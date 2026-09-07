<?php

namespace App\Infrastructure\Persistence\Eloquent\Models;

use Illuminate\Database\Eloquent\Model;
use Illuminate\Database\Eloquent\Relations\BelongsTo;

class RadiographicFileModel extends Model
{
    protected $table = 'archivos_radiograficos';

    protected $primaryKey = 'id_archivo';

    public $incrementing = false;

    protected $keyType = 'string';

    public $timestamps = false;

    protected $guarded = [];

    protected $casts = [
        'activo' => 'boolean',
        'version' => 'integer',
        'tamano_bytes' => 'integer',
        'ancho_px' => 'integer',
        'alto_px' => 'integer',
        'fecha_carga' => 'datetime',
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
}