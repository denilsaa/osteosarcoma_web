<?php

namespace App\Infrastructure\Persistence\Eloquent\Models;

use Illuminate\Database\Eloquent\Model;
use Illuminate\Database\Eloquent\Relations\HasMany;

class ValidationResult extends Model
{
    protected $table =
        'resultados_validacion';

    protected $primaryKey =
        'id_resultado_validacion';

    public $incrementing =
        true;

    protected $keyType =
        'int';

    public $timestamps =
        true;

    protected $guarded =
        [];


    public function validations(): HasMany
    {
        return $this->hasMany(
            RadiographicFileValidation::class,
            'id_resultado_validacion',
            'id_resultado_validacion'
        );
    }
}