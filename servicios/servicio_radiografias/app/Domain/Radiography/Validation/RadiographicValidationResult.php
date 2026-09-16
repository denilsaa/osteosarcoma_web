<?php

namespace App\Domain\Radiography\Validation;

final readonly class RadiographicValidationResult
{
    public function __construct(
        public string $typeCode,
        public bool $valid,
        public string $detail,
        public ?string $reason = null,
        public ?string $correction = null,
    ) {
    }


    public function resultCode(): string
    {
        return $this->valid
            ? 'VALIDO'
            : 'INVALIDO';
    }
}