<?php

namespace App\Infrastructure\Persistence\Eloquent\Models;

use Illuminate\Database\Eloquent\Model;
use Illuminate\Database\Eloquent\Relations\HasMany;

class ValidationType extends Model
{
    protected $table =
        'tipos_validacion';

    protected $primaryKey =
        'id_tipo_validacion';

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
            'id_tipo_validacion',
            'id_tipo_validacion'
        );
    }
}