<?php

namespace App\Infrastructure\Persistence\Eloquent\Models;

use Illuminate\Database\Eloquent\Model;
use Illuminate\Database\Eloquent\Relations\HasMany;

class MimeType extends Model
{
    protected $table = 'tipos_mime';

    protected $primaryKey = 'id_tipo_mime';

    public $incrementing = true;

    protected $keyType = 'int';

    protected $guarded = [];

    protected $casts = [
        'activo' => 'boolean',
    ];

    public function files(): HasMany
    {
        return $this->hasMany(
            RadiographicFileModel::class,
            'id_tipo_mime',
            'id_tipo_mime'
        );
    }
}