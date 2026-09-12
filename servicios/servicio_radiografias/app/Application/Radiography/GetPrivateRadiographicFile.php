<?php

namespace App\Application\Radiography;

use App\Domain\Radiography\Entities\RadiographicFile;
use App\Domain\Radiography\Repositories\RadiographicFileRepository;
use InvalidArgumentException;
use RuntimeException;

final readonly class GetPrivateRadiographicFile
{
    public function __construct(
        private RadiographicFileRepository $repository,
    ) {
    }


    public function execute(
        string $fileUuid
    ): RadiographicFile {
        if (! $this->isUuid($fileUuid)) {
            throw new InvalidArgumentException(
                'El identificador del archivo radiográfico no es válido.'
            );
        }


        $file = $this
            ->repository
            ->findActiveByUuid(
                $fileUuid
            );


        if ($file === null) {
            throw new RuntimeException(
                'El archivo radiográfico no existe o se encuentra inactivo.'
            );
        }


        return $file;
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