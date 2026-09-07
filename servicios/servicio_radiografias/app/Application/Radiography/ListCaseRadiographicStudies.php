<?php

namespace App\Application\Radiography;

use App\Domain\Radiography\Repositories\RadiographicStudyRepository;
use InvalidArgumentException;

final readonly class ListCaseRadiographicStudies
{
    public function __construct(
        private RadiographicStudyRepository $repository,
    ) {
    }

    public function execute(
        string $caseUuid
    ): array {
        if (! $this->isUuid($caseUuid)) {
            throw new InvalidArgumentException(
                'El identificador del caso clínico no es un UUID válido.'
            );
        }

        return $this->repository->findByCaseUuid(
            $caseUuid
        );
    }

    private function isUuid(
        string $value
    ): bool {
        return preg_match(
            '/^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i',
            $value
        ) === 1;
    }
}