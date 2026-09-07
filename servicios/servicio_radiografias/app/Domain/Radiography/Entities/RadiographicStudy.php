<?php

namespace App\Domain\Radiography\Entities;

final readonly class RadiographicStudy
{
    /**
     * @param RadiographicFile[] $files
     */
    public function __construct(
        public string $id,
        public string $caseUuid,
        public string $registeredByUuid,
        public int $studyTypeId,
        public string $studyTypeCode,
        public string $studyTypeName,
        public int $anatomicalRegionId,
        public string $anatomicalRegionCode,
        public string $anatomicalRegionName,
        public ?string $studyDate,
        public ?string $observation,
        public string $registeredAt,
        public array $files,
    ) {
    }
}