<?php

namespace App\Infrastructure\Persistence\Eloquent\Models;

use Illuminate\Database\Eloquent\Model;
use Illuminate\Database\Eloquent\Relations\HasMany;

class Laterality extends Model
{
    protected $table =
        'lateralidades';

    protected $primaryKey =
        'id_lateralidad';

    public $incrementing =
        true;

    protected $keyType =
        'int';

    protected $guarded = [];


    public function studies(): HasMany
    {
        return $this->hasMany(
            RadiographicStudyModel::class,
            'id_lateralidad',
            'id_lateralidad'
        );
    }
}