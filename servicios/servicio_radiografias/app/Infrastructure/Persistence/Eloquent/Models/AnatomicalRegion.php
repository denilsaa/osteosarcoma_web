<?php

namespace App\Infrastructure\Persistence\Eloquent\Models;

use Illuminate\Database\Eloquent\Model;
use Illuminate\Database\Eloquent\Relations\HasMany;

class AnatomicalRegion extends Model
{
    protected $table =
        'regiones_anatomicas';

    protected $primaryKey =
        'id_region_anatomica';

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
            'id_region_anatomica',
            'id_region_anatomica'
        );
    }
}