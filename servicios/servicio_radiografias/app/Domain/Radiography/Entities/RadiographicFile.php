<?php

namespace App\Domain\Radiography\Entities;

final readonly class RadiographicFile
{
    public function __construct(
        public string $id,
        public string $caseUuid,
        public int $version,
        public string $originalName,
        public string $storedName,
        public string $storagePath,
        public int $sizeBytes,
        public ?int $widthPx,
        public ?int $heightPx,
        public string $sha256,
        public bool $active,
        public string $validationStatus,
        public string $mimeCode,
        public string $mimeType,
        public string $extension,
        public string $uploadedAt,
    ) {
    }


    public function isValid(): bool
    {
        return $this->validationStatus === 'VALIDA';
    }


    public function isRejected(): bool
    {
        return $this->validationStatus === 'RECHAZADA';
    }
}