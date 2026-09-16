<?php

namespace App\Infrastructure\Persistence\Eloquent\Models;

use Illuminate\Database\Eloquent\Model;
use Illuminate\Database\Eloquent\Relations\BelongsTo;

class RadiographicFileValidation extends Model
{
    protected $table =
        'validaciones_archivo';

    protected $primaryKey =
        'id_validacion';

    public $incrementing =
        true;

    protected $keyType =
        'int';

    public $timestamps =
        false;

    protected $guarded =
        [];

    protected $casts = [
        'fecha_validacion' =>
            'datetime',
    ];


    public function file(): BelongsTo
    {
        return $this->belongsTo(
            RadiographicFileModel::class,
            'id_archivo',
            'id_archivo'
        );
    }


    public function validationType(): BelongsTo
    {
        return $this->belongsTo(
            ValidationType::class,
            'id_tipo_validacion',
            'id_tipo_validacion'
        );
    }


    public function validationResult(): BelongsTo
    {
        return $this->belongsTo(
            ValidationResult::class,
            'id_resultado_validacion',
            'id_resultado_validacion'
        );
    }
}