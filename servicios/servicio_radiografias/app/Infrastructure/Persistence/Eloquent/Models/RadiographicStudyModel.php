<?php

namespace App\Infrastructure\Persistence\Eloquent\Models;

use Illuminate\Database\Eloquent\Model;
use Illuminate\Database\Eloquent\Relations\BelongsTo;
use Illuminate\Database\Eloquent\Relations\HasMany;

class RadiographicStudyModel extends Model
{
    protected $table =
        'estudios_radiograficos';

    protected $primaryKey =
        'id_estudio';

    public $incrementing =
        false;

    protected $keyType =
        'string';

    public $timestamps =
        false;

    protected $guarded = [];

    protected $casts = [
        'fecha_estudio' =>
            'date',

        'fecha_registro' =>
            'datetime',
    ];


    public function studyType(): BelongsTo
    {
        return $this->belongsTo(
            StudyType::class,
            'id_tipo_estudio',
            'id_tipo_estudio'
        );
    }


    public function anatomicalRegion(): BelongsTo
    {
        return $this->belongsTo(
            AnatomicalRegion::class,
            'id_region_anatomica',
            'id_region_anatomica'
        );
    }


    public function laterality(): BelongsTo
    {
        return $this->belongsTo(
            Laterality::class,
            'id_lateralidad',
            'id_lateralidad'
        );
    }


    public function files(): HasMany
    {
        return $this->hasMany(
            RadiographicFileModel::class,
            'id_estudio',
            'id_estudio'
        );
    }
}