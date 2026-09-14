<?php

namespace App\Infrastructure\Persistence\Eloquent\Models;

use Illuminate\Database\Eloquent\Model;
use Illuminate\Database\Eloquent\Relations\HasMany;

class StudyType extends Model
{
    protected $table =
        'tipos_estudio';

    protected $primaryKey =
        'id_tipo_estudio';

    public $incrementing =
        true;

    protected $keyType =
        'int';

    protected $guarded =
        [];

    protected $casts = [
        'activo' =>
            'boolean',
    ];


    public function studies(): HasMany
    {
        return $this->hasMany(
            RadiographicStudyModel::class,
            'id_tipo_estudio',
            'id_tipo_estudio'
        );
    }
}